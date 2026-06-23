# Cold Outreach Campaign Execution Protocol

## Campaign Overview
This document outlines the deployment strategy for the initial cold outreach phase targeting regional Planet Fitness Franchise Groups. The goal is to bypass corporate procurement by offering a zero-risk, high-ROI pilot of StepManiaX.

## Target Audience
Decision-makers (VP of Operations, Regional Directors, Franchise Owners) identified in `LEADS.md`, specifically targeting:
* EPIC Fitness Group (Midwest)
* Flynn Group (National)
* UK Fitness Corp (London)
* Canada Gyms (Toronto)

## Execution Cadence

### Touchpoint 1: The "Rogue Pilot" Pitch (Day 1)
* **Medium:** Direct Email (via automated CRM dispatch)
* **Content:** Utilize `outreach/outreach-script.md` (Template 1).
* **Focus:** Highlight the specific problem (cardio floor stagnation) and the Zero-Risk 90-day pilot solution.
* **Call to Action:** Request a 10-minute Discovery Call.

### Touchpoint 2: The Data-Driven Follow-Up (Day 3)
* **Medium:** Email (Automated via `launch_outreach.py`)
* **Content:** Utilize `outreach/follow-ups.md` (Day 3 Template).
* **Focus:** Provide hard data—mention the 2-4% retention lift and the interactive ROI simulator link on the Prospect Portal.

### Touchpoint 3: The Technical/Operational Reassurance (Day 7)
* **Medium:** LinkedIn Message or Direct Email
* **Content:** Utilize `outreach/follow-ups.md` (Day 7 Template).
* **Focus:** Address unspoken objections regarding maintenance and floor space by linking to `maintenance-slas.md`.

### Touchpoint 4: The "Final Attempt" / Scarcity Play (Day 14)
* **Medium:** Direct Email
* **Content:** Utilize `outreach/follow-ups.md` (Day 14 Template).
* **Focus:** Note that pilot hardware slots for the quarter are closing.

## System Integration
* All campaign emails are populated into the `OutreachLog` table.
* The `health_monitor.py` task runs the `launch_outreach()` function daily to advance leads through the cadence automatically.
* Responses (simulated or real) update the lead status to "Discovery Call Scheduled" within the CRM.
