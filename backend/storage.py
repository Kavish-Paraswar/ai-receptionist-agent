"""Persistence layer.

Primary store: SQLite (always on, keeps the dashboard working with zero setup).
Mandatory integration: Google Sheets - every appointment and call log row is
mirrored to a Google Sheet when GOOGLE_SERVICE_ACCOUNT_JSON + GOOGLE_SHEET_ID
are configured. Sheet failures never block a booking (fail-open by design,
errors are surfaced on the /integrations status endpoint).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("storage")

DB_PATH = Path(os.environ.get("DB_PATH", Path(__file__).parent / "clinic.db"))

_lock = threading.Lock()

APPOINTMENT_HEADERS = [
    "appointment_id", "patient_name", "phone", "email", "service",
    "appointment_time", "notes", "status", "call_id", "created_at",
]
CALL_LOG_HEADERS = [
    "call_id", "caller_number", "event", "summary", "sentiment", "created_at",
]


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock, _conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS appointments (
                appointment_id TEXT PRIMARY KEY,
                patient_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                service TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'confirmed',
                call_id TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT,
                caller_number TEXT,
                event TEXT,
                summary TEXT,
                sentiment TEXT,
                created_at TEXT NOT NULL
            )"""
        )


# ---------------------------------------------------------------------------
# Google Sheets mirror
# ---------------------------------------------------------------------------

_sheets_status: dict = {"configured": False, "connected": False, "error": None}


def _get_sheet():
    """Return the gspread spreadsheet, or None if not configured."""
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not creds_json or not sheet_id:
        _sheets_status.update(configured=False, connected=False, error=None)
        return None
    _sheets_status["configured"] = True
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds = Credentials.from_service_account_info(
            json.loads(creds_json),
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        _sheets_status.update(connected=True, error=None)
        return sheet
    except Exception as exc:  # noqa: BLE001 - fail open, report on status endpoint
        logger.warning("Google Sheets unavailable: %s", exc)
        _sheets_status.update(connected=False, error=str(exc))
        return None


def _append_to_sheet(worksheet_title: str, headers: list[str], row: list) -> bool:
    sheet = _get_sheet()
    if sheet is None:
        return False
    try:
        try:
            ws = sheet.worksheet(worksheet_title)
        except Exception:  # worksheet missing -> create with header row
            ws = sheet.add_worksheet(title=worksheet_title, rows=1000, cols=len(headers))
            ws.append_row(headers)
        ws.append_row([str(v) if v is not None else "" for v in row])
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to append to Google Sheet: %s", exc)
        _sheets_status.update(error=str(exc))
        return False


def sheets_status() -> dict:
    _get_sheet()  # refresh status
    return dict(_sheets_status)


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

def create_appointment(
    *,
    patient_name: str,
    phone: str,
    email: str | None,
    service: str,
    appointment_time: str,
    notes: str | None,
    call_id: str | None,
) -> dict:
    appointment = {
        "appointment_id": f"APT-{uuid.uuid4().hex[:8].upper()}",
        "patient_name": patient_name,
        "phone": phone,
        "email": email,
        "service": service,
        "appointment_time": appointment_time,
        "notes": notes,
        "status": "confirmed",
        "call_id": call_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock, _conn() as conn:
        conn.execute(
            """INSERT INTO appointments
               (appointment_id, patient_name, phone, email, service,
                appointment_time, notes, status, call_id, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            [appointment[h] for h in APPOINTMENT_HEADERS],
        )
    synced = _append_to_sheet(
        "Appointments", APPOINTMENT_HEADERS, [appointment[h] for h in APPOINTMENT_HEADERS]
    )
    appointment["synced_to_sheets"] = synced
    return appointment


def list_appointments() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM appointments ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def slot_taken(appointment_time: str) -> bool:
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM appointments WHERE appointment_time = ? AND status = 'confirmed' LIMIT 1",
            (appointment_time,),
        ).fetchone()
    return row is not None


def booked_times_for_date(date_prefix: str) -> set[str]:
    """All confirmed appointment ISO times starting with YYYY-MM-DD."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT appointment_time FROM appointments WHERE status='confirmed' AND appointment_time LIKE ?",
            (f"{date_prefix}%",),
        ).fetchall()
    return {r["appointment_time"] for r in rows}


# ---------------------------------------------------------------------------
# Call logs
# ---------------------------------------------------------------------------

def log_call_event(
    *,
    call_id: str | None,
    caller_number: str | None,
    event: str,
    summary: str | None = None,
    sentiment: str | None = None,
) -> dict:
    entry = {
        "call_id": call_id,
        "caller_number": caller_number,
        "event": event,
        "summary": summary,
        "sentiment": sentiment,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock, _conn() as conn:
        conn.execute(
            """INSERT INTO call_logs (call_id, caller_number, event, summary, sentiment, created_at)
               VALUES (?,?,?,?,?,?)""",
            [entry[h] for h in CALL_LOG_HEADERS],
        )
    _append_to_sheet("CallLogs", CALL_LOG_HEADERS, [entry[h] for h in CALL_LOG_HEADERS])
    return entry


def list_call_logs() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM call_logs ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    return [dict(r) for r in rows]
