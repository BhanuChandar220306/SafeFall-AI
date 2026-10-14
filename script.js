/**
 * SafeFall AI — Autonomous Emergency Monitoring & Incident Triage Engine
 * Zero-Backend Browser Application for Vercel Static Deployment
 */

// =====================================================================
// 1. CONSTANTS & CONFIGURATION
// =====================================================================
const STORAGE_KEY = 'safefall_incidents_v1';
const CONTACTS_KEY = 'safefall_contacts_v1';

const ROOM_HAZARDS = {
  "Bathroom": {
    level: "High Risk Zone",
    hazards: "Hard tile surfaces, high moisture/slip probability, confined space",
    urgencyBoost: true,
    class: "danger",
    icon: "⚠️"
  },
  "Staircase": {
    level: "Critical Risk Zone",
    hazards: "High kinetic impact hazard, potential head trauma risk",
    urgencyBoost: true,
    class: "danger",
    icon: "🚨"
  },
  "Kitchen": {
    level: "Medium Risk Zone",
    hazards: "Hard flooring, appliances, potential spill hazards",
    urgencyBoost: false,
    class: "warning",
    icon: "⚠️"
  },
  "Bedroom": {
    level: "Moderate Risk Zone",
    hazards: "Bed-height transfer hazard, low nighttime lighting",
    urgencyBoost: false,
    class: "info",
    icon: "ℹ️"
  },
  "Living Room": {
    level: "Low/Moderate Risk Zone",
    hazards: "Area rugs, coffee tables, standard residential layout",
    urgencyBoost: false,
    class: "info",
    icon: "ℹ️"
  }
};

const DEFAULT_CONTACTS = [
  {
    priority: 1,
    name: "Sarah Miller",
    relation: "Primary Caregiver (Daughter)",
    phone: "+1 (555) 234-8901",
    channels: "SMS, WhatsApp, Voice Call"
  },
  {
    priority: 2,
    name: "Dr. Robert Chen",
    relation: "Attending Physician / Family Doctor",
    phone: "+1 (555) 782-4412",
    channels: "SMS, WhatsApp"
  },
  {
    priority: 3,
    name: "Building Concierge / Security Desk",
    relation: "On-Site First Responder",
    phone: "+1 (555) 901-3320",
    channels: "Automated Voice, SMS"
  }
];

// =====================================================================
// 2. APPLICATION STATE
// =====================================================================
let appState = {
  fallActive: false,
  countdownInterval: null,
  countdownRemaining: 10,
  countdownTotal: 10,
  fallStartTime: 0,
  activeRoom: "Living Room",
  activeScenario: "Loss of balance at living room carpet edge",
  activeSource: "Simulated Fall Trigger",
  syntheticMode: "standing", // 'standing', 'stumbling', 'fallen'
  webcamStream: null,
  latestIncident: null,
  latestDispatch: null
};

// =====================================================================
// 3. INITIALIZATION & DOM BINDINGS
// =====================================================================
document.addEventListener('DOMContentLoaded', () => {
  initStorage();
  bindUIEvents();
  renderKPIs();
  renderIncidentsTable();
  renderContactsTable();
  drawSyntheticCanvas('standing');
  updateRoomHazardUI();
  renderAnalyticsCharts();
});

function initStorage() {
  if (!localStorage.getItem(STORAGE_KEY)) {
    seedDemoIncidents();
  }
  if (!localStorage.getItem(CONTACTS_KEY)) {
    localStorage.setItem(CONTACTS_KEY, JSON.stringify(DEFAULT_CONTACTS));
  }
}

