"""AI Receptionist automation backend - QuensultingAI Dental Clinic.

Exposes:
  * RetellAI custom-function webhooks (check availability, book appointment, answer FAQ)
  * RetellAI call-lifecycle webhook (call_started / call_ended / call_analyzed)
  * Dashboard read APIs (appointments, call logs, integration status)

Deployed behind the /api route prefix (Vercel strips the prefix before
forwarding, so routes here are defined without it).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import fastapi
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

import clinic
import notifications
import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = fastapi.FastAPI(title="QuensultingAI Dental Clinic - AI Receptionist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage.init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _retell_args(request: Request) -> tuple[dict, dict]:
    """Extract (args, call) from a Retell custom-function POST.

    Retell sends {"call": {...}, "name": "...", "args": {...}}.
    We also accept a flat JSON body so the endpoints are easy to test
    with curl or the dashboard.
    """
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    if isinstance(body, dict) and isinstance(body.get("args"), dict):
        return body["args"], body.get("call") or {}
    return body if isinstance(body, dict) else {}, {}


def _parse_datetime(value: str) -> datetime | None:
    """Parse ISO-ish datetimes the LLM produces, e.g. '2026-07-08 15:00'."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Health / clinic info
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "ai-receptionist-backend"}


@app.get("/clinic")
async def clinic_info() -> dict:
    return {
        "name": clinic.CLINIC_NAME,
        "address": clinic.CLINIC_ADDRESS,
        "phone": clinic.CLINIC_PHONE,
        "working_hours": "Mon-Sat, 9:00 AM - 6:00 PM",
        "services": clinic.SERVICES,
        "faqs": [{"question": f["question"], "answer": f["answer"]} for f in clinic.FAQS],
    }


@app.get("/integrations")
async def integrations() -> dict:
    return {
        "google_sheets": storage.sheets_status(),
        "notifications": notifications.notification_status(),
    }


# ---------------------------------------------------------------------------
# RetellAI custom functions
# ---------------------------------------------------------------------------

@app.post("/retell/check-availability")
async def check_availability(request: Request) -> dict:
    """Custom function: check_availability(date, time?, service?).

    Returns whether the requested slot is free, or suggests the next
    few open slots for that day.
    """
    args, _call = await _retell_args(request)
    date_str = str(args.get("date", "")).strip()
    time_str = str(args.get("time", "")).strip()

    if not date_str:
        return {"available": False, "message": "Please provide the date the caller wants."}

    # Specific slot requested
    if time_str:
        dt = _parse_datetime(f"{date_str} {time_str}") or _parse_datetime(f"{date_str}T{time_str}")
        if dt is None:
            return {"available": False, "message": "I could not understand that date and time. Please confirm it with the caller."}
        ok, reason = clinic.is_within_working_hours(dt)
        if not ok:
            return {"available": False, "message": reason}
        iso = dt.strftime("%Y-%m-%dT%H:%M")
        if storage.slot_taken(iso):
            return {"available": False, "message": "That slot is already booked. Ask the caller for another time.", "requested_slot": iso}
        return {"available": True, "message": "The slot is available.", "requested_slot": iso}

    # No time given: suggest open slots for that date
    day = _parse_datetime(f"{date_str} 09:00")
    if day is None:
        return {"available": False, "message": "I could not understand that date. Please confirm it with the caller."}
    ok, reason = clinic.is_within_working_hours(day)
    if not ok:
        return {"available": False, "message": reason}

    booked = storage.booked_times_for_date(day.strftime("%Y-%m-%d"))
    suggestions: list[str] = []
    cursor = day
    while cursor.time() < clinic.CLOSE_TIME and len(suggestions) < 4:
        iso = cursor.strftime("%Y-%m-%dT%H:%M")
        if iso not in booked:
            suggestions.append(cursor.strftime("%I:%M %p").lstrip("0"))
        cursor += timedelta(minutes=clinic.SLOT_MINUTES)
    if not suggestions:
        return {"available": False, "message": "That day is fully booked. Ask the caller for a different day."}
    return {"available": True, "message": f"Open slots on {day.strftime('%A, %d %B')}: {', '.join(suggestions)}.", "open_slots": suggestions}


