# Staff Training Manual: StepManiaX Pilot Onboarding

**Objective:** Equip club staff to effectively introduce, manage, and troubleshoot StepManiaX during the 90-day pilot program.

---

## 0. Global Operations Center & System Management (v9.3.0)
Management and technical staff can access the consolidated **Global Operations Center** (`/admin/unified-dashboard`):
- **Executive Wallboard:** Comprehensive overview consolidating outreach pipelines, real-time fleet telemetry, pilot revenue tracking, and automated service dispatches.
- **System Tray & Process Controls:** Launch or stop servers cleanly via `./system_tray_manager.py` (supporting `--start`, `--stop`, `--restart`, `--status`, `--logs`).
- **Interactive Metrics & Tooltips:** Informational tooltips accompany every metric and control to assist staff in understanding MET calculations and telemetry health indicators.

## 1. Introduction to StepManiaX (The "Elevator Pitch")
"StepManiaX is our new **Gamified HIIT** cardio amenity. It’s designed to make high-intensity cardio more engaging by turning it into an interactive experience. It’s low-impact, high-energy, and perfect for members looking for something more exciting than a traditional treadmill."

## 2. Key Staff Responsibilities
### A. Introduction & Assistance
- Proactively invite members to try a "10-minute HIIT session."
- Assist new users with the touchscreen UI and help them select the "Beginner" or "Basic" difficulty levels for their first session.
- Emphasize that the unit is "Etiquette Friendly"—members should use the headphone jack for audio.

### B. Daily Operational Checks
- **Morning Shift:** Ensure the unit is powered on and the touchscreen is clean.
- **Mid-Day Shift:** Check the stages for any debris or obstructions.
- **Evening Shift:** Perform a quick visual inspection of the handrails and load cells.

## 3. Managing High Demand (Gym Floor Etiquette)
To ensure the machine remains accessible in the "Judgement Free Zone":
- Remind members that sessions are limited to **2 songs or 10 minutes** during peak hours.
- Encourage users to scan in using the QR code (if applicable) to track their progress.

## 4. Basic Troubleshooting
| Issue | Potential Solution |
| :--- | :--- |
| **No Sound** | Ensure the member's headphones are fully plugged in. Check if the "Silent Mode" volume is up. |
| **Stage Not Responding** | Ensure there is no debris under the stage. Restart the unit using the rear power switch if necessary. |
| **Screen Frozen** | Power cycle the unit. If the issue persists, contact the 48-hour service line immediately. |

## 5. Cleaning & Maintenance
- Use the same medical-grade disinfectants used for other cardio equipment.
- **Do not** spray liquid directly onto the touchscreen; spray onto a cloth first.
- Metal stages should be wiped down daily to prevent moisture buildup.

## 6. Reporting Issues
For any hardware failures or persistent software issues:
- **Contact:** [Agent/Initiative Email]
- **SLA:** We guarantee on-site service within **48 hours**.

### 6.1 Automated Telemetry Ingestion & Autonomous Dispatch (v9.4.0)
The hardware fleet transmits real-time telemetry packets via `ingest_telemetry_packet.py` or the `/ws/telemetry` socket. If a unit experiences uptime degradation below 95% or an anomalous predictive health score below 70, the system automatically opens an Andamiro Field Service SLA dispatch (`AUTO-DISP-...`) with pending status and tags the hardware as `Service Dispatched`. Field technicians can inspect and resolve these dispatches directly from the Global Operations Center (`/admin/unified-dashboard`).

### 6.2 Enterprise Telemetry & MET Data Export (v9.5.0)
Franchise directors can export live fleet biomechanics and operational telemetry directly via the Enterprise API endpoint:
- **JSON Format**: `GET /api/v1/enterprise/export` (Returns full telemetry, engagement, sentiment, and session histories with dynamically modeled ACSM MET estimations).
- **CSV Spreadsheet**: `GET /api/v1/enterprise/export?format=csv` (Downloads `enterprise_telemetry_export.csv` containing Unit ID, Name, Location, Uptime %, Total Scans, Average Session Duration, Estimated MET Capacity, Health Score, and Maintenance Status).

---
**Remember:** You are the face of this pilot. Your enthusiasm and assistance will directly impact the data we collect on member retention.