function bindUIEvents() {
  // Room and Scenario Selectors
  const roomSelect = document.getElementById('select-room');
  if (roomSelect) {
    roomSelect.addEventListener('change', (e) => {
      appState.activeRoom = e.target.value;
      updateRoomHazardUI();
      renderKPIs();
    });
  }

  const scenarioSelect = document.getElementById('select-scenario');
  if (scenarioSelect) {
    scenarioSelect.addEventListener('change', (e) => {
      appState.activeScenario = e.target.value;
    });
  }

  // Simulation Trigger & Standby Reset
  document.getElementById('btn-simulate-fall').addEventListener('click', () => {
    triggerFallWorkflow("Simulated Fall Trigger");
  });

  document.getElementById('btn-standby-reset').addEventListener('click', () => {
    resetStandby();
  });

  // Verification Buttons
  document.getElementById('btn-im-ok').addEventListener('click', () => {
    handleVerificationChoice("Confirmed OK");
  });

  document.getElementById('btn-need-help').addEventListener('click', () => {
    handleVerificationChoice("Help Requested");
  });

  // Sensor Segmented Control (Synthetic vs Webcam)
  document.getElementById('tab-sensor-synthetic').addEventListener('click', () => {
    switchSensorTab('synthetic');
  });

  document.getElementById('tab-sensor-webcam').addEventListener('click', () => {
    switchSensorTab('webcam');
  });

  // Synthetic Posture Buttons
  document.getElementById('pose-btn-standing').addEventListener('click', () => {
    setSyntheticPose('standing');
  });
  document.getElementById('pose-btn-stumbling').addEventListener('click', () => {
    setSyntheticPose('stumbling');
  });
  document.getElementById('pose-btn-fallen').addEventListener('click', () => {
    setSyntheticPose('fallen');
  });

  document.getElementById('btn-trigger-vision-fall').addEventListener('click', () => {
    setSyntheticPose('fallen');
    triggerFallWorkflow("Synthetic Sensor Vision Feed");
  });

  // Webcam Controls
  document.getElementById('btn-start-webcam').addEventListener('click', startWebcam);
  document.getElementById('btn-stop-webcam').addEventListener('click', stopWebcam);

  // Tab Navigation
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tabId = e.currentTarget.getAttribute('data-tab');
      switchMainTab(tabId, e.currentTarget);
    });
  });

  // History Actions
  document.getElementById('filter-room').addEventListener('change', renderIncidentsTable);
  document.getElementById('filter-severity').addEventListener('change', renderIncidentsTable);
  document.getElementById('btn-export-csv').addEventListener('click', exportIncidentsCSV);
  document.getElementById('btn-seed-data').addEventListener('click', () => {
    seedDemoIncidents();
    renderKPIs();
    renderIncidentsTable();
    renderAnalyticsCharts();
    alert('🌱 Demo incidents loaded successfully into localStorage.');
  });
  document.getElementById('btn-clear-data').addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all incident records?')) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
      appState.latestIncident = null;
      appState.latestDispatch = null;
      resetStandby();
      renderKPIs();
      renderIncidentsTable();
      renderAnalyticsCharts();
    }
  });

  // Add Contact Form
  const addContactForm = document.getElementById('add-contact-form');
  if (addContactForm) {
    addContactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('new-contact-name').value.trim();
      const relation = document.getElementById('new-contact-relation').value.trim();
      const phone = document.getElementById('new-contact-phone').value.trim();
      if (name && phone) {
        addDemoContact(name, relation, phone);
        addContactForm.reset();
      }
    });
  }
}

// =====================================================================
// 4. VERIFICATION WORKFLOW & COUNTDOWN ENGINE
// =====================================================================
function triggerFallWorkflow(source = "Simulated Fall Trigger") {
  if (appState.fallActive) return;

  const durationInput = document.getElementById('input-countdown');
  const duration = durationInput ? Math.max(5, Math.min(30, parseInt(durationInput.value) || 10)) : 10;

  appState.fallActive = true;
  appState.activeSource = source;
  appState.countdownTotal = duration;
  appState.countdownRemaining = duration;
  appState.fallStartTime = Date.now();

  // Update System Status
  setSystemStatusBadge("VERIFYING EVENT", "status-verifying");
  document.getElementById('kpi-system-state').innerHTML = '🟡 VERIFYING EVENT';
  document.getElementById('kpi-system-state').className = 'badge badge-warning';

  // Show Verification Panel
  const verPanel = document.getElementById('verification-panel');
  verPanel.classList.remove('hidden');
  document.getElementById('verification-title').textContent = `🚨 POTENTIAL FALL DETECTED IN ${appState.activeRoom.toUpperCase()}`;
  document.getElementById('verification-desc').innerHTML = 
    `A potential fall signal was registered via <strong>${source}</strong> in ${appState.activeRoom}. Please confirm resident condition immediately.`;

  updateCountdownUI();

  // Clear any existing countdown
  if (appState.countdownInterval) {
    clearInterval(appState.countdownInterval);
  }

  // Start Interval
  appState.countdownInterval = setInterval(() => {
    const elapsed = (Date.now() - appState.fallStartTime) / 1000;
    appState.countdownRemaining = Math.max(0, Math.ceil(appState.countdownTotal - elapsed));

    updateCountdownUI();

    if (appState.countdownRemaining <= 0) {
      clearInterval(appState.countdownInterval);
      appState.countdownInterval = null;
      handleVerificationChoice("No Response (Timeout)");
    }
  }, 250);
}

function updateCountdownUI() {
  const timerText = document.getElementById('countdown-timer-text');
  const progressBar = document.getElementById('countdown-progress-bar');
  if (timerText) {
    timerText.textContent = `${appState.countdownRemaining}s REMAINING`;
  }
  if (progressBar) {
    const progressPercent = (appState.countdownRemaining / appState.countdownTotal) * 100;
    progressBar.style.width = `${progressPercent}%`;
  }
}

