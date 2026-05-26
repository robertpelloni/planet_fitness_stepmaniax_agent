# Memory

## Core Vision & Progress
The repository is dedicated to the autonomous execution of a B2B sales pipeline for StepManiaX cardio units targeting Planet Fitness franchise groups.

## Architectural Observations (v4.4.0)
- **Modular Blueprint Architecture:** The application logic is fully decoupled into `auth`, `admin`, `staff`, `member`, and `api` blueprints. This structure supports high maintainability and role-based data isolation.
- **System Integrity (v4.4.0):** Database integrity is now secured via an automated, timestamped backup system (`backup_job.py`) using the `sqlite3.backup` API, integrated into the core monitoring loop.
- **Heartbeat & Pulse Monitoring:** Background automation tasks (Lead Scraper, Health Monitor, Outreach Cadence) are monitored in real-time via the `AutomationHeartbeat` model and visualized in the System Health dashboard.
- **Reactive Infrastructure:** HTMX is utilized for sub-minute UI updates across all operational dashboards, including live metrics and member activity feeds.

## Key Design Traits
- **Namespaced Routing:** Strict enforcement of namespaced `url_for` calls (e.g., `staff.dashboard`) ensures correct endpoint resolution post-refactor.
- **Hybrid Auth:** Concurrent support for session-based user authentication and machine-to-machine API-Key authorization.
- **Financial Intelligence:** The `analytics.py` engine calculates LTV-based ROI, factoring in real-world member engagement and conversion metrics.

## Future Focus
- Integration of ML-based hardware failure prediction.
- Expansion of autonomous outreach with multi-channel CRM synchronization.
- Automated generation of high-fidelity B2B marketing collateral.
