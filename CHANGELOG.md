# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0] - Member Portal & Unified Schema Milestone
- **Member-Facing Dashboard:** Launched a dedicated portal for gym members to view pilot status and update profiles.
- **Unified SQLAlchemy Schema:** Migrated the legacy 'leads' and 'outreach_logs' tables into the SQLAlchemy ORM as `Lead` and `OutreachLog`.
- **Enhanced Multi-Tenancy:** Hardened data isolation for equipment metrics, alerts, and members using strict `franchise_id` foreign keys.
- **Dynamic Onboarding:** Updated the onboarding portal to dynamically fetch active pilot locations from the `Lead` table.
- **Security Hardening:** Enforced role-based redirects and fixed fragile string-matching heuristics in the telemetry API.

## [2.1.0] - Multi-Tenancy & Webhooks Milestone
- **Multi-Tenant Dashboard:** Implemented role-based access control (RBAC) allowing franchisees to view only their specific club data.
- **Webhook Notification System:** Launched `notifications.py` and a Webhook model supporting Discord/Slack alerts for critical events.
- **Automated Notifications:** Integrated real-time alerts for equipment uptime drops and new member registrations.
- **Settings Page:** Added a management interface for users to configure and view their notification webhooks.
- **CLI Tenant Tools:** Updated `crm_tool.py` with commands for managing multi-tenant users and webhooks.
- **Enhanced Data Models:** Added `role`, `franchise_id` to `User`, and created the `Webhook` model.

## [2.0.0] - Member Lifecycle Milestone
- **Member Onboarding Workflow:** Launched `member_onboarding.py` and a web-based onboarding portal for pilot participants.
- **Retention Analytics Integration:** Updated `analytics.py` to factor member onboarding conversion rates into ROI and retention lift projections.
- **Onboarding Portal:** Created `templates/onboarding_portal.html` providing a professional registration interface for gym members.
- **Dashboard Enhancements:** Added an "Onboarding & Retention" metrics card to the management dashboard.
- **Data-Driven Reporting:** Enhanced `report_generator.py` and `pilot-performance-report.md` to include onboarding and conversion KPIs.
- **Database Schema Update:** Added `Member` model to `crm.db` to track member lifecycle states.

## [1.9.0] - Telemetry & Monitoring Milestone
- **Real-time Telemetry API:** Launched `/api/v1/telemetry` for StepManiaX units to report live engagement and uptime data.
- **Automated Health Monitoring:** Established `health_monitor.py` to detect low uptime and generate system alerts.
- **Engagement Dashboard:** Integrated real-time Chart.js visualizations for session scans and unit utilization.
- **Technical Documentation:** Consolidated manufacturer specifications into `manufacturer-alignment.md`.

## [1.8.0] - Sales Funnel Management Milestone
- **Interactive CRM Dashboard:** Launched a web-based UI for managing sales leads and updating funnel status.
- **Automated Performance Reporting:** Integrated `report_generator.py` into the dashboard for one-click ROI reports.
- **Technical Resource Portal:** Established a secure resource route for accessing B2B sales collateral.

## [1.5.0] - Data Persistence & CRM Migration
- **SQLite CRM Migration:** Migrated the flat-file `crm.json` to a structured SQLite database (`crm.db`).
- **CRM CLI Tool:** Launched `crm_tool.py` for advanced lead management and portfolio-wide ROI analytics.
- **Scraper Heuristics:** Enhanced lead discovery with 'junk' detection to improve data quality in the discovery pipeline.

## [1.0.0] - Initial Autonomous Agent Release
- **Lead Discovery Engine:** Implemented automated web scraping for Planet Fitness franchise groups.
- **ROI Modeling Framework:** Established the LTV-based financial modeling in `analytics.py`.
- **B2B Asset Generation:** Automated creation of personalized emails and pitch decks.
- **Sales Strategy:** Formalized the "Rogue Franchise Loophole" in `VISION.md` and `CASE_STUDY.md`.