function handleVerificationChoice(choice) {
  if (appState.countdownInterval) {
    clearInterval(appState.countdownInterval);
    appState.countdownInterval = null;
  }
  appState.fallActive = false;

  // Hide verification panel
  document.getElementById('verification-panel').classList.add('hidden');

  // Compute elapsed time
  const elapsedSec = ((Date.now() - appState.fallStartTime) / 1000).toFixed(1);

  // Evaluate incident via Agentic Triage Logic
  const incidentReport = evaluateIncidentTriage(
    appState.activeRoom,
    choice,
    appState.activeSource,
    elapsedSec
  );

  // Save to LocalStorage
  const savedIncident = saveIncident(incidentReport);
  appState.latestIncident = savedIncident;

  // If escalated, generate simulated emergency dispatch
  if (choice !== "Confirmed OK") {
    appState.latestDispatch = generateSimulatedDispatch(savedIncident);
    setSystemStatusBadge("ESCALATED ALERT", "status-escalated");
    document.getElementById('kpi-system-state').innerHTML = '🔴 ESCALATED ALERT';
    document.getElementById('kpi-system-state').className = 'badge badge-danger';
  } else {
    appState.latestDispatch = null;
    setSystemStatusBadge("OPERATIONAL", "status-active");
    document.getElementById('kpi-system-state').innerHTML = '🟢 PASSIVE SCANNING';
    document.getElementById('kpi-system-state').className = 'badge badge-success';
  }

  // Render UI updates
  renderIncidentActionCenter(savedIncident, appState.latestDispatch);
  renderKPIs();
  renderIncidentsTable();
  renderAnalyticsCharts();
}

function resetStandby() {
  if (appState.countdownInterval) {
    clearInterval(appState.countdownInterval);
    appState.countdownInterval = null;
  }
  appState.fallActive = false;
  document.getElementById('verification-panel').classList.add('hidden');
  setSystemStatusBadge("OPERATIONAL", "status-active");
  document.getElementById('kpi-system-state').innerHTML = '🟢 PASSIVE SCANNING';
  document.getElementById('kpi-system-state').className = 'badge badge-success';
  setSyntheticPose('standing');
}

// =====================================================================
// 5. AGENTIC CONTEXT-AWARE TRIAGE ENGINE
// =====================================================================
function evaluateIncidentTriage(room, verificationResult, detectionSource, elapsedSeconds) {
  const roomInfo = ROOM_HAZARDS[room] || {
    level: "General Domestic Zone",
    hazards: "Standard residential layout",
    urgencyBoost: false
  };

  const timestamp = formatDateTime(new Date());
  let severity = "Low";
  let eventStatus = "Resolved - False Alarm";
  let urgencyLabel = "Green (Safe / Self-Resolved)";
  let dispatchStatus = "CANCELLED (User Verified OK)";
  let reasoning = "";
  let recommendedAction = "";

  if (verificationResult === "Confirmed OK") {
    severity = "Low";
    eventStatus = "Resolved - False Alarm";
    urgencyLabel = "Green (Safe / Self-Resolved)";
    dispatchStatus = "CANCELLED (User Verified OK)";
    reasoning = `Resident actively acknowledged safety check within ${elapsedSeconds}s. No physical assistance requested. Zone: ${room} (${roomInfo.level}).`;
    recommendedAction = "Log self-verified safe status. Maintain standard passive monitoring. No caregiver dispatch required.";
  } else if (verificationResult === "Help Requested") {
    severity = roomInfo.urgencyBoost ? "Critical" : "High";
    eventStatus = "Escalated - Help Requested";
    urgencyLabel = "Red (Active Assistance Required)";
    dispatchStatus = "SIMULATED DISPATCH SENT";
    reasoning = `Resident actively triggered the NEED HELP action in ${room} (${roomInfo.level}). Environmental factor note: ${roomInfo.hazards}.`;
    recommendedAction = "Dispatch primary caregiver immediately via Simulated SMS & WhatsApp. Activate 2-way room speakerphone/intercom. Check in with resident.";
  } else {
    // No Response (Timeout)
    severity = "Critical";
    eventStatus = "Escalated - Timeout / Unresponsive";
    urgencyLabel = "Flashing Red (Resident Unresponsive)";
    dispatchStatus = "SIMULATED DISPATCH SENT";
    reasoning = `Countdown window expired with ZERO response in ${room}. Resident is potentially immobilized or unable to reach controls. Zone Risk: ${roomInfo.level} - ${roomInfo.hazards}.`;
    recommendedAction = "URGENT: Trigger automated voice dispatch to primary contact and concierge. Sound local smart beacon chime in residence. Prepare building access instructions.";
  }

  return {
    timestamp,
    room,
    detection_source: detectionSource,
    event_status: eventStatus,
    verification_result: verificationResult,
    severity,
    urgency_label: urgencyLabel,
    dispatch_status: dispatchStatus,
    reasoning,
    recommended_action: recommendedAction,
    notes: `Scenario: ${appState.activeScenario}. Response time: ${elapsedSeconds}s.`
  };
}

