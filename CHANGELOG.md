# Changelog

All notable changes to this project will be documented in this file.

## [3.2.0] - Member Engagement & Tracking Milestone
- **Member Dashboard v2:** Launched a reactive portal for pilot participants with session booking and engagement visualization.
- **Engagement Scoring:** Implemented an automated tracking system calculating points and retention scores based on daily activity.
- **Staff Member Management:** Developed a dedicated interface for staff to manage member onboarding and monitor individual progress.
- **Relational Telemetry:** Upgraded the telemetry ingestion engine to attribute StepManiaX usage to individual member accounts.

## [3.1.0] - Operational Intelligence & Real-time Analytics Milestone
- **Real-time Staff Dashboard:** Integrated HTMX-powered usage distribution and maintenance metrics.
- **Anomaly Detection:** Enhanced `health_monitor.py` to automatically flag significant spikes or drops in equipment usage.
- **Prospect Portals:** Launched personalized B2B landing pages with secure tokenized access and dynamic ROI modeling.
- **Dual-Mode Authentication:** Hardened API security to support both Session and API Key authorization for internal dashboards.

## [2.9.0] - Lead Intelligence & Playwright Scraper Milestone
- **Playwright Scraper:** Upgraded `scrape_leads.py` to use Playwright for headless browser scraping of dynamic franchise portals.
- **Lead Propensity Scoring:** Implemented an automated scoring algorithm in `analytics.py` to rank leads by sales priority.
- **Propensity Leaderboard:** Integrated a new "High Propensity Targets" section into the Admin Dashboard for prioritized outreach.
- **Scalable Extraction:** Enhanced metadata extraction heuristics for leadership team pages across multiple franchise group domains.

## [2.8.0] - Production Deployment & Monitoring Milestone
- **Production Infrastructure:** Added `gunicorn_config.py` and systemd service templates for professional deployment.
- **Continuous Health Monitoring:** Updated `health_monitor.py` with a persistent execution loop for real-time alerting.
- **Deployment Automation:** Created `production_check.sh` to automate environmental verification.
- **Bug Fixes:** Resolved schema mismatch in `report_generator.py` and removed hardcoded API keys from frontend templates.
- **Documentation:** Overhauled `DEPLOY.md` with full production setup and operational instructions.

## [2.7.0] - Management & Security Hardening Milestone
- **Staff Analytics Integration:** Added 7-day engagement trend charts to the Staff Dashboard for club-level usage monitoring.
- **Admin User Management UI:** Launched a dedicated user provisioning interface in Settings for Global Admins.
- **Enhanced API Security:** Implemented dual-mode authentication (Session or API Key) for analytics endpoints to support both UI and machine access.
- **RBAC Audit:** Hardened all administrative and management routes with strict `@role_required` enforcement.

## [2.6.0] - Usage Trend Analytics & API Security Milestone
- **Historical Usage Tracking:** Implemented time-series tracking via `TelemetryHistory` to capture per-scan equipment data.
- **Usage Analytics API:** Launched `/api/v1/analytics/usage` for daily scan aggregation and trend reporting.
- **Interactive Trend Charts:** Integrated a new "Historical Usage Trends" line chart into the dashboard for 7-day engagement visualization.
- **API Key Authentication:** Hardened all `/api/v1/` REST endpoints with a mandatory `X-API-KEY` header requirement.
- **Telemetry Security:** Secured the machine-to-machine telemetry ingestion endpoint to prevent unauthorized metric injection.

## [2.5.0] - Member Management API & Centralized Config Milestone
- **Member REST API:** Launched a full CRUD API (`/api/v1/members`) for programmatic member management.
- **API Security:** Enforced RBAC and CSRF exemptions for the management API while maintaining session-based security.
- **Centralized Automation Config:** Created `config.py` to house all threshold and financial parameters (UPTIME_THRESHOLD, ROI defaults).
- **Multi-Tenant API Isolation:** Programmatic member access is isolated by `franchise_id` to ensure data privacy between clubs.

## [2.4.0] - Staff Operations & Real-time Monitoring Milestone
- **Staff-Facing Dashboard:** Launched a dedicated, high-visibility dashboard for facility staff to monitor club operations in real-time.
- **Real-time Updates (HTMX):** Integrated HTMX for seamless, live-reloading of usage metrics, maintenance logs, and critical alerts.
- **Automated Maintenance Alerts:** Updated telemetry logic to automatically flag equipment as 'Needs Maintenance' when performance drops below threshold.
- **Role-Based Access Control:** Added the 'Staff' role with restricted access to club-level monitoring and facility status.
- **Facility Management UI:** Designed a dark-mode Staff Portal for high-contrast monitoring in gym environments.

## [2.3.0] - RBAC & Security Hardening Milestone
- **Granular RBAC:** Introduced `role_required` decorator to secure administrative and management routes.
- **Member Access Control:** Restricted members to their dedicated portal, preventing access to facility telemetry or CRM data.
- **Unified Database Schema:** Standardized on pluralized table names (`leads`, `outreach_logs`) across SQLAlchemy and CLI tools.
- **Admin User Management:** Enhanced settings page to allow global administrators to manage all platform users.

## [2.2.0] - Member Portal & Unified Schema Milestone
- **Member-Facing Dashboard:** Launched a dedicated portal for gym members to view pilot status and update profiles.
- **Unified SQLAlchemy Schema:** Migrated the legacy 'leads' and 'outreach_logs' tables into the SQLAlchemy ORM as `Lead` and `OutreachLog`.
- **Enhanced Multi-Tenancy:** Hardened data isolation for equipment metrics, alerts, and members using strict `franchise_id` foreign keys.
- **Dynamic Onboarding:** Updated the onboarding portal to dynamically fetch active pilot locations from the `Lead` table.

## [2.1.0] - Multi-Tenancy & Webhooks Milestone
- **Multi-Tenant Dashboard:** Implemented role-based access control (RBAC) allowing franchisees to view only their specific club data.
- **Webhook Notification System:** Launched `notifications.py` and a Webhook model supporting Discord/Slack alerts for critical events.
- **Automated Notifications:** Integrated real-time alerts for equipment uptime drops and new member registrations.

[... previous entries remain unchanged ...]
