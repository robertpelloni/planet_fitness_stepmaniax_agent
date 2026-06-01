# Changelog

All notable changes to this project will be documented in this file.

## [6.8.0] - 2026-06-01
### Engagement Intelligence & Portal Lead Capture
- **Lead Capture Form:** Implemented a 'Request Pilot Demo' form on the Prospect Portal with HTMX-powered submission.
- **Discovery Status Integration:** Submission of the demo form automatically transitions lead status to 'Discovery Call Scheduled' and logs contact details to Lead Notes.
- **Engagement Visualization:** Added an "Engagement" column to the Lead Management UI displaying Portal Views and Propensity Scores.
- **Real-time Indicators:** Implemented CSS pulsing animations for high-engagement leads (>80 propensity or active views).
- **Campaign Pulse Widget:** Launched an outreach volume visualization widget in the Global Command Center.
- **System Hygiene:** Cleaned up internal log rotation files and generated markdown assets from Git tracking.

## [6.7.0] - 2026-06-01
### Sales Pipeline & Conversion Flow
- **Pipeline Kanban:** Implemented a visual, stage-based Sales Pipeline at `/admin/pipeline`.
- **Proposal Generator:** Added automated commercial proposal generation based on pilot performance data.
- **Lead Conversion:** Launched the Lead-to-Franchisee conversion flow, auto-provisioning secure user accounts for successful leads.
- **UI Expansion:** Integrated Proposal and Convert actions into the primary Lead Management dashboard.

## [6.6.1] - 2026-06-01
### Repository Consolidation & Synchronization
- **Intelligent Merge:** Successfully consolidated legacy feature branches (`feat/enterprise-sync`, `feat/lead-research`) into the `main` branch.
- **Repository Sync:** Established 100% synchronization between local and remote `main` branch.
- **Protocol Adherence:** Verified all structural documentation and execution scripts following the repository refresh.

## [6.6.0] - 2026-06-01
### Outreach Orchestration & Manual Controls
- **Background Orchestration:** Integrated `launch_outreach()` into `health_monitor.py` for fully autonomous cadence processing every minute.
- **Manual Dispatch UI:** Added "Dispatch" buttons to the Leads dashboard to trigger initial or follow-up outreach tiers immediately.
- **Quick-Status Transitions:** Implemented a status dropdown in the Leads table with HTMX-powered updates and audit logging.
- **Circular Import Resolution:** Optimized blueprint and background task imports to maintain architectural stability during expansion.
- **Database Safety:** Refined background task execution order to mitigate SQLite 'database is locked' errors during concurrent SQLAlchemy and raw SQL access.

## [6.5.0] - 2026-05-31
### High-Intent Lead Intelligence
- **Interactive ROI Simulator:** Launched a real-time portfolio lift calculator on the Prospect Portal with club-count and retention sliders.
- **Intent Tracking:** Integrated a secure tracking endpoint to log simulator interactions as "High Intent" signals.
- **Dynamic Propensity Scoring:** Updated `analytics.py` to award a +30 point boost to leads interacting with the simulator, prioritizing them for immediate follow-up.
- **Architectural Cleanup:** Refactored CSRF protection into `extensions.py` to support cross-blueprint namespaced exemptions.

## [6.4.0] - 2026-05-31
### Automated Outreach Cadence
- **Multi-tier Follow-up Engine:** Implemented automated Day 3, 7, and 14 follow-up tiers in `launch_outreach.py` with timing and tier-selection logic.
- **Cadence Dashboard:** Enhanced the Admin Leads interface with real-time cadence tracking and HTMX controls for pausing, resuming, and resetting outreach states.
- **Model Enhancement:** Added `cadence_paused` field to the `Lead` model to allow granular control over automated sequences.
- **Integration Testing:** Launched `tests/integration/test_cadence.py` verifying automated tier progression and timing logic.

