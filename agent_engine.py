"""
SafeFall AI — Agentic Emergency Response & Context-Aware Triage Engine
Evaluates fall signals, contextual risk factors (room hazard, time of day, response),
and generates actionable emergency recommendations and incident reports.
"""

import datetime
from typing import Dict, Any, Optional

ROOM_RISK_MODIFIERS = {
    "Bathroom": {
        "risk_level": "High Risk Zone",
        "hazards": "Hard tile surfaces, high moisture/slip probability, confined space",
        "urgency_boost": True
    },
    "Staircase": {
        "risk_level": "Critical Risk Zone",
        "hazards": "High kinetic impact hazard, potential head trauma risk",
        "urgency_boost": True
    },
    "Kitchen": {
        "risk_level": "Medium Risk Zone",
        "hazards": "Hard flooring, appliances, potential spill hazards",
        "urgency_boost": False
    },
    "Bedroom": {
        "risk_level": "Moderate Risk Zone",
        "hazards": "Bed-height transfer hazard, low nighttime lighting",
        "urgency_boost": False
    },
    "Living Room": {
        "risk_level": "Low/Moderate Risk Zone",
        "hazards": "Area rugs, coffee tables, standard residential layout",
        "urgency_boost": False
    }
}


def evaluate_incident(
    room: str,
    verification_result: str,
    detection_source: str = "Simulated Fall Trigger",
    elapsed_seconds: Optional[float] = None
) -> Dict[str, Any]:
    """
    Perform agentic context-aware triage on a fall detection event.

    Args:
        room: Monitored room name
        verification_result: 'Confirmed OK', 'Help Requested', or 'No Response (Timeout)'
        detection_source: Name of detector trigger
        elapsed_seconds: Time taken to verify or timeout

    Returns:
        Structured evaluation with severity, status, reasoning, and recommended action.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    room_info = ROOM_RISK_MODIFIERS.get(room, {
        "risk_level": "General Zone",
        "hazards": "Standard domestic environment",
        "urgency_boost": False
    })

    is_high_risk_zone = room_info["urgency_boost"]

    # Agent triage decision matrix
    if verification_result == "Confirmed OK":
        severity = "Low"
        event_status = "Resolved - False Alarm"
        urgency_label = "Green (Safe / Self-Resolved)"
        dispatch_status = "CANCELLED (User Verified OK)"
        reasoning = (
            f"Resident actively acknowledged safety check within "
            f"{f'{elapsed_seconds:.1f}s' if elapsed_seconds else 'countdown window'}. "
            f"No physical assistance required. Room: {room} ({room_info['risk_level']})."
        )
        recommended_action = (
            "Log self-verified safe status. Maintain standard passive monitoring. "
            "No caregiver dispatch or audible alarm required."
        )

    elif verification_result == "Help Requested":
        severity = "Critical" if is_high_risk_zone else "High"
        event_status = "Escalated - Help Requested"
        urgency_label = "Red (Active Assistance Required)"
        dispatch_status = "SIMULATED DISPATCH SENT"
        reasoning = (
            f"Resident actively triggered HELP button in {room} ({room_info['risk_level']}). "
            f"Key environmental factors: {room_info['hazards']}."
        )
        recommended_action = (
            f"Dispatch primary caregiver immediately via Simulated SMS & WhatsApp. "
            f"Activate 2-way room speakerphone/intercom. "
            f"Confirm caregiver arrival within 10 minutes or escalate to emergency services relay."
        )

    else:  # No Response (Timeout)
        severity = "Critical"
        event_status = "Escalated - Timeout / Unresponsive"
        urgency_label = "Flashing Red (Resident Unresponsive)"
        dispatch_status = "SIMULATED DISPATCH SENT"
        reasoning = (
            f"Countdown timer expired with ZERO response in {room}. "
            f"Resident is potentially immobilized or unable to reach controls. "
            f"Zone Risk: {room_info['risk_level']} - {room_info['hazards']}."
        )
        recommended_action = (
            f"URGENT: Trigger automated voice dispatch to primary contact and concierge. "
            f"Sound local smart beacon chime in residence. "
            f"Prepare building access PIN for emergency responders if unattended."
        )

    return {
        "timestamp": timestamp,
        "room": room,
        "detection_source": detection_source,
        "event_status": event_status,
        "verification_result": verification_result,
        "severity": severity,
        "urgency_label": urgency_label,
        "dispatch_status": dispatch_status,
        "reasoning": reasoning,
        "recommended_action": recommended_action,
        "room_info": room_info
    }
