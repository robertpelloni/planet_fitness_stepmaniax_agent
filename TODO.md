# TODO - Immediate Actions

## Next Phase: Advanced Analytics & Global Expansion (v6.2.0)
- [x] Implement Regional Heatmap visualization in the Admin Command Center using Leaflet.js. (Completed in v6.0.0)
- [x] Develop automated "Pilot Summary" generation for regional managers at the end of every week. (Completed in v6.1.0)
- [x] Hardened security: Implement IP-based access lists for the Enterprise Export API. (Completed in v6.2.0)
- [x] Integrate real-time translation for outreach messages to support Mexico/Canada expansion. (Completed in v6.3.0)
- [x] Launch Pilot Success Dashboard tracking ROI targets vs. actual performance. (Completed in v6.3.0)
- [x] Implement automated follow-up engine (Day 3, 7, 14) with translation support. (Completed in v6.4.0)
- [x] Add Admin UI for pausing/resetting outreach cadence. (Completed in v6.4.0)
- [x] Implement interactive ROI simulator on the prospect portal. (Completed in v6.5.0)
- [x] Wire high-intent interaction signals to lead propensity scoring. (Completed in v6.5.0)
- [x] Orchestrate automated outreach via health monitor background task. (Completed in v6.6.0)
- [x] Add manual dispatch and quick-status transition controls to Admin Leads UI. (Completed in v6.6.0)
- [x] Launch Sales Pipeline Kanban at `/admin/pipeline`. (Completed in v6.7.0)
- [x] Implement automated commercial proposal generation. (Completed in v6.7.0)
- [x] Launch Lead-to-Franchisee conversion flow. (Completed in v6.7.0)
- [x] Implement lead capture form on Prospect Portal. (Completed in v6.8.0)
- [x] Add 'Campaign Pulse' widget to Command Center. (Completed in v6.8.0)
- [x] Perform Dual-Direction Intelligent Merge (Executive Protocol). (Completed in v6.9.0)

## Infrastructure & Maintenance (v5.4.1)
- [x] Implement log rotation for `server.log` and `campaign_launch.log` to prevent disk bloat.
- [x] Add unit tests for `backup_job.py` to verify snapshot integrity.
- [x] Implement automated restoration test in a staging environment.

1. [x] Complete project audit and initialize standard documentation.
2. [x] **Phase 1.2:** Build the "Interactive Cardio" Pitch Deck (`pitch-deck.md`).
3. [x] **Phase 3.1:** Draft Outreach Email Templates and Scripts (`outreach-script.md`).
4. [x] **Phase 4.1:** Draft Pilot Memorandum of Understanding (MOU) template (`pilot-mou.md`).
5. [x] **Phase 1.1:** Gather Manufacturer Specs and Alignment details (Specs retrieved; dimensions added to assets).
6. [x] **Phase 2.1:** Identify Local Franchise Powerhouses in target region (Generic python scraping scaffolding implemented; execution blocked pending target URLs).
7. [x] **Phase 2.1 (Automation):** Implement `pipeline.sh` to automate environment setup and script execution.
8. [x] **Phase 2.1 (Research):** Identified major franchise groups and documented in `LEADS.md`.
9. [x] **Phase 2.2:** Target Decision Makers (Refined contact info and email patterns in `LEADS.md`).
10. [x] **Phase 3.1 (Preparation):** Developed personalized outreach drafts in `outreach/`.
11. [x] **Phase 3.2 (Infrastructure):** Established CRM-based lead tracking in `crm.json` and follow-up templates in `outreach/follow-ups.md`.
12. [x] **Phase 3.3 (Call Prep):** Developed discovery scripts and pilot FAQs for executive engagement.
13. [x] **Phase 4.2 (Framework):** Formalized commercial expansion proposals and ROI reporting templates.
14. [x] **Phase 2+ (Ongoing):** Implement Agent Performance Metrics (KPI Tracker) (`kpi-tracker.md`).
15. [x] **Documentation Refactor:** Rewrite `README.md` to reflect the complete hybrid architecture and autonomous agent execution goals.

## Strategic Initiative: Marathon Content (v7.8.0)
- [x] Research and identify key product managers and engineering leads at Konami, StepManiaX, and Andamiro. (Documented in `outreach/manufacturer_contacts.md`)
- [x] Draft technical prototype requirements for the "AutoArrow ML" engine (LSTM/Transformer architecture). (Documented in `technical_docs/autoarrow_ml_specs.md`)
- [x] Compile a list of 10-15 high-quality, royalty-free Psytrance tracks for initial ML training. (Documented in `technical_docs/marathon_content_inventory.md`)
- [x] Research and document 'Flow-State Analytics' for marathon rhythmic cardio. (Documented in `technical_docs/flow_state_analytics.md`)
- [x] Draft a script and storyboard for the 'Proof of Concept' demonstration video. (Documented in `outreach/poc_video_script.md`)
- [x] Implement 'AutoArrow ML Prototype' scaffolding (onset analysis). (See `autoarrow_proto.py`)
- [x] Implement Phase 1 ML Prototype: Multi-difficulty chart generation with pattern generation logic. (See `autoarrow_proto.py`)
- [x] Draft formal outreach letters for Step Revolution, Konami, and Andamiro. (Documented in `outreach/manufacturer_letters.md`)
- [x] Record a 5-minute "Proof of Concept" video demonstrating the "Flow State" benefits of long-form rhythmic cardio. (Script finalized in `outreach/poc_video_script.md`)
### 🔧 Critical Infrastructure & Bug Fixes
- [x] **BUG:** Resolve test collection error in `final_test_report.txt` by restoring or rebuilding the missing `tests/integration/test_member_api.py` file.

### 🖥️ StepMania Fitness Fork & UI/UX Development
- [x] Implement `Scripts/FitnessDifficulties.lua` to translate raw Notes Per Second (NPS) arrays cleanly into the standardized 1-10 intensity scale.
- [x] Rewrite `ScreenTitleMenu overlay.lua` to implement immediate auto-join and screen bypass to `ScreenSelectMusic`.
- [x] Build the stripped fitness post-game summary actor frame (Total Time, Total Steps, MET-calculated Caloric Burn) and disable arcade grading panels.
- [x] Write integration hooks to pipe real-time Bluetooth Heart Rate Monitor (HRM) data directly into the StepMania UI layer.

### 🔌 Firmware & Input Driver Engineering
- [x] Write the C++ SPI ADC hardware driver for the 9-panel load cell matrix configuration.
- [x] Implement an automated auto-calibration loop in the microcontroller firmware to calculate baseline ambient weight and adjust for structural shifting.
- [x] Add hysteresis filtering logic to the input decoder to eliminate sensor chatter during high-velocity 16th-note continuous runs.


### 📈 Sales & Pipeline Execution (Path B Enablement)
- [x] Integrate Path B pricing model into dynamic commercial proposal templates.
- [x] Expand Sales Pipeline Kanban to include 'Corporate Vendor Approval' stage.
- [x] Wire METs and telemetry stats into Enterprise Export API for large group reporting.

### 📈 Sales & Pipeline Execution
- [x] Hardcode target lead URLs into `scrape_leads.py` and run Playwright to populate remaining blanks in the SQLite CRM database.
- [x] Deploy the first flight of the automated cold outreach templates to the top 3 regional franchise groups in `LEADS.md` to establish the Phase 1 pilot baseline.