class BookingArgs(BaseModel):
    patient_name: str = Field(min_length=1)
    phone: str = Field(min_length=6)
    email: str | None = None
    service: str = Field(min_length=1)
    date: str
    time: str
    notes: str | None = None

    @field_validator("patient_name", "phone", "service", "date", "time", mode="before")
    @classmethod
    def _strip(cls, v):
        return str(v).strip() if v is not None else v


@app.post("/retell/book-appointment")
async def book_appointment(request: Request) -> dict:
    """Custom function: book_appointment(patient_name, phone, email?, service, date, time, notes?).

    Validates the request, persists it (SQLite + Google Sheets), and
    triggers the confirmation email / webhook.
    """
    args, call = await _retell_args(request)
    try:
        booking = BookingArgs(**args)
    except Exception as exc:  # noqa: BLE001 - report missing fields back to the agent
        missing = ", ".join(sorted({str(e.get("loc", ["field"])[0]) for e in getattr(exc, "errors", lambda: [])()})) or "required details"
        return {"success": False, "message": f"Missing or invalid details: {missing}. Please collect them from the caller."}

    svc = clinic.get_service(booking.service)
    if svc is None:
        names = ", ".join(s["name"] for s in clinic.SERVICES)
        return {"success": False, "message": f"We do not offer that service. Available services: {names}."}

    dt = _parse_datetime(f"{booking.date} {booking.time}") or _parse_datetime(f"{booking.date}T{booking.time}")
    if dt is None:
        return {"success": False, "message": "I could not understand the appointment date and time. Please re-confirm them with the caller."}
    ok, reason = clinic.is_within_working_hours(dt)
    if not ok:
        return {"success": False, "message": reason}

    iso = dt.strftime("%Y-%m-%dT%H:%M")
    if storage.slot_taken(iso):
        return {"success": False, "message": "That slot was just booked. Please offer the caller a different time."}

    appointment = storage.create_appointment(
        patient_name=booking.patient_name,
        phone=booking.phone,
        email=booking.email,
        service=svc["name"],
        appointment_time=iso,
        notes=booking.notes,
        call_id=(call or {}).get("call_id"),
    )
    confirmations = notifications.send_booking_confirmation(appointment)
    logger.info("Booked %s for %s", appointment["appointment_id"], booking.patient_name)

    return {
        "success": True,
        "appointment_id": appointment["appointment_id"],
        "message": (
            f"Appointment confirmed for {booking.patient_name} - {svc['name']} on "
            f"{dt.strftime('%A, %d %B at %I:%M %p')}. Booking ID {appointment['appointment_id']}."
        ),
        "confirmations": confirmations,
    }


@app.post("/retell/answer-faq")
async def answer_faq(request: Request) -> dict:
    """Custom function: answer_faq(question). Grounded FAQ lookup."""
    args, _call = await _retell_args(request)
    question = str(args.get("question", "")).strip()
    faq = clinic.find_faq(question)
    if faq is None:
        return {
            "found": False,
            "answer": (
                "I do not have that information. Offer to transfer the caller to the "
                "front desk, or take a message with their name and number."
            ),
        }
    return {"found": True, "answer": faq["answer"]}


# ---------------------------------------------------------------------------
# RetellAI call lifecycle webhook
# ---------------------------------------------------------------------------

@app.post("/retell/webhook")
async def retell_webhook(request: Request) -> dict:
    """Receives call_started / call_ended / call_analyzed events from Retell."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return {"received": False}

    event = body.get("event", "unknown")
    call = body.get("call") or {}
    analysis = call.get("call_analysis") or {}
    storage.log_call_event(
        call_id=call.get("call_id"),
        caller_number=call.get("from_number"),
        event=event,
        summary=analysis.get("call_summary"),
        sentiment=analysis.get("user_sentiment"),
    )
    logger.info("Retell webhook: %s (%s)", event, call.get("call_id"))
    return {"received": True}


# ---------------------------------------------------------------------------
# Dashboard read APIs
# ---------------------------------------------------------------------------

@app.get("/appointments")
async def appointments() -> dict:
    return {"appointments": storage.list_appointments()}


@app.get("/call-logs")
async def call_logs() -> dict:
    return {"call_logs": storage.list_call_logs()}