## [6.3.0] - 2026-05-31
### Internationalization & Pilot Analytics
- **Real-time Translation:** Integrated `googletrans` into the outreach engine to support automated localization for Mexico (Spanish) and Canada (French) regions.
- **Pilot Success Dashboard:** Launched `/admin/pilot-success` providing real-time ROI tracking against franchise-specific MOU targets.
- **Geolocation Seeding:** Updated `populate_test_data.py` with regional coordinates (Detroit, Chicago, London, Toronto) to support spatial visualization.
- **Verification Suite:** Finalized `validate_system.sh` ensuring 100% pass rate across 13 integration and UI tests.

## [6.2.0] - 2026-05-31
### Enterprise Security & Reporting Refinement
- **IP-based Access Lists:** Implemented IP filtering for Enterprise APIs. Administrators can now restrict API access to specific whitelisted IPs per user.
- **Reporting Persistence:** Refined the weekly summary trigger in `health_monitor.py` to prevent duplicate report generation using `AutomationHeartbeat` tracking.
- **Security Hardening:** Updated `require_api_or_role` and `require_api_key` decorators to enforce IP validation.

## [6.1.0] - 2026-05-31
### Automated Performance Reporting
- **Weekly Pilot Summaries:** Launched background engine in `health_monitor.py` to aggregate and generate weekly ROI reports for all active pilot franchises.
- **Enhanced Reporting Engine:** Added `generate_weekly_summary` to `report_generator.py` with cross-table metric aggregation.
- **Reporting Infrastructure:** Created `weekly-pilot-summary-template.md` and dedicated report output directories.

## [6.0.0] - 2026-05-31
### Advanced Analytics & Global Expansion
- **Regional Heatmap:** Integrated Leaflet.js into the Admin Command Center for global fleet and lead visualization.
- **Geolocation API:** Launched `/api/v1/analytics/geo` to serve spatial data for units and prospects.
- **Spatial Schema:** Added `latitude` and `longitude` support to Lead and Equipment models.
- **UI Hardening:** Resolved structural template errors and implemented output escaping for system logs.

## [5.9.1] - 2026-05-31
### Multi-Region Scalability & Outreach Optimization
- **Multi-Region Support:** Implemented granular data filtering by `region_cluster` across all Admin and Staff dashboards.
- **UI Consolidation:** Launched a reusable `region_selector.html` partial for consistent fleet management.
- **Optimized Outreach:** Enhanced `launch_outreach.py` with ML-simulation for lead prioritization and sentiment-aware regional messaging.
- **Architectural Cleanup:** Centralized `log_security_event` in `extensions.py` and stabilized development session keys in `app.py`.
- **Scraper Hardening:** Fully restored Playwright-based lead scraping heuristics in `scrape_leads.py`.
- **Governance Compliance:** Fixed `.gitignore` and documentation standards to align with the Principal Directive.

## [5.8.1] - 2026-05-31
- **UI Test Infrastructure:** Integrated `pytest-playwright` and added a visual verification suite (`tests/integration/test_ui.py`) for Admin and Staff portals.
- **Database Alignment:** Fixed `populate_test_data.py` to include mandatory tables (`audit_log`, `outreach_logs`, `service_dispatch`) required for production-ready state.
- **Routing Namespacing:** Synchronized UI tests with the namespaced blueprint routing architecture.
- **Verification Completion:** Achieved 100% pass rate across backend (11) and frontend (2) integration test suites.

## [5.8.0]
- **Governance Protocol Initialization:** Formally documented the Autonomous Development & Governance Protocol in `GOVERNANCE.md`.
- **System Consolidation:** Successfully merged all v5.7.0 features into the `main` branch.

## [5.7.0]
- **Lead Management Refactor:** Migrated legacy flat-file lead data into SQLite and launched a full CRUD Admin interface.
- **Enhanced Scraper:** Updated `scrape_leads.py` with targeted heuristics for major franchise groups and Playwright support.
- **Automated Outreach Engine:** Launched `launch_outreach.py` for automated personalized message generation and stage tracking.

## [5.6.0]
- **Automated Service Dispatch:** Integrated a work order management system that automatically triggers service dispatches for offline equipment.
- **Maintenance UI:** Added an "Active Work Orders" module to the Global Command Center and "Dispatch" buttons to critical alert cards.
- **Service API:** Launched `/api/v1/dispatches` endpoint for programmatic ticket management.
- **Log Rotation:** Implemented `RotatingFileHandler` across all core background services and the main application server.

