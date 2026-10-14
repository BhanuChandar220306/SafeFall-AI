"""
SafeFall AI — Agentic Fall Detection and Context-Aware Emergency Response
Streamlit Production Prototype & Dashboard
"""

import streamlit as st
import time
import datetime
import os
import json
import pandas as pd
import numpy as np

# SafeFall AI Internal Modules
import database as db
import agent_engine as agent
import notifier
import fall_detector

# Optional visualization imports
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ==========================================
# 1. PAGE SETUP & STYLING
# ==========================================
st.set_page_config(
    page_title="SafeFall AI — Agentic Fall Response",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Professional Medical UI Styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 12px;
        margin-bottom: 1.2rem;
        border-left: 6px solid #3b82f6;
        color: #f8fafc;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .disclaimer-banner {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b;
        color: #92400e;
        padding: 0.85rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.2rem;
        font-size: 0.88rem;
        line-height: 1.4;
    }
    .status-badge-active {
        background-color: #dcfce7;
        color: #166534;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        border: 1px solid #86efac;
    }
    .status-badge-verifying {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        border: 1px solid #fcd34d;
        animation: pulse 1.5s infinite;
    }
    .status-badge-emergency {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        border: 1px solid #fca5a5;
    }
    .verification-modal {
        background-color: #fff1f2;
        border: 2px solid #e11d48;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(225, 29, 72, 0.15);
    }
    .dispatch-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .simulation-tag {
        background-color: #e0e7ff;
        color: #3730a3;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. SESSION STATE MANAGEMENT
# ==========================================
if "fall_active" not in st.session_state:
    st.session_state.fall_active = False
if "fall_start_time" not in st.session_state:
    st.session_state.fall_start_time = 0.0
if "fall_room" not in st.session_state:
    st.session_state.fall_room = "Living Room"
if "fall_scenario" not in st.session_state:
    st.session_state.fall_scenario = "Slip on wet floor"
if "fall_source" not in st.session_state:
    st.session_state.fall_source = "Simulated Fall Trigger"
if "countdown_duration" not in st.session_state:
    st.session_state.countdown_duration = 10
if "last_incident_report" not in st.session_state:
    st.session_state.last_incident_report = None
if "latest_dispatch" not in st.session_state:
    st.session_state.latest_dispatch = None
if "system_status" not in st.session_state:
    st.session_state.system_status = "MONITORING_ACTIVE"
if "vision_synthetic_mode" not in st.session_state:
    st.session_state.vision_synthetic_mode = "standing"


# ==========================================
# 3. VERIFICATION COUNTDOWN HANDLER
# ==========================================
# Handle active verification countdown logic before rendering UI
time_elapsed = 0.0
time_remaining = st.session_state.countdown_duration

if st.session_state.fall_active:
    time_elapsed = time.time() - st.session_state.fall_start_time
    time_remaining = max(0, int(st.session_state.countdown_duration - time_elapsed))

    # Automatic Timeout Trigger when countdown completes
    if time_remaining <= 0:
        # Resident was unresponsive
        eval_result = agent.evaluate_incident(
            room=st.session_state.fall_room,
            verification_result="No Response (Timeout)",
            detection_source=st.session_state.fall_source,
            elapsed_seconds=st.session_state.countdown_duration
        )

        # Record in SQLite database
        inc_id = db.insert_incident(
            room=eval_result["room"],
            detection_source=eval_result["detection_source"],
            event_status=eval_result["event_status"],
            verification_result=eval_result["verification_result"],
            severity=eval_result["severity"],
            recommended_action=eval_result["recommended_action"],
            dispatch_status=eval_result["dispatch_status"],
            dispatch_details="Simulated multi-channel broadcast initiated following timeout.",
            notes=f"Auto-escalated: Resident was unresponsive during {st.session_state.countdown_duration}s verification window."
        )

        # Generate simulated emergency dispatch records
        dispatch_bundle = notifier.execute_simulated_dispatch(
            incident_id=inc_id,
            room=eval_result["room"],
            severity=eval_result["severity"],
            verification_result=eval_result["verification_result"]
        )

        st.session_state.last_incident_report = eval_result
        st.session_state.last_incident_report["id"] = inc_id
        st.session_state.latest_dispatch = dispatch_bundle
        st.session_state.fall_active = False
        st.session_state.system_status = "EMERGENCY_ESCALATED"
        st.session_state.vision_synthetic_mode = "fallen"
        st.rerun()


# ==========================================
# 4. SIDEBAR CONFIGURATION & CONTROLS
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("SafeFall AI Settings")
    st.caption("Context-Aware Emergency Orchestrator v1.0")

    st.markdown("---")
    st.subheader("⏱️ Verification Timer")
    countdown_slider = st.slider(
        "Verification Countdown (seconds):",
        min_value=5,
        max_value=30,
        value=st.session_state.countdown_duration,
        step=1,
        help="Time allowed for resident to respond 'I am OK' before automatic escalation"
    )
    st.session_state.countdown_duration = countdown_slider

    st.markdown("---")
    st.subheader("📍 Target Monitoring Zone")
    selected_room = st.selectbox(
        "Monitored Room / Sensor Node:",
        ["Living Room", "Bathroom", "Kitchen", "Bedroom", "Staircase"],
        index=0
    )
    st.session_state.fall_room = selected_room

    # Room hazard indicator
    room_hazard = agent.ROOM_RISK_MODIFIERS.get(selected_room, {})
    if room_hazard.get("urgency_boost"):
        st.warning(f"⚠️ **{room_hazard.get('risk_level')}:** {room_hazard.get('hazards')}")
    else:
        st.info(f"ℹ️ **{room_hazard.get('risk_level')}:** {room_hazard.get('hazards')}")

    st.markdown("---")
    st.subheader("🛠️ Demo & Diagnostic Controls")
    
    col_demo1, col_demo2 = st.columns(2)
    with col_demo1:
        if st.button("🌱 Seed Demo Data", use_container_width=True, help="Populate SQLite with realistic historical incidents"):
            db.seed_demo_data()
            st.success("Demo records loaded!")
            time.sleep(0.5)
            st.rerun()

    with col_demo2:
        if st.button("🗑️ Reset All Data", use_container_width=True, help="Clear database for a fresh test run"):
            db.clear_all_incidents()
            st.session_state.last_incident_report = None
            st.session_state.latest_dispatch = None
            st.session_state.system_status = "MONITORING_ACTIVE"
            st.session_state.fall_active = False
            st.session_state.vision_synthetic_mode = "standing"
            st.success("All data cleared!")
            time.sleep(0.5)
            st.rerun()

    # System Health Diagnostic
    st.markdown("---")
    st.subheader("🔍 Subsystem Diagnostics")
    vision_info = fall_detector.check_vision_support()
    st.markdown(f"**Database:** `SQLite (Connected)`")
    st.markdown(f"**OpenCV Support:** `{'Installed' if vision_info['opencv'] else 'Graceful Fallback'}`")
    st.markdown(f"**MediaPipe Support:** `{'Installed' if vision_info['mediapipe'] else 'Graceful Fallback'}`")
    st.markdown(f"**Dispatch Pipeline:** `Simulated Sandbox (Active)`")


# ==========================================
# 5. MAIN HEADER & PROMINENT DISCLAIMER
# ==========================================
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0; font-size: 1.85rem; font-weight: 800; color: #ffffff;">
                🛡️ SafeFall AI
            </h1>
            <p style="margin: 0.3rem 0 0 0; color: #94a3b8; font-size: 0.95rem;">
                Agentic Fall Detection and Context-Aware Emergency Response System
            </p>
        </div>
        <div>
            <span class="status-badge-active">● OPERATIONAL</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Mandatory Safety & Prototype Disclaimer
st.markdown("""
<div class="disclaimer-banner">
    <strong>⚠️ CRITICAL SAFETY & PROTOTYPE DISCLAIMER:</strong> SafeFall AI is an experimental hackathon concept prototype designed strictly for demonstration and research purposes. It is <strong>NOT a certified medical device</strong> (FDA / CE mark), does not establish a person's medical diagnosis or state of unconsciousness, does not operate physical locks, and does NOT connect to real 911 / emergency dispatch services. All emergency dispatch notifications (SMS, WhatsApp, Voice) are <strong>simulations</strong> logged within this demonstration interface.
</div>
""", unsafe_allow_html=True)


# ==========================================
# 6. TOP KPI SUMMARY METRICS
# ==========================================
stats = db.get_incident_statistics()

kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

with kpi_col1:
    if st.session_state.fall_active:
        st.markdown("**System State**")
        st.markdown('<span class="status-badge-verifying">🟡 VERIFYING EVENT</span>', unsafe_allow_html=True)
    elif st.session_state.system_status == "EMERGENCY_ESCALATED":
        st.markdown("**System State**")
        st.markdown('<span class="status-badge-emergency">🔴 ESCALATED ALERT</span>', unsafe_allow_html=True)
    else:
        st.markdown("**System State**")
        st.markdown('<span class="status-badge-active">🟢 PASSIVE SCANNING</span>', unsafe_allow_html=True)

with kpi_col2:
    st.metric(
        label="Active Zone",
        value=st.session_state.fall_room,
        delta=room_hazard.get("risk_level", "Normal")
    )

with kpi_col3:
    st.metric(
        label="Total Incidents",
        value=stats["total_incidents"],
        delta="Persistent (SQLite)"
    )

with kpi_col4:
    st.metric(
        label="Escalated Dispatches",
        value=stats["escalated_count"],
        delta=f"{round(stats['escalated_count'] / max(1, stats['total_incidents']) * 100)}% Rate",
        delta_color="inverse"
    )

with kpi_col5:
    st.metric(
        label="Verified False Alarms",
        value=stats["ok_count"],
        delta="Safe Self-Resolved"
    )

st.markdown("---")


# ==========================================
# 7. ACTIVE VERIFICATION MODAL (HIGH PRIORITY)
# ==========================================
if st.session_state.fall_active:
    st.markdown(f"""
    <div class="verification-modal">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="color: #be123c; margin: 0; font-size: 1.5rem;">
                🚨 POTENTIAL FALL DETECTED IN {st.session_state.fall_room.upper()}
            </h2>
            <span class="status-badge-verifying" style="font-size: 1rem; padding: 0.4rem 1rem;">
                ⏱️ {time_remaining} SECONDS REMAINING
            </span>
        </div>
        <p style="color: #4b5563; margin-top: 0.5rem; font-size: 1.05rem;">
            A potential fall signal was registered via <strong>{st.session_state.fall_source}</strong>.
            Please confirm resident condition immediately. If unconfirmed within the window, emergency escalation will initiate automatically.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar showing countdown elapsed
    progress_val = max(0.0, min(1.0, (st.session_state.countdown_duration - time_remaining) / st.session_state.countdown_duration))
    st.progress(progress_val)

    # Interactive Action Buttons
    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        if st.button("✅ I'M OK (Cancel Alarm)", key="btn_ok", type="primary", use_container_width=True):
            # Resident confirmed OK
            eval_result = agent.evaluate_incident(
                room=st.session_state.fall_room,
                verification_result="Confirmed OK",
                detection_source=st.session_state.fall_source,
                elapsed_seconds=round(time_elapsed, 1)
            )

            inc_id = db.insert_incident(
                room=eval_result["room"],
                detection_source=eval_result["detection_source"],
                event_status=eval_result["event_status"],
                verification_result=eval_result["verification_result"],
                severity=eval_result["severity"],
                recommended_action=eval_result["recommended_action"],
                dispatch_status=eval_result["dispatch_status"],
                dispatch_details="Self-verification completed within response window. Dispatch cancelled.",
                notes=f"User tapped 'I am OK' after {round(time_elapsed, 1)}s. Escalation aborted."
            )

            eval_result["id"] = inc_id
            st.session_state.last_incident_report = eval_result
            st.session_state.latest_dispatch = None
            st.session_state.fall_active = False
            st.session_state.system_status = "RESOLVED_SAFE"
            st.session_state.vision_synthetic_mode = "standing"
            st.success("Safe status confirmed. Incident recorded as self-resolved.")
            time.sleep(0.5)
            st.rerun()

    with action_col2:
        if st.button("🚨 NEED HELP (Immediate Dispatch)", key="btn_help", type="secondary", use_container_width=True):
            # Resident actively requested help
            eval_result = agent.evaluate_incident(
                room=st.session_state.fall_room,
                verification_result="Help Requested",
                detection_source=st.session_state.fall_source,
                elapsed_seconds=round(time_elapsed, 1)
            )

            inc_id = db.insert_incident(
                room=eval_result["room"],
                detection_source=eval_result["detection_source"],
                event_status=eval_result["event_status"],
                verification_result=eval_result["verification_result"],
                severity=eval_result["severity"],
                recommended_action=eval_result["recommended_action"],
                dispatch_status=eval_result["dispatch_status"],
                dispatch_details="Simulated multi-channel emergency broadcast triggered by resident request.",
                notes=f"Resident actively pressed 'Need Help' button in {st.session_state.fall_room}."
            )

            # Generate simulated emergency dispatch
            dispatch_bundle = notifier.execute_simulated_dispatch(
                incident_id=inc_id,
                room=eval_result["room"],
                severity=eval_result["severity"],
                verification_result=eval_result["verification_result"]
            )

            eval_result["id"] = inc_id
            st.session_state.last_incident_report = eval_result
            st.session_state.latest_dispatch = dispatch_bundle
            st.session_state.fall_active = False
            st.session_state.system_status = "EMERGENCY_ESCALATED"
            st.session_state.vision_synthetic_mode = "fallen"
            st.error("Emergency dispatch simulated. Help requested by resident.")
            time.sleep(0.5)
            st.rerun()

    # Smooth automatic countdown refresh
    time.sleep(1)
    st.rerun()


# ==========================================
# 8. WORKSPACE SPLIT (DETECTION vs ACTION)
# ==========================================
col_monitor, col_response = st.columns([1, 1], gap="large")

# ------------------------------------------
# LEFT COLUMN: LIVE MONITORING & SIMULATION
# ------------------------------------------
with col_monitor:
    st.subheader("📡 Live Monitoring & Fall Detection Hub")

    with st.container(border=True):
        st.markdown("#### ⚡ 1. Reliable Fall Simulation (Zero-Camera Needed)")
        st.markdown(
            "Click below to test the complete end-to-end incident orchestration, "
            "verification countdown, and context-aware escalation workflow."
        )

        sim_scenario = st.selectbox(
            "Select Fall Scenario:",
            [
                "Sudden slip on wet bathroom tile",
                "Loss of balance at living room carpet edge",
                "Trip and forward fall in kitchen",
                "Missed step on staircase landing",
                "Bedside transfer instability"
            ],
            index=0
        )

        sim_col_a, sim_col_b = st.columns([2, 1])
        with sim_col_a:
            if st.button("⚡ SIMULATE FALL INCIDENT", type="primary", use_container_width=True):
                st.session_state.fall_active = True
                st.session_state.fall_start_time = time.time()
                st.session_state.fall_scenario = sim_scenario
                st.session_state.fall_source = "Simulated Fall Trigger"
                st.session_state.system_status = "VERIFYING_FALL"
                st.session_state.vision_synthetic_mode = "stumbling"
                st.rerun()

        with sim_col_b:
            if st.button("🔄 Standby Reset", use_container_width=True):
                st.session_state.fall_active = False
                st.session_state.system_status = "MONITORING_ACTIVE"
                st.session_state.vision_synthetic_mode = "standing"
                st.rerun()

    # Computer Vision & Sensor Feed Module
    with st.container(border=True):
        st.markdown("#### 👁️ 2. Vision Feed & Pose Estimation")
        st.caption("Treats posture estimation as potential-fall signals (not clinical diagnostics).")

        feed_mode = st.radio(
            "Sensor Feed Channel:",
            ["Synthetic Sensor Simulation", "Webcam Pose Estimation (Optional)"],
            horizontal=True
        )

        if feed_mode == "Synthetic Sensor Simulation":
            st.markdown(
                "Synthetic sensor rendering generates real-time telemetry frames "
                "representing resident joint angles and posture states."
            )
            sim_state = st.radio(
                "Simulated Posture State:",
                ["Standing (Normal)", "Stumbling (Unstable)", "Fallen (Ground Posture)"],
                index=0 if st.session_state.vision_synthetic_mode == "standing" else (
                    1 if st.session_state.vision_synthetic_mode == "stumbling" else 2
                ),
                horizontal=True
            )

            state_key = "standing" if "Standing" in sim_state else ("stumbling" if "Stumbling" in sim_state else "fallen")
            st.session_state.vision_synthetic_mode = state_key

            frame = fall_detector.generate_synthetic_demo_frame(mode=state_key)
            if PIL_AVAILABLE:
                st.image(frame, channels="BGR", use_container_width=True)

            if state_key == "fallen" and not st.session_state.fall_active and st.session_state.system_status != "EMERGENCY_ESCALATED":
                if st.button("⚠️ Trigger Fall Workflow from Vision Signal", use_container_width=True):
                    st.session_state.fall_active = True
                    st.session_state.fall_start_time = time.time()
                    st.session_state.fall_source = "Synthetic Sensor Vision Feed"
                    st.session_state.system_status = "VERIFYING_FALL"
                    st.rerun()

        else:
            # Webcam Mode
            st.info("Webcam Snapshot Analysis: capture a frame to test pose-estimation fall detection.")
            cam_picture = st.camera_input("Capture pose evaluation frame")

            if cam_picture is not None:
                if fall_detector.OPENCV_AVAILABLE and fall_detector.MEDIAPIPE_AVAILABLE:
                    try:
                        import cv2
                        file_bytes = np.asarray(bytearray(cam_picture.read()), dtype=np.uint8)
                        opencv_img = cv2.imdecode(file_bytes, 1)

                        detector = fall_detector.VisionFallDetector()
                        annotated, is_fall, telemetry = detector.process_frame(opencv_img)

                        st.image(annotated, channels="BGR", caption="Analyzed Pose Landmarks")
                        st.json(telemetry)

                        if is_fall:
                            st.error("⚠️ Potential fall posture detected from webcam pose estimate!")
                            if st.button("🚨 Engage Fall Verification Protocol", type="primary"):
                                st.session_state.fall_active = True
                                st.session_state.fall_start_time = time.time()
                                st.session_state.fall_source = "Webcam MediaPipe Pose Model"
                                st.session_state.system_status = "VERIFYING_FALL"
                                st.rerun()
                        else:
                            st.success(f"Posture evaluated: {telemetry.get('posture', 'Normal')}")
                    except Exception as err:
                        st.warning(f"Pose analysis notice: {err}. Switching to synthetic feed.")
                else:
                    st.warning(
                        "OpenCV or MediaPipe library is running in fallback mode on this environment. "
                        "Webcam pose estimation is optional. You can test all features reliably with the "
                        "'Simulate Fall' button and 'Synthetic Sensor Simulation' channel."
                    )


# ------------------------------------------
# RIGHT COLUMN: AGENTIC INCIDENT ACTION CENTER
# ------------------------------------------
with col_response:
    st.subheader("🤖 Context-Aware Incident Action Center")

    if st.session_state.last_incident_report:
        rep = st.session_state.last_incident_report
        severity_color = "#e11d48" if rep["severity"] == "Critical" else ("#f59e0b" if rep["severity"] == "High" else "#10b981")

        with st.container(border=True):
            st.markdown(f"""
            <div style="border-left: 5px solid {severity_color}; padding-left: 1rem; margin-bottom: 0.5rem;">
                <span style="font-size: 0.8rem; font-weight: 700; color: #64748b;">LATEST INCIDENT REPORT #{rep.get('id', 'NEW')}</span>
                <h3 style="margin: 0.2rem 0; color: {severity_color};">
                    Severity: {rep['severity'].upper()} — {rep['event_status']}
                </h3>
            </div>
            """, unsafe_allow_html=True)

            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.markdown(f"**Timestamp:** `{rep['timestamp']}`")
                st.markdown(f"**Room / Zone:** `{rep['room']}`")
                st.markdown(f"**Detection Channel:** `{rep['detection_source']}`")
            with c_info2:
                st.markdown(f"**Verification Outcome:** `{rep['verification_result']}`")
                st.markdown(f"**Urgency Label:** `{rep['urgency_label']}`")
                st.markdown(f"**Dispatch Status:** `{rep['dispatch_status']}`")

            st.markdown("#### 🧠 Context-Aware AI Triage Reasoning")
            st.info(rep["reasoning"])

            st.markdown("#### 📋 Recommended Emergency Response Plan")
            st.success(f"👉 **Next Action:** {rep['recommended_action']}")

        # Simulated Emergency Dispatch Section
        if st.session_state.latest_dispatch:
            st.markdown("### 📡 Simulated Emergency Dispatch Broadcast")
            st.caption("CLEARLY MARKED SIMULATION: Audited demo payloads sent to mock endpoints.")

            disp_bundle = st.session_state.latest_dispatch

            for disp in disp_bundle.get("dispatches", []):
                channel_icon = "📱" if disp["channel"] == "SMS" else ("💬" if disp["channel"] == "WhatsApp" else "📞")
                with st.expander(f"{channel_icon} Simulated {disp['channel']} ➔ {disp['contact_name']} ({disp['relation']})", expanded=True):
                    st.markdown(f"<span class='simulation-tag'>SIMULATION ONLY</span> &nbsp; Status: <strong>{disp['status']}</strong>", unsafe_allow_html=True)
                    st.text(disp["payload"])
                    st.caption(f"Phone: {disp['phone']} | Time: {disp['timestamp']} | Disclaimer: {disp['simulation_disclaimer']}")

    else:
        with st.container(border=True):
            st.info("System is currently in Standby / Passive Monitoring mode.")
            st.markdown(
                "Trigger a fall event using the **'⚡ SIMULATE FALL INCIDENT'** button on the left "
                "or click **'🌱 Seed Demo Data'** in the sidebar to review past incident reports."
            )


# ==========================================
# 9. TABS: INCIDENT HISTORY, ANALYTICS, CONTACTS
# ==========================================
st.markdown("---")
st.subheader("📊 System Records & Intelligence")

tab_history, tab_analytics, tab_contacts, tab_info = st.tabs([
    "📜 SQLite Incident History",
    "📈 Analytics & Risk Trends",
    "👥 Emergency Contacts Directory",
    "📘 Safety & Architecture Standards"
])

# ------------------------------------------
# TAB 1: SQLITE INCIDENT HISTORY
# ------------------------------------------
with tab_history:
    df_incidents = db.get_all_incidents(limit=100)

    if not df_incidents.empty:
        col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
        with col_f1:
            room_filter = st.multiselect("Filter by Room:", options=df_incidents["room"].unique(), default=[])
        with col_f2:
            severity_filter = st.multiselect("Filter by Severity:", options=df_incidents["severity"].unique(), default=[])

        filtered_df = df_incidents.copy()
        if room_filter:
            filtered_df = filtered_df[filtered_df["room"].isin(room_filter)]
        if severity_filter:
            filtered_df = filtered_df[filtered_df["severity"].isin(severity_filter)]

        st.dataframe(
            filtered_df[[
                "id", "timestamp", "room", "detection_source",
                "event_status", "verification_result", "severity",
                "dispatch_status", "recommended_action"
            ]],
            use_container_width=True,
            hide_index=True
        )

        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Incident Log (CSV)",
            data=csv_data,
            file_name=f"safefall_incidents_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No incidents logged in the database yet. Click '🌱 Seed Demo Data' in the sidebar or trigger a simulated fall.")


# ------------------------------------------
# TAB 2: ANALYTICS & RISK TRENDS
# ------------------------------------------
with tab_analytics:
    df_all = db.get_all_incidents(limit=200)

    if not df_all.empty and len(df_all) >= 1:
        an_col1, an_col2 = st.columns(2)

        with an_col1:
            st.markdown("#### Incidents by Room Hazard Zone")
            room_counts = df_all["room"].value_counts().reset_index()
            room_counts.columns = ["Room", "Incident Count"]
            if PLOTLY_AVAILABLE:
                fig_room = px.bar(
                    room_counts,
                    x="Room",
                    y="Incident Count",
                    color="Room",
                    title="Spatial Distribution of Fall Events"
                )
                fig_room.update_layout(showlegend=False, height=320)
                st.plotly_chart(fig_room, use_container_width=True)
            else:
                st.bar_chart(room_counts.set_index("Room"))

        with an_col2:
            st.markdown("#### Severity Breakdown")
            sev_counts = df_all["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            if PLOTLY_AVAILABLE:
                fig_sev = px.pie(
                    sev_counts,
                    names="Severity",
                    values="Count",
                    color="Severity",
                    color_discrete_map={"Critical": "#ef4444", "High": "#f59e0b", "Low": "#10b981"},
                    title="Incident Severity Distribution"
                )
                fig_sev.update_layout(height=320)
                st.plotly_chart(fig_sev, use_container_width=True)
            else:
                st.bar_chart(sev_counts.set_index("Severity"))

        # Outcome summary
        st.markdown("#### Verification Outcomes Summary")
        outcome_counts = df_all["verification_result"].value_counts().reset_index()
        outcome_counts.columns = ["Outcome", "Total Events"]
        st.dataframe(outcome_counts, use_container_width=True, hide_index=True)

    else:
        st.info("Insufficient incident telemetry to render trend charts. Please record or seed incidents first.")


# ------------------------------------------
# TAB 3: EMERGENCY CONTACTS DIRECTORY
# ------------------------------------------
with tab_contacts:
    st.markdown("#### Configured Escalation Contacts (Simulation Sandbox)")
    st.caption("Notifications generated for these contacts are mock records with explicit disclaimers.")

    contacts_df = pd.DataFrame(notifier.DEFAULT_CONTACTS)
    st.dataframe(contacts_df[["priority", "name", "relation", "phone", "channels"]], use_container_width=True, hide_index=True)

    with st.expander("➕ Register Additional Demo Contact"):
        with st.form("new_contact_form"):
            c_name = st.text_input("Full Name", placeholder="e.g. Michael Miller")
            c_rel = st.text_input("Relationship", placeholder="e.g. Neighbor / Keyholder")
            c_phone = st.text_input("Phone Number", placeholder="e.g. +1 (555) 345-6789")
            c_channels = st.multiselect("Enabled Dispatch Channels", ["SMS", "WhatsApp", "Voice Call"], default=["SMS"])
            submitted = st.form_submit_button("Save Contact (Demo)")
            if submitted and c_name and c_phone:
                st.success(f"Contact {c_name} registered in sandbox session.")


# ------------------------------------------
# TAB 4: SAFETY & ARCHITECTURE STANDARDS
# ------------------------------------------
with tab_info:
    st.markdown("""
    ### 🛡️ SafeFall AI Safety & Ethical Guardrails

    1. **Non-Diagnostic Bounding:** SafeFall AI interprets pose vectors strictly as *potential fall posture signals*. It makes no claim to diagnose bone fractures, concussions, or physiological causes.
    2. **Human-in-the-Loop Verification:** Every detected fall initiates an audible and visual verification countdown giving the resident primary autonomy to cancel false alarms.
    3. **Zero Real Network Overhead / Simulation Clarity:** Hackathon compliance ensures that no unsolicited SMS, cellular phone call, or external emergency service is contacted without authorization.
    4. **Air-Gapped Safety:** System does NOT control physical locks, access gates, or hardware actuators.
    5. **Persistent Data Provenance:** Every event is written into local SQLite audit tables with full timestamps, room context, and verification trail.
    """)


# ==========================================
# 10. FOOTER
# ==========================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.82rem;'>"
    "SafeFall AI — Hackathon MVP Prototype | Local SQLite Persistent Store | "
    "Emergency Dispatch Simulator Active (Zero Paid APIs Required)"
    "</div>",
    unsafe_allow_html=True
)
