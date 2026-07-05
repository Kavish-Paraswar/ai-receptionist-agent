"""Booking confirmations.

Mandatory integration: after a successful booking we trigger
1. A confirmation email via SMTP (if SMTP_* env vars are set), and/or
2. An outbound webhook (if CONFIRMATION_WEBHOOK_URL is set).

Both are fire-and-forget from the caller's perspective - a notification
failure must never fail the booking itself.
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

import httpx

logger = logging.getLogger("notifications")


def _send_email(appointment: dict) -> dict:
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    port = int(os.environ.get("SMTP_PORT", "587"))
    sender = os.environ.get("SMTP_FROM", user or "")
    recipient = appointment.get("email")

    if not (host and user and password):
        return {"channel": "email", "sent": False, "reason": "SMTP not configured"}
    if not recipient:
        return {"channel": "email", "sent": False, "reason": "Caller did not provide an email"}

    msg = EmailMessage()
    msg["Subject"] = f"Appointment Confirmed - {appointment['appointment_id']}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(
        f"Dear {appointment['patient_name']},\n\n"
        f"Your appointment at QuensultingAI Dental Clinic is confirmed.\n\n"
        f"  Booking ID:  {appointment['appointment_id']}\n"
        f"  Service:     {appointment['service']}\n"
        f"  Date & Time: {appointment['appointment_time']}\n\n"
        f"Address: 2nd Floor, Sunrise Plaza, FC Road, Pune 411005\n"
        f"Please arrive 10 minutes early. To reschedule, call us at +91 20 4567 8900.\n\n"
        f"Warm regards,\nQuensultingAI Dental Clinic"
    )
    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)
        return {"channel": "email", "sent": True}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Email send failed: %s", exc)
        return {"channel": "email", "sent": False, "reason": str(exc)}


def _fire_webhook(appointment: dict) -> dict:
    url = os.environ.get("CONFIRMATION_WEBHOOK_URL")
    if not url:
        return {"channel": "webhook", "sent": False, "reason": "CONFIRMATION_WEBHOOK_URL not configured"}
    try:
        resp = httpx.post(
            url,
            json={"event": "appointment.confirmed", "appointment": appointment},
            timeout=10,
        )
        return {"channel": "webhook", "sent": resp.is_success, "status_code": resp.status_code}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Confirmation webhook failed: %s", exc)
        return {"channel": "webhook", "sent": False, "reason": str(exc)}


def send_booking_confirmation(appointment: dict) -> list[dict]:
    """Trigger all configured confirmation channels. Never raises."""
    results = [_send_email(appointment), _fire_webhook(appointment)]
    logger.info("Confirmation results for %s: %s", appointment["appointment_id"], results)
    return results


def notification_status() -> dict:
    return {
        "email_configured": bool(os.environ.get("SMTP_HOST") and os.environ.get("SMTP_USER")),
        "webhook_configured": bool(os.environ.get("CONFIRMATION_WEBHOOK_URL")),
    }
