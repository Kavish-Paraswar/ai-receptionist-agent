# AI Receptionist Voice Agent — QuensultingAI Dental Clinic

Take-home submission for the AI Voice Agent Intern position. An inbound-call AI receptionist built with **RetellAI Conversational Flow**, a **Python (FastAPI)** automation backend, **Google Sheets** persistence, and **email/webhook** booking confirmations — plus a Next.js admin dashboard.

## Architecture

```
Caller ──> RetellAI Conversational Flow agent
              │  custom function webhooks (check_availability, book_appointment, answer_faq)
              │  call lifecycle webhook (call_started / ended / analyzed)
              ▼
        FastAPI backend (/api)
              ├── SQLite (always-on local store, powers the dashboard)
              ├── Google Sheets (mirrors appointments + call logs)
              └── Confirmation email (SMTP) + outbound webhook
              ▲
        Next.js admin dashboard (appointments, call logs, FAQs, integration status)
```

## Repository layout

| Path | Purpose |
|---|---|
| `retell/conversation-flow.json` | RetellAI Conversational Flow agent JSON (nodes, edges, tools) — the submission artifact |
| `retell/create_agent.py` | Script to create the flow + agent on Retell via API |
| `backend/` | FastAPI automation service (booking, availability, FAQ, webhooks, integrations) |
| `frontend/` | Next.js admin dashboard |
| `vercel.json` | Multi-service deployment config (frontend at `/`, backend at `/api`) |

## Conversation design

The flow uses proper conversation nodes and branching (no prompt-only implementation):

- **Greeting & intent detection** → routes to booking, FAQ, or human transfer
- **FAQ answering** via a `answer_faq` custom function (grounded lookup — the agent never invents facts)
- **Booking pipeline**: collect details one at a time → `check_availability` function node → read-back confirmation → `book_appointment` function node → success/failure branches
- **Error handling**: invalid dates, closed days (Sunday), out-of-hours requests, double-booked slots, and booking failures each have recovery paths
- **Fallback node** for unclear intent (two attempts, then offers a human)
- **Transfer node** (cold transfer to front desk) with a transfer-failed branch that takes a message
- **Interruption handling** via high `interruption_sensitivity`, backchanneling, and short 1–2 sentence responses enforced in the global prompt

## Backend endpoints

| Endpoint | Used by |
|---|---|
| `POST /api/retell/check-availability` | Retell custom function — validates hours, suggests open slots |
| `POST /api/retell/book-appointment` | Retell custom function — validates, persists, triggers confirmations |
| `POST /api/retell/answer-faq` | Retell custom function — grounded FAQ lookup |
| `POST /api/retell/webhook` | Retell agent-level webhook — logs call events + post-call analysis |
| `GET /api/appointments`, `/api/call-logs`, `/api/clinic`, `/api/integrations`, `/api/health` | Dashboard |

All booking writes go to SQLite (so the demo works with zero setup) and are mirrored to Google Sheets when configured. Integration failures are fail-open: they never break a live call.

## Environment variables (all optional — app runs without them)

| Variable | Purpose |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service-account JSON (share your sheet with its `client_email`) |
| `GOOGLE_SHEET_ID` | Target spreadsheet ID (from the sheet URL) |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | Confirmation emails |
| `CONFIRMATION_WEBHOOK_URL` | Fires `appointment.confirmed` JSON payload after each booking |
| `RETELL_API_KEY`, `BACKEND_URL` | Only needed by `retell/create_agent.py` |

## Setting up the Retell agent

1. Deploy this project (Publish button in v0, or `vercel deploy`).
2. Option A — script: `RETELL_API_KEY=... BACKEND_URL=https://your-app.vercel.app python retell/create_agent.py`
3. Option B — manual: import/recreate `retell/conversation-flow.json` in the Retell dashboard, replacing `https://YOUR-DEPLOYMENT.vercel.app` in the three tool URLs with your deployment URL, and set the agent webhook to `https://your-app.vercel.app/api/retell/webhook`.
4. Attach a phone number to the agent and call it.

## Testing without a phone call

The dashboard includes a **Test the booking function** panel that posts the exact Retell custom-function payload to the backend, so the whole pipeline (validation → SQLite → Sheets → confirmation) can be demonstrated in the Loom walkthrough.

## Design decisions

- **Fail-open integrations**: a Sheets or SMTP outage must never cause a live caller's booking to fail; errors surface on the dashboard's integration panel instead.
- **Server-side validation as the source of truth**: the LLM collects data, but working hours, service catalog, slot conflicts, and required fields are all enforced in Python.
- **Grounded FAQ tool** instead of prompt knowledge, so answers stay consistent and auditable.
- **SQLite + Sheets dual-write** keeps the demo runnable with zero credentials while satisfying the mandatory Sheets integration.
