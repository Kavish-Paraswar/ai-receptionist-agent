"""One-shot script: create the Conversation Flow + Agent on RetellAI.

Usage:
    export RETELL_API_KEY=key_xxx
    export BACKEND_URL=https://your-deployment.vercel.app   # your deployed backend
    python retell/create_agent.py

It reads conversation-flow.json, rewrites the tool URLs to point at your
backend, creates the conversation flow, then creates an agent bound to it.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx

API_BASE = "https://api.retellai.com"


def main() -> None:
    api_key = os.environ.get("RETELL_API_KEY")
    if not api_key:
        sys.exit("Set RETELL_API_KEY first (dashboard -> API Keys).")
    backend_url = os.environ.get("BACKEND_URL", "").rstrip("/")

    flow = json.loads((Path(__file__).parent / "conversation-flow.json").read_text())

    if backend_url:
        for tool in flow.get("tools", []):
            if tool.get("type") == "custom":
                path = tool["url"].split(".vercel.app", 1)[-1]
                tool["url"] = f"{backend_url}{path}"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    resp = httpx.post(f"{API_BASE}/create-conversation-flow", json=flow, headers=headers, timeout=30)
    resp.raise_for_status()
    flow_id = resp.json()["conversation_flow_id"]
    print(f"Created conversation flow: {flow_id}")

    agent_payload = {
        "agent_name": "QuensultingAI Dental Clinic Receptionist",
        "voice_id": "11labs-Anjali",
        "language": "en-IN",
        "response_engine": {"type": "conversation-flow", "conversation_flow_id": flow_id},
        "webhook_url": f"{backend_url}/api/retell/webhook" if backend_url else None,
        "enable_backchannel": True,
        "interruption_sensitivity": 0.9,
        "responsiveness": 0.9,
        "end_call_after_silence_ms": 30000,
        "max_call_duration_ms": 600000,
        "post_call_analysis_data": [
            {
                "type": "string",
                "name": "booking_outcome",
                "description": "Whether an appointment was booked, and the booking ID if so.",
            }
        ],
    }
    agent_payload = {k: v for k, v in agent_payload.items() if v is not None}

    resp = httpx.post(f"{API_BASE}/create-agent", json=agent_payload, headers=headers, timeout=30)
    resp.raise_for_status()
    agent = resp.json()
    print(f"Created agent: {agent['agent_id']}")
    print("Open the Retell dashboard to attach a phone number and test the call.")


if __name__ == "__main__":
    main()