// =====================================================================
// 6. SIMULATED EMERGENCY DISPATCH ENGINE
// =====================================================================
function generateSimulatedDispatch(incident) {
  const timestamp = incident.timestamp;
  const incId = incident.id;
  const room = incident.room;
  const severity = incident.severity;
  const verification = incident.verification_result;

  const smsText = 
`[SIMULATED SMS - SafeFall AI Alert]
INCIDENT #${incId} | SEVERITY: ${severity.toUpperCase()}
Location: ${room}
Time: ${timestamp}
Status: ${verification}
Action: Primary caregiver requested to check on resident immediately.
(SIMULATION ONLY: Demo notification. No real SMS sent.)`;

  const whatsappText = 
`🚨 *[SIMULATED WHATSAPP EMERGENCY ALERT]*
*SafeFall AI Incident Triage Engine*
━━━━━━━━━━━━━━━━━━
• *Incident ID:* #${incId}
• *Room/Zone:* ${room}
• *Severity Level:* ${severity.toUpperCase()}
• *Verification:* ${verification}
• *Timestamp:* ${timestamp}
• *Location Pin:* Residence Zone 4 (Coordinates: [SIMULATED GPS])
• *Intercom Link:* https://safefall.local/intercom/${incId} (Demo)
━━━━━━━━━━━━━━━━━━
⚠️ *SIMULATION ONLY:* No actual WhatsApp transmission occurred.`;

  const voiceText = 
`[SIMULATED VOICE CALL TRANSCRIPT - TTS ENGINE]
"Urgent alert from SafeFall AI. A potential fall has been detected in ${room}. 
Verification status is: ${verification}. Severity level is evaluated as ${severity}. 
Please press 1 to connect to the residence speakerphone, or press 2 to acknowledge escalation."
[CALL DURATION: 18s | RESULT: Call Answered & Acknowledged (SIMULATED)]`;

  return {
    sms: smsText,
    whatsapp: whatsappText,
    voice: voiceText
  };
}

// =====================================================================
// 7. INCIDENT PERSISTENCE & LOCALSTORAGE
// =====================================================================
function getStoredIncidents() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch (e) {
    return [];
  }
}

function saveIncident(incidentData) {
  const incidents = getStoredIncidents();
  const nextId = incidents.length > 0 ? Math.max(...incidents.map(i => i.id || 0)) + 1 : 1;
  const newIncident = { id: nextId, ...incidentData };
  incidents.unshift(newIncident);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(incidents));
  return newIncident;
}

function seedDemoIncidents() {
  const now = new Date();
  const fmt = (d) => formatDateTime(d);

  const samples = [
    {
      id: 101,
      timestamp: fmt(new Date(now.getTime() - 26 * 3600 * 1000)),
      room: "Living Room",
      detection_source: "Simulated Fall Trigger",
      event_status: "Resolved - False Alarm",
      verification_result: "Confirmed OK",
      severity: "Low",
      urgency_label: "Green (Safe / Self-Resolved)",
      dispatch_status: "CANCELLED (User Verified OK)",
      reasoning: "Resident confirmed safe within 4s response window. Slip on area rug, uninjured.",
      recommended_action: "Log self-verified safe status. Maintain standard passive monitoring.",
      notes: "Slip on rug, resident recovered unassisted."
    },
    {
      id: 102,
      timestamp: fmt(new Date(now.getTime() - 14 * 3600 * 1000)),
      room: "Kitchen",
      detection_source: "Webcam Vision Model",
      event_status: "Escalated - Help Requested",
      verification_result: "Help Requested",
      severity: "High",
      urgency_label: "Red (Active Assistance Required)",
      dispatch_status: "SIMULATED DISPATCH SENT",
      reasoning: "Resident actively pressed Need Help after loss of balance near kitchen counter.",
      recommended_action: "Dispatch primary caregiver (Sarah M.) via Simulated SMS & WhatsApp. Initiate intercom check.",
      notes: "Loss of balance, resident requested assistance."
    },
    {
      id: 103,
      timestamp: fmt(new Date(now.getTime() - 4 * 3600 * 1000)),
      room: "Bathroom",
      detection_source: "Synthetic Sensor Vision Feed",
      event_status: "Escalated - Timeout / Unresponsive",
      verification_result: "No Response (Timeout)",
      severity: "Critical",
      urgency_label: "Flashing Red (Resident Unresponsive)",
      dispatch_status: "SIMULATED DISPATCH SENT",
      reasoning: "Zero response to 10s verification countdown in high-moisture hazard zone.",
      recommended_action: "URGENT: Initiate EMS protocol proxy, alert building concierge, sound audible beacon.",
      notes: "Unresponsive event in bathroom wet zone."
    }
  ];

  localStorage.setItem(STORAGE_KEY, JSON.stringify(samples));
}

// =====================================================================
// 8. UI RENDERING & COMPONENT UPDATES
// =====================================================================
function setSystemStatusBadge(text, className) {
  const pill = document.getElementById('system-status-pill');
  const textEl = document.getElementById('system-status-text');
  if (pill && textEl) {
    pill.className = `status-pill ${className}`;
    textEl.textContent = text;
  }
}

