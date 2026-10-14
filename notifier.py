"""
SafeFall AI — Simulated Emergency Dispatch Module
Clearly marked simulation of SMS, WhatsApp, and automated voice dispatch.
NOTE: As required by safety guidelines, this is strictly a simulated notification engine.
No real network calls or cellular messages are sent to external carriers.
"""

import datetime
from typing import List, Dict, Any, Optional

DEFAULT_CONTACTS = [
    {
        "name": "Sarah Miller",
        "relation": "Primary Caregiver (Daughter)",
        "phone": "+1 (555) 234-8901",
        "channels": ["SMS", "WhatsApp", "Voice Call"],
        "priority": 1
    },
    {
        "name": "Dr. Robert Chen",
        "relation": "Attending Physician / Family Doctor",
        "phone": "+1 (555) 782-4412",
        "channels": ["SMS", "WhatsApp"],
        "priority": 2
    },
    {
        "name": "Building Concierge / Security Desk",
        "relation": "On-Site First Responder",
        "phone": "+1 (555) 901-3320",
        "channels": ["Automated Voice", "SMS"],
        "priority": 3
    }
]


def format_sms_payload(incident_id: int, room: str, severity: str, verification_result: str, timestamp: str) -> str:
    """Generate mock SMS text format."""
    return (
        f"[SIMULATED SMS - SafeFall AI Alert]\n"
        f"INCIDENT #{incident_id} | SEVERITY: {severity.upper()}\n"
        f"Location: {room}\n"
        f"Time: {timestamp}\n"
        f"Status: {verification_result}\n"
        f"Action: Primary caregiver requested to check on resident immediately.\n"
        f"(SIMULATION: Demo notification only. No real SMS sent.)"
    )


def format_whatsapp_payload(incident_id: int, room: str, severity: str, verification_result: str, timestamp: str) -> str:
    """Generate mock WhatsApp rich template text."""
    urgency_emoji = "🚨" if severity in ["High", "Critical"] else "⚠️"
    return (
        f"{urgency_emoji} *[SIMULATED WHATSAPP EMERGENCY ALERT]*\n"
        f"*SafeFall AI Incident Triage Engine*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"• *Incident ID:* #{incident_id}\n"
        f"• *Room/Zone:* {room}\n"
        f"• *Severity Level:* {severity.upper()}\n"
        f"• *Verification:* {verification_result}\n"
        f"• *Timestamp:* {timestamp}\n"
        f"• *Location Pin:* Residence Zone 4 (Coordinates: [SIMULATED GPS])\n"
        f"• *Intercom Link:* https://safefall.local/intercom/{incident_id} (Demo)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *SIMULATION ONLY:* No actual WhatsApp transmission occurred."
    )


def format_voice_call_transcript(incident_id: int, room: str, severity: str, verification_result: str) -> str:
    """Generate simulated automated voice call text-to-speech transcript."""
    return (
        f"[SIMULATED VOICE CALL TRANSCRIPT - TTS ENGINE]\n"
        f"\"Urgent alert from SafeFall AI. A potential fall has been detected in {room}. "
        f"Verification status is: {verification_result}. Severity level is evaluated as {severity}. "
        f"Please press 1 to connect to the residence speakerphone, or press 2 to acknowledge escalation.\" "
        f"[CALL DURATION: 18s | RESULT: Call Answered & Acknowledged (SIMULATED)]"
    )


def execute_simulated_dispatch(
    incident_id: int,
    room: str,
    severity: str,
    verification_result: str,
    contacts: Optional[List[Dict[str, Any]]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run simulated multi-channel dispatch for an escalated incident.
    Returns structured audit record with all dispatched simulated messages.
    """
    if contacts is None:
        contacts = DEFAULT_CONTACTS
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dispatched_items = []

    for contact in contacts:
        for channel in contact.get("channels", []):
            if channel == "SMS":
                payload = format_sms_payload(incident_id, room, severity, verification_result, timestamp)
            elif channel == "WhatsApp":
                payload = format_whatsapp_payload(incident_id, room, severity, verification_result, timestamp)
            elif channel in ["Voice Call", "Automated Voice"]:
                payload = format_voice_call_transcript(incident_id, room, severity, verification_result)
            else:
                payload = f"[SIMULATED ALERT] {severity} fall in {room}"

            item = {
                "channel": channel,
                "contact_name": contact["name"],
                "relation": contact["relation"],
                "phone": contact["phone"],
                "timestamp": timestamp,
                "status": "SIMULATED - DELIVERED TO LOG",
                "payload": payload,
                "simulation_disclaimer": "Prototype simulation only — no real network or telecom activity performed."
            }
            dispatched_items.append(item)

    summary_text = (
        f"Dispatched {len(dispatched_items)} simulated notifications across "
        f"{len(contacts)} contacts (SMS, WhatsApp, Voice)."
    )

    return {
        "incident_id": incident_id,
        "timestamp": timestamp,
        "summary": summary_text,
        "dispatches": dispatched_items,
        "status": "SIMULATED DISPATCH SENT"
    }
