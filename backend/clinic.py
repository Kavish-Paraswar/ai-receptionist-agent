"""Static clinic configuration and FAQ knowledge base.

Single source of truth for clinic business rules used by the
availability checker, booking validator, and FAQ answering endpoint.
"""

from __future__ import annotations

from datetime import datetime, time

CLINIC_NAME = "QuensultingAI Dental Clinic"
CLINIC_ADDRESS = "2nd Floor, Sunrise Plaza, FC Road, Pune, Maharashtra 411005"
CLINIC_PHONE = "+91 20 4567 8900"

# Monday=0 ... Sunday=6. Clinic is closed on Sunday.
WORKING_DAYS = {0, 1, 2, 3, 4, 5}
OPEN_TIME = time(9, 0)
CLOSE_TIME = time(18, 0)
SLOT_MINUTES = 30

SERVICES: list[dict] = [
    {"id": "dental_cleaning", "name": "Dental Cleaning", "duration_min": 30, "fee_inr": 1200},
    {"id": "root_canal", "name": "Root Canal Treatment", "duration_min": 60, "fee_inr": 6500},
    {"id": "teeth_whitening", "name": "Teeth Whitening", "duration_min": 45, "fee_inr": 4000},
    {"id": "braces_consultation", "name": "Braces Consultation", "duration_min": 30, "fee_inr": 800},
    {"id": "tooth_extraction", "name": "Tooth Extraction", "duration_min": 45, "fee_inr": 2500},
    {"id": "general_consultation", "name": "General Dental Consultation", "duration_min": 30, "fee_inr": 500},
]

FAQS: list[dict] = [
    {
        "id": "timings",
        "keywords": ["timing", "timings", "hours", "open", "close", "when"],
        "question": "What are your clinic timings?",
        "answer": "We are open Monday to Saturday, 9:00 AM to 6:00 PM. We are closed on Sundays.",
    },
    {
        "id": "walk_in",
        "keywords": ["walk-in", "walk in", "walkin", "without appointment", "directly"],
        "question": "Do you accept walk-in patients?",
        "answer": "Yes, we accept walk-in patients, but appointments get priority. During busy hours walk-ins may need to wait 30 to 45 minutes, so we recommend booking a slot.",
    },
    {
        "id": "consultation_fee",
        "keywords": ["fee", "fees", "cost", "price", "charge", "consultation fee"],
        "question": "What is the consultation fee?",
        "answer": "A general dental consultation is 500 rupees. Specialist consultations like braces consultation are 800 rupees. Treatment costs are quoted after the initial examination.",
    },
    {
        "id": "location",
        "keywords": ["where", "location", "address", "located", "reach", "directions"],
        "question": "Where is the clinic located?",
        "answer": f"We are located at {CLINIC_ADDRESS}. We are a two minute walk from the FC Road bus stop, and parking is available in the building.",
    },
    {
        "id": "emergency",
        "keywords": ["emergency", "urgent", "pain", "immediately", "asap"],
        "question": "Do you provide emergency appointments?",
        "answer": "Yes. For dental emergencies during working hours we keep buffer slots and will see you the same day. For severe emergencies please mention it and we can transfer you to our front desk immediately.",
    },
    {
        "id": "payment",
        "keywords": ["payment", "pay", "upi", "card", "cash", "insurance"],
        "question": "What payment methods do you accept?",
        "answer": "We accept cash, all major credit and debit cards, and UPI. We also support most major dental insurance plans - please carry your insurance details to your visit.",
    },
]


def get_service(service_query: str) -> dict | None:
    """Fuzzy-match a spoken service name to a configured service."""
    q = (service_query or "").strip().lower()
    if not q:
        return None
    for svc in SERVICES:
        if q == svc["id"] or q == svc["name"].lower():
            return svc
    # Partial keyword match (e.g. "cleaning" -> Dental Cleaning)
    for svc in SERVICES:
        name = svc["name"].lower()
        if q in name or any(word in name for word in q.split()):
            return svc
    return None


def is_within_working_hours(dt: datetime) -> tuple[bool, str]:
    """Validate a requested appointment datetime against clinic hours."""
    if dt.weekday() not in WORKING_DAYS:
        return False, "The clinic is closed on Sundays. We are open Monday to Saturday, 9 AM to 6 PM."
    if not (OPEN_TIME <= dt.time() < CLOSE_TIME):
        return False, "That time is outside our working hours. We are open 9 AM to 6 PM, Monday to Saturday."
    return True, "ok"


def find_faq(query: str) -> dict | None:
    """Keyword-score FAQ lookup for the answer_faq custom function."""
    q = (query or "").lower()
    if not q:
        return None
    best, best_score = None, 0
    for faq in FAQS:
        score = sum(1 for kw in faq["keywords"] if kw in q)
        if score > best_score:
            best, best_score = faq, score
    return best