## [5.5.0]
- **Multi-Region Cluster Support:** Implemented `region_cluster` filtering across Admin and Staff dashboards to support international expansion.
- **Enhanced Background Logging:** Integrated `RotatingFileHandler` into `health_monitor.py` and `backup_job.py`.

## [5.4.1]
- **Repository Consolidation:** Successfully merged `feat/lead-research-v0.4.0` containing advanced hardware integration, MFA, and enterprise API features.
- **Security Hardening:** Integrated TOTP-based Multi-Factor Authentication and secure session cookie policies.
- **Hardware Integration:** Added support for Biometric and NFC-based member check-ins via telemetry endpoints.
- **Enterprise Capabilities:** Launched secure REST endpoints for BI export and lead synchronization.
- **Maintenance Automation:** Implemented log rotation and enhanced backup verification suites.

## [0.7.0]
- **Discovery Infrastructure:** Developed `discovery-call-script.md` and `pilot-faq.md` for structured decision-maker engagement.
- **Commercial Framework:** Created `commercial-proposal-template.md` and `pilot-performance-report.md` to bridge pilot success with regional procurement contracts.
- **Tone Refinement:** Standardized sales collateral with strict B2B corporate fitness terminology ("Gamified HIIT", "Member Retention Lift").

## [0.6.0]
- **CRM Implementation:** Initialized `crm.json` to formally track the B2B outreach funnel and executive lead states.
- **Strategic Cadence:** Developed a multi-touch follow-up framework in `outreach/follow-ups.md` (Day 3, 7, and 14).
- **Service Assurance:** Drafted `maintenance-slas.md` providing technical reliability specs and a 48-hour service guarantee.
- **KPI Synchronization:** Updated outreach metrics to reflect prepared personalized touches.

## [0.5.0]
- **Repository Synchronization:** Performed comprehensive upstream sync and intelligent merge, reconciling all active feature branches into `main`.
- **Contact Intelligence:** Refined `LEADS.md` with specific email patterns, LinkedIn URLs, and personalized notes for top franchise executives.
- **Personalized Outreach:** Created `outreach/` directory with tailored sales scripts for EPIC Fitness Group, PF Michigan Group, and Ohana Growth Partners.
- **Protocol Adherence:** Verified all structural documentation and execution scripts following the repository refresh.

## [0.4.0]
- **Targeted Lead Research:** Identified major Planet Fitness Franchise Groups (National Fitness Partners, Grand Fitness Partners, Excel Fitness, United FP, Taymax Group) and their operational regions.
- **Enhanced Scraper:** Updated `scrape_leads.py` with targeted URLs and basic parsing logic for franchise group team pages.
- **Architectural Documentation:** Created `MEMORY.md` for internal architectural observations and `IDEAS.md` for creative feature expansions.
- **KPI Initialization:** Populated initial lead counts in `kpi-tracker.md`.

## [0.3.0]
- Major documentation overhaul: Rewrote `README.md` to reflect the actual repository architecture (hybrid B2B collateral workspace and Python data-gathering utility).
- Updated README to clearly outline the overarching autonomous agent case-study goals and the 4-Phase SOP execution pipeline.

## [2.0.0] - Member Lifecycle Milestone
- **Member Onboarding Workflow:** Launched `member_onboarding.py` and a web-based onboarding portal for pilot participants.
- **Retention Analytics Integration:** Updated `analytics.py` to factor member onboarding conversion rates into ROI and retention lift projections.
- **Onboarding Portal:** Created `templates/onboarding_portal.html` providing a professional registration interface for gym members.
- **Dashboard Enhancements:** Added an "Onboarding & Retention" metrics card to the management dashboard.
- **Data-Driven Reporting:** Enhanced `report_generator.py` and `pilot-performance-report.md` to include onboarding and conversion KPIs.
- **Database Schema Update:** Added `Member` model to `crm.db` to track member lifecycle states.

[... previous entries remain unchanged ...]
