"""
SafeFall AI — Persistent SQLite Database Module
Stores incidents, sensor logs, and system audit trails.
"""

import sqlite3
import datetime
import os
from typing import List, Dict, Any, Optional
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "safefall.db")


def get_connection() -> sqlite3.Connection:
    """Create or retrieve a SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Incidents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            room TEXT NOT NULL,
            detection_source TEXT NOT NULL,
            event_status TEXT NOT NULL,
            verification_result TEXT NOT NULL,
            severity TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            dispatch_status TEXT NOT NULL,
            dispatch_details TEXT,
            notes TEXT
        )
    """)

    # Audit system log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_incident(
    room: str,
    detection_source: str,
    event_status: str,
    verification_result: str,
    severity: str,
    recommended_action: str,
    dispatch_status: str = "SIMULATED DISPATCH SENT",
    dispatch_details: str = "",
    notes: str = "",
    timestamp: Optional[str] = None
) -> int:
    """Insert a new fall incident into the database and return its row ID."""
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO incidents (
            timestamp, room, detection_source, event_status,
            verification_result, severity, recommended_action,
            dispatch_status, dispatch_details, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, room, detection_source, event_status,
        verification_result, severity, recommended_action,
        dispatch_status, dispatch_details, notes
    ))
    incident_id = cursor.lastrowid
    conn.commit()

    # Log to audit log
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, event_type, message)
        VALUES (?, ?, ?)
    """, (timestamp, "INCIDENT_RECORDED", f"Incident #{incident_id} ({severity}) in {room}: {event_status}"))
    conn.commit()
    conn.close()
    return incident_id


def get_all_incidents(limit: int = 100) -> pd.DataFrame:
    """Retrieve all incidents as a pandas DataFrame ordered by most recent."""
    conn = get_connection()
    query = "SELECT * FROM incidents ORDER BY id DESC LIMIT ?"
    try:
        df = pd.read_sql_query(query, conn, params=(limit,))
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def get_incident_by_id(incident_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve details of a single incident."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_incident_statistics() -> Dict[str, Any]:
    """Calculate key analytics for the dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM incidents")
    total_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE event_status LIKE '%Escalated%'")
    escalated_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE verification_result = 'Confirmed OK'")
    ok_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM incidents WHERE verification_result LIKE '%No Response%'")
    unresponsive_count = cursor.fetchone()[0]

    cursor.execute("SELECT severity, COUNT(*) FROM incidents GROUP BY severity")
    severity_breakdown = dict(cursor.fetchall())

    cursor.execute("SELECT room, COUNT(*) FROM incidents GROUP BY room")
    room_breakdown = dict(cursor.fetchall())

    conn.close()

    return {
        "total_incidents": total_count,
        "escalated_count": escalated_count,
        "ok_count": ok_count,
        "unresponsive_count": unresponsive_count,
        "severity_breakdown": severity_breakdown,
        "room_breakdown": room_breakdown
    }


def clear_all_incidents() -> None:
    """Clear all records from database (for demo resets)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incidents")
    cursor.execute("DELETE FROM audit_logs")
    cursor.execute("INSERT INTO audit_logs (timestamp, event_type, message) VALUES (?, ?, ?)",
                   (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "SYSTEM_RESET", "Incident history cleared by operator"))
    conn.commit()
    conn.close()


def seed_demo_data() -> None:
    """Populate database with sample realistic incidents for immediate evaluation."""
    now = datetime.datetime.now()
    sample_records = [
        (
            (now - datetime.timedelta(hours=26)).strftime("%Y-%m-%d %H:%M:%S"),
            "Living Room",
            "Simulated Fall Trigger",
            "Resolved - False Alarm",
            "Confirmed OK",
            "Low",
            "Log self-verified safe status; no caregiver dispatch required.",
            "CANCELLED (User Verified OK)",
            "User tapped 'I am OK' within 4s. Escalation halted.",
            "Slip on area rug, recovered unassisted."
        ),
        (
            (now - datetime.timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S"),
            "Kitchen",
            "Webcam Vision Model",
            "Escalated - Help Requested",
            "Help Requested",
            "High",
            "Dispatch designated caregiver, open 2-way intercom, alert local responder.",
            "SIMULATED DISPATCH SENT",
            "Simulated SMS to Caregiver (Sarah M.) & Simulated WhatsApp emergency message.",
            "User pressed 'Need Help' after loss of balance."
        ),
        (
            (now - datetime.timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
            "Bathroom",
            "Synthetic Sensor Simulation",
            "Escalated - Timeout / Unresponsive",
            "No Response (Timeout)",
            "Critical",
            "URGENT: Initiate EMS dispatch protocol, alert building concierge, trigger beacon chime.",
            "SIMULATED DISPATCH SENT",
            "Simulated Automated Voice Call to Primary Contact (Dr. Robert Chen, son) & Simulated SMS to 911 proxy relay.",
            "No response to 15s verification countdown in high-moisture hazard zone."
        ),
    ]

    conn = get_connection()
    cursor = conn.cursor()
    for rec in sample_records:
        cursor.execute("""
            INSERT INTO incidents (
                timestamp, room, detection_source, event_status,
                verification_result, severity, recommended_action,
                dispatch_status, dispatch_details, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rec)
    conn.commit()
    conn.close()


# Initialize on import
init_db()