function updateRoomHazardUI() {
  const room = appState.activeRoom;
  const hazard = ROOM_HAZARDS[room] || { level: "Standard", hazards: "Nominal domestic layout", class: "info", icon: "ℹ️" };

  const hazardCard = document.getElementById('room-hazard-card');
  const hazardIcon = document.getElementById('room-hazard-icon');
  const hazardText = document.getElementById('room-hazard-text');

  if (hazardCard && hazardIcon && hazardText) {
    hazardCard.className = `hazard-card ${hazard.class}`;
    hazardIcon.textContent = hazard.icon;
    hazardText.innerHTML = `<strong>${hazard.level}:</strong> ${hazard.hazards}.`;
  }

  const kpiRoom = document.getElementById('kpi-active-room');
  const kpiRisk = document.getElementById('kpi-room-risk');
  if (kpiRoom) kpiRoom.textContent = room;
  if (kpiRisk) kpiRisk.textContent = hazard.level;
}

function renderKPIs() {
  const incidents = getStoredIncidents();
  const total = incidents.length;
  const escalated = incidents.filter(i => i.event_status && i.event_status.includes("Escalated")).length;
  const safe = incidents.filter(i => i.verification_result === "Confirmed OK").length;
  const rate = total > 0 ? Math.round((escalated / total) * 100) : 0;

  const totalEl = document.getElementById('kpi-total-incidents');
  const escEl = document.getElementById('kpi-escalated-count');
  const rateEl = document.getElementById('kpi-escalated-rate');
  const safeEl = document.getElementById('kpi-safe-count');

  if (totalEl) totalEl.textContent = total;
  if (escEl) escEl.textContent = escalated;
  if (rateEl) rateEl.textContent = `${rate}% Escalation Rate`;
  if (safeEl) safeEl.textContent = safe;
}

function renderIncidentActionCenter(incident, dispatch) {
  const emptyState = document.getElementById('incident-report-empty');
  const reportCard = document.getElementById('incident-report-card');
  const dispatchEmpty = document.getElementById('dispatch-empty');
  const dispatchList = document.getElementById('dispatch-list');

  if (!incident) {
    if (emptyState) emptyState.classList.remove('hidden');
    if (reportCard) reportCard.classList.add('hidden');
    if (dispatchEmpty) dispatchEmpty.classList.remove('hidden');
    if (dispatchList) dispatchList.classList.add('hidden');
    return;
  }

  // Populate Report Card
  if (emptyState) emptyState.classList.add('hidden');
  if (reportCard) reportCard.classList.remove('hidden');

  document.getElementById('rep-id-badge').textContent = `INCIDENT #${incident.id}`;
  
  const sevBadge = document.getElementById('rep-severity-badge');
  sevBadge.textContent = incident.severity.toUpperCase();
  sevBadge.className = incident.severity === 'Critical' ? 'badge badge-danger' : 
                       (incident.severity === 'High' ? 'badge badge-warning' : 'badge badge-success');

  document.getElementById('rep-status-title').textContent = incident.event_status;
  document.getElementById('rep-timestamp').textContent = incident.timestamp;
  document.getElementById('rep-room').textContent = incident.room;
  document.getElementById('rep-channel').textContent = incident.detection_source;
  document.getElementById('rep-outcome').textContent = incident.verification_result;
  document.getElementById('rep-reasoning').textContent = incident.reasoning;
  document.getElementById('rep-action').innerHTML = `👉 <strong>Next Action:</strong> ${incident.recommended_action}`;

  // Populate Dispatch Terminal
  if (dispatch) {
    if (dispatchEmpty) dispatchEmpty.classList.add('hidden');
    if (dispatchList) dispatchList.classList.remove('hidden');

    document.getElementById('sms-payload-text').textContent = dispatch.sms;
    document.getElementById('whatsapp-payload-text').textContent = dispatch.whatsapp;
    document.getElementById('voice-payload-text').textContent = dispatch.voice;
  } else {
    if (dispatchEmpty) {
      dispatchEmpty.classList.remove('hidden');
      dispatchEmpty.innerHTML = `<p>Incident was verified safe (False Alarm). Escalation was aborted; no dispatch broadcast required.</p>`;
    }
    if (dispatchList) dispatchList.classList.add('hidden');
  }
}

function renderIncidentsTable() {
  const tableBody = document.getElementById('incidents-table-body');
  if (!tableBody) return;

  const roomFilter = document.getElementById('filter-room')?.value || 'ALL';
  const severityFilter = document.getElementById('filter-severity')?.value || 'ALL';

  let incidents = getStoredIncidents();

  if (roomFilter !== 'ALL') {
    incidents = incidents.filter(i => i.room === roomFilter);
  }
  if (severityFilter !== 'ALL') {
    incidents = incidents.filter(i => i.severity === severityFilter);
  }

  if (incidents.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 2rem;">No incidents match the selected filters.</td></tr>`;
    return;
  }

  tableBody.innerHTML = incidents.map(inc => {
    const sevBadgeClass = inc.severity === 'Critical' ? 'badge badge-danger' : 
                         (inc.severity === 'High' ? 'badge badge-warning' : 'badge badge-success');
    return `
      <tr>
        <td><strong>#${inc.id}</strong></td>
        <td><code>${inc.timestamp}</code></td>
        <td>${inc.room}</td>
        <td>${inc.detection_source}</td>
        <td>${inc.event_status}</td>
        <td>${inc.verification_result}</td>
        <td><span class="${sevBadgeClass}">${inc.severity}</span></td>
        <td><small>${inc.recommended_action}</small></td>
      </tr>
    `;
  }).join('');
}

