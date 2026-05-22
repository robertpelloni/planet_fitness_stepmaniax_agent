# Changelog

All notable changes to this project will be documented in this file.

## [0.9.0]
- **Operational Onboarding:** Created `staff-training-manual.md` to guide club staff through the StepManiaX pilot.
- **Strategic Scaling:** Drafted `regional-expansion-strategy.md` outlining the "Land and Expand" methodology for regional rollouts.
- **CRM Enrichment:** Enhanced `crm.json` with `roi_projection` data to track potential portfolio impact per lead.
- **Workflow Maturity:** Updated `ROADMAP.md` and `TODO.md` to reflect full readiness for Phase 3 and Phase 4 execution.

## [0.8.0]
- **ROI Analytics:** Launched `roi_calculator.py` to model the financial impact of retention lift for franchisees.
- **Outreach Automation:** Implemented `generate_personalized_assets.py` for dynamic, CRM-driven sales collateral generation.
- **Workflow Integration:** Updated `pipeline.sh` to include ROI projection and asset generation in the automated sequence.

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

## [0.2.0]
- Added `pipeline.sh` to automate the Python virtual environment setup, dependency installation, and execution of the lead scraping utility.
- Updated `README.md` to include instructions for the new automated execution pipeline.

## [0.1.7]
- Created `kpi-tracker.md` to track Agent Performance Metrics (Leads Generated, Outreach Volume, Discovery Calls).
- Updated `TODO.md` to reflect the addition of the KPI tracking mechanism.

## [0.1.6]
- Created `scrape_leads.py` as a generic template to unblock Phase 2.1 data gathering.
- Created `requirements.txt` to track new Python dependencies (requests, beautifulsoup4).
- Updated `DEPLOY.md` to document the Python execution environment.
- Added `.gitignore` and `.env.example` to enforce secret management and keep binaries out of version control.

## [0.1.5]
- Unblocked Phase 1.1: Successfully extracted StepManiaX cabinet dimensions from stepmaniax.com.
- Updated `pitch-deck.md` and `pilot-mou.md` to reflect real-world machine footprint dimensions, replacing placeholder estimates.

## [0.1.4]
- Concluded internal agent implementation cycles. Remaining tasks marked as blocked due to requiring external credentials (LinkedIn Sales Navigator) and manual data gathering.

## [0.1.3]
- Implemented `pilot-mou.md` containing the Phase 4.1 Memorandum of Understanding template.
- Updated TODO.md to mark Phase 4.1 as complete.

## [0.1.2]
- Implemented `outreach-script.md` containing the Phase 3 outreach email template and objection handling cheat sheet.
- Updated TODO.md to mark Phase 3.1 as complete.

## [0.1.1]
- Implemented `pitch-deck.md` containing the Phase 1 B2B presentation copy.
- Updated TODO.md to mark Phase 1.2 as complete.

## [0.1.0] - Initial Setup
- Initialized core repository documentation (VISION, ROADMAP, TODO, HANDOFF, etc.).
- Established AI agent instructions and contribution guidelines.