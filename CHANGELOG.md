# Changelog

All notable changes to this project will be documented in this file.

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