function renderContactsTable() {
  const tableBody = document.getElementById('contacts-table-body');
  if (!tableBody) return;

  const contacts = JSON.parse(localStorage.getItem(CONTACTS_KEY) || '[]');
  tableBody.innerHTML = contacts.map(c => `
    <tr>
      <td><span class="badge badge-info">Priority ${c.priority}</span></td>
      <td><strong>${c.name}</strong></td>
      <td>${c.relation}</td>
      <td><code>${c.phone}</code></td>
      <td>${c.channels}</td>
    </tr>
  `).join('');
}

function addDemoContact(name, relation, phone) {
  const contacts = JSON.parse(localStorage.getItem(CONTACTS_KEY) || '[]');
  const newPriority = contacts.length + 1;
  contacts.push({
    priority: newPriority,
    name,
    relation,
    phone,
    channels: "SMS, WhatsApp (Simulated)"
  });
  localStorage.setItem(CONTACTS_KEY, JSON.stringify(contacts));
  renderContactsTable();
  alert(`✅ Registered simulated contact "${name}" in sandbox.`);
}

function exportIncidentsCSV() {
  const incidents = getStoredIncidents();
  if (incidents.length === 0) {
    alert("No incidents to export.");
    return;
  }

  const headers = ["ID", "Timestamp", "Room", "Detection Source", "Event Status", "Verification Result", "Severity", "Recommended Action", "Notes"];
  const rows = incidents.map(i => [
    i.id,
    `"${i.timestamp}"`,
    `"${i.room}"`,
    `"${i.detection_source}"`,
    `"${i.event_status}"`,
    `"${i.verification_result}"`,
    `"${i.severity}"`,
    `"${(i.recommended_action || '').replace(/"/g, '""')}"`,
    `"${(i.notes || '').replace(/"/g, '""')}"`
  ]);

  const csvContent = "data:text/csv;charset=utf-8," + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `safefall_incidents_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// =====================================================================
// 9. SYNTHETIC SENSOR CANVAS DRAWING
// =====================================================================
function switchSensorTab(tabName) {
  const syntheticBtn = document.getElementById('tab-sensor-synthetic');
  const webcamBtn = document.getElementById('tab-sensor-webcam');
  const syntheticView = document.getElementById('synthetic-view');
  const webcamView = document.getElementById('webcam-view');

  if (tabName === 'synthetic') {
    syntheticBtn.classList.add('active');
    webcamBtn.classList.remove('active');
    syntheticView.classList.remove('hidden');
    webcamView.classList.add('hidden');
  } else {
    webcamBtn.classList.add('active');
    syntheticBtn.classList.remove('active');
    webcamView.classList.remove('hidden');
    syntheticView.classList.add('hidden');
  }
}

function setSyntheticPose(mode) {
  appState.syntheticMode = mode;
  document.querySelectorAll('.posture-selector-bar .btn-sm').forEach(btn => btn.classList.remove('active'));
  if (mode === 'standing') document.getElementById('pose-btn-standing').classList.add('active');
  if (mode === 'stumbling') document.getElementById('pose-btn-stumbling').classList.add('active');
  if (mode === 'fallen') document.getElementById('pose-btn-fallen').classList.add('active');
  drawSyntheticCanvas(mode);
}

function drawSyntheticCanvas(mode = 'standing') {
  const canvas = document.getElementById('synthetic-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  // Background room fill
  ctx.fillStyle = '#111827';
  ctx.fillRect(0, 0, w, h);

  // Floor grid
  const floorY = h * 0.72;
  ctx.fillStyle = '#1e293b';
  ctx.fillRect(0, floorY, w, h - floorY);

  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(0, floorY);
  ctx.lineTo(w, floorY);
  ctx.stroke();

  // Perspective wall lines
  ctx.beginPath();
  ctx.moveTo(0, h * 0.2);
  ctx.lineTo(w * 0.25, floorY);
  ctx.moveTo(w, h * 0.2);
  ctx.lineTo(w * 0.75, floorY);
  ctx.stroke();

  const cx = w / 2;

  if (mode === 'standing') {
    const headY = floorY - 140;
    const shoulderY = floorY - 110;
    const hipY = floorY - 60;

    // Green stick figure
    ctx.strokeStyle = '#10b981';
    ctx.fillStyle = '#10b981';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';

    // Head
    ctx.beginPath();
    ctx.arc(cx, headY, 14, 0, Math.PI * 2);
    ctx.fill();

    // Torso
    ctx.beginPath();
    ctx.moveTo(cx, headY + 14);
    ctx.lineTo(cx, hipY);
    ctx.stroke();

    // Arms
    ctx.beginPath();
    ctx.moveTo(cx - 24, shoulderY + 25);
    ctx.lineTo(cx, shoulderY);
    ctx.lineTo(cx + 24, shoulderY + 25);
    ctx.stroke();

    // Legs
    ctx.beginPath();
    ctx.moveTo(cx - 18, floorY);
    ctx.lineTo(cx, hipY);
    ctx.lineTo(cx + 18, floorY);
    ctx.stroke();

    // Telemetry HUD
    drawCanvasHUD(ctx, "NORMAL MONITORING", "#10b981", "Spine Angle: 88.5° | Posture: Upright / Stable", w, h);

  } else if (mode === 'stumbling') {
    const headX = cx + 35;
    const headY = floorY - 115;
    const shoulderX = cx + 18;
    const shoulderY = floorY - 85;
    const hipX = cx - 10;
    const hipY = floorY - 45;

    // Amber stick figure
    ctx.strokeStyle = '#f59e0b';
    ctx.fillStyle = '#f59e0b';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';

    // Head
    ctx.beginPath();
    ctx.arc(headX, headY, 14, 0, Math.PI * 2);
    ctx.fill();

    // Torso
    ctx.beginPath();
    ctx.moveTo(headX, headY + 14);
    ctx.lineTo(hipX, hipY);
    ctx.stroke();

    // Flailing arms
    ctx.beginPath();
    ctx.moveTo(shoulderX - 35, shoulderY - 15);
    ctx.lineTo(shoulderX, shoulderY);
    ctx.lineTo(shoulderX + 45, shoulderY - 10);
    ctx.stroke();

    // Legs
    ctx.beginPath();
    ctx.moveTo(cx - 40, floorY);
    ctx.lineTo(hipX, hipY);
    ctx.lineTo(cx + 25, floorY);
    ctx.stroke();

    drawCanvasHUD(ctx, "UNSTABLE MOTION DETECTED", "#f59e0b", "Spine Angle: 44.8° | Posture: Rapid Trajectory Tilt", w, h);

  } else {
    // Fallen figure (lying down)
    const headX = cx - 100;
    const headY = floorY + 28;
    const shoulderX = cx - 50;
    const hipX = cx + 30;
    const kneeX = cx + 90;
    const footX = cx + 140;
    const lineY = floorY + 34;

    // Red stick figure
    ctx.strokeStyle = '#e11d48';
    ctx.fillStyle = '#e11d48';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';

    // Head
    ctx.beginPath();
    ctx.arc(headX, headY, 14, 0, Math.PI * 2);
    ctx.fill();

    // Torso & legs horizontal
    ctx.beginPath();
    ctx.moveTo(headX + 14, lineY);
    ctx.lineTo(shoulderX, lineY);
    ctx.lineTo(hipX, lineY);
    ctx.lineTo(kneeX, lineY - 4);
    ctx.lineTo(footX, lineY);
    ctx.stroke();

    // Arms
    ctx.beginPath();
    ctx.moveTo(shoulderX, lineY);
    ctx.lineTo(shoulderX + 15, lineY - 20);
    ctx.stroke();

    drawCanvasHUD(ctx, "POTENTIAL FALL POSTURE DETECTED", "#e11d48", "Spine Angle: 12.4° | Posture: Grounded / Horizontal", w, h);
  }
}

function drawCanvasHUD(ctx, statusText, color, subtext, w, h) {
  ctx.fillStyle = color;
  ctx.font = 'bold 15px Inter, sans-serif';
  ctx.fillText(`[SYNTHETIC SENSOR FEED: ${statusText}]`, 20, 32);

  ctx.fillStyle = '#e2e8f0';
  ctx.font = '12px Inter, sans-serif';
  ctx.fillText(subtext, 20, 54);

  // Disclaimer watermark
  ctx.fillStyle = '#64748b';
  ctx.font = '10px Inter, sans-serif';
  ctx.fillText('SafeFall AI Signal Preview • Prototype Technology (Non-Diagnostic)', 20, h - 16);
}

// =====================================================================
// 10. WEBCAM STREAMING (BROWSER MEDIADEVICES API)
// =====================================================================
async function startWebcam() {
  const video = document.getElementById('webcam-video');
  const placeholder = document.getElementById('webcam-placeholder');
  const statusMsg = document.getElementById('webcam-status-msg');
  const startBtn = document.getElementById('btn-start-webcam');
  const stopBtn = document.getElementById('btn-stop-webcam');

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    statusMsg.innerHTML = '<span class="text-danger">⚠️ Camera API is not supported by your browser or environment.</span>';
    return;
  }

  try {
    statusMsg.innerHTML = '<span style="color: #93c5fd;">Requesting camera permission...</span>';
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 360 } });
    appState.webcamStream = stream;
    video.srcObject = stream;
    video.classList.remove('hidden');
    placeholder.classList.add('hidden');
    startBtn.disabled = true;
    stopBtn.disabled = false;
    statusMsg.innerHTML = '<span class="text-success">🟢 Live camera preview active. Pose estimation running in local sandbox.</span>';
  } catch (err) {
    console.warn("Webcam access error:", err);
    statusMsg.innerHTML = `<span class="text-danger">⚠️ Camera access denied or unavailable (${err.name}). You can continue using the Synthetic Sensor visualizer or Simulate Fall button.</span>`;
  }
}

function stopWebcam() {
  const video = document.getElementById('webcam-video');
  const placeholder = document.getElementById('webcam-placeholder');
  const statusMsg = document.getElementById('webcam-status-msg');
  const startBtn = document.getElementById('btn-start-webcam');
  const stopBtn = document.getElementById('btn-stop-webcam');

  if (appState.webcamStream) {
    appState.webcamStream.getTracks().forEach(track => track.stop());
    appState.webcamStream = null;
  }

  video.srcObject = null;
  video.classList.add('hidden');
  placeholder.classList.remove('hidden');
  startBtn.disabled = false;
  stopBtn.disabled = true;
  statusMsg.innerHTML = '<span style="color: var(--text-dim);">Camera preview stopped.</span>';
}

// =====================================================================
// 11. ANALYTICS CHARTS (LIGHTWEIGHT CANVAS CHARTS)
// =====================================================================
function renderAnalyticsCharts() {
  const incidents = getStoredIncidents();

  // 1. Room Distribution Bar Chart
  const roomCounts = { "Living Room": 0, "Bathroom": 0, "Kitchen": 0, "Bedroom": 0, "Staircase": 0 };
  incidents.forEach(i => {
    if (roomCounts[i.room] !== undefined) roomCounts[i.room]++;
    else roomCounts[i.room] = 1;
  });
  drawBarChart('chart-room-distribution', roomCounts);

  // 2. Severity Distribution Doughnut Chart
  const sevCounts = { "Critical": 0, "High": 0, "Low": 0 };
  incidents.forEach(i => {
    if (sevCounts[i.severity] !== undefined) sevCounts[i.severity]++;
    else sevCounts[i.severity] = 1;
  });
  drawDoughnutChart('chart-severity-distribution', sevCounts);
}

function drawBarChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const entries = Object.entries(data);
  const maxVal = Math.max(1, ...Object.values(data));
  const paddingBottom = 40;
  const paddingTop = 20;
  const chartHeight = h - paddingBottom - paddingTop;
  const barWidth = 45;
  const spacing = (w - (entries.length * barWidth)) / (entries.length + 1);

  entries.forEach(([label, count], idx) => {
    const barH = (count / maxVal) * chartHeight;
    const x = spacing + idx * (barWidth + spacing);
    const y = h - paddingBottom - barH;

    // Bar fill
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(x, y, barWidth, barH);

    // Value text
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(count.toString(), x + barWidth / 2, y - 6);

    // Label text
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px Inter, sans-serif';
    const shortLabel = label.length > 8 ? label.substring(0, 7) + '.' : label;
    ctx.fillText(shortLabel, x + barWidth / 2, h - 16);
  });
}

function drawDoughnutChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const colors = {
    "Critical": "#e11d48",
    "High": "#f59e0b",
    "Low": "#10b981"
  };

  const total = Object.values(data).reduce((acc, v) => acc + v, 0);
  const cx = w * 0.4;
  const cy = h / 2;
  const radius = 70;
  const innerRadius = 45;

  let currentAngle = -Math.PI / 2;

  if (total === 0) {
    ctx.fillStyle = '#334155';
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#0e1526';
    ctx.beginPath();
    ctx.arc(cx, cy, innerRadius, 0, Math.PI * 2);
    ctx.fill();
    return;
  }

  Object.entries(data).forEach(([key, val]) => {
    if (val === 0) return;
    const sliceAngle = (val / total) * Math.PI * 2;

    ctx.fillStyle = colors[key] || '#94a3b8';
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, currentAngle, currentAngle + sliceAngle);
    ctx.closePath();
    ctx.fill();

    currentAngle += sliceAngle;
  });

  // Inner cutout for doughnut
  ctx.fillStyle = '#0e1526';
  ctx.beginPath();
  ctx.arc(cx, cy, innerRadius, 0, Math.PI * 2);
  ctx.fill();

  // Total text inside doughnut
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 16px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(total.toString(), cx, cy + 5);

  // Legend on right side
  let legendY = 60;
  Object.entries(data).forEach(([key, val]) => {
    ctx.fillStyle = colors[key];
    ctx.fillRect(w * 0.72, legendY - 10, 12, 12);

    ctx.fillStyle = '#cbd5e1';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${key}: ${val}`, w * 0.72 + 20, legendY);
    legendY += 28;
  });
}

// =====================================================================
// 12. TAB NAVIGATION & UTILITIES
// =====================================================================
function switchMainTab(tabId, targetBtn) {
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  targetBtn.classList.add('active');
  const targetContent = document.getElementById(tabId);
  if (targetContent) {
    targetContent.classList.add('active');
  }

  if (tabId === 'tab-analytics') {
    renderAnalyticsCharts();
  }
}

function formatDateTime(d) {
  const pad = (n) => n.toString().padStart(2, '0');
  const year = d.getFullYear();
  const month = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const hours = pad(d.getHours());
  const mins = pad(d.getMinutes());
  const secs = pad(d.getSeconds());
  return `${year}-${month}-${day} ${hours}:${mins}:${secs}`;
}
