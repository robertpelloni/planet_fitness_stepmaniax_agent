# Changelog

All notable changes to this project will be documented in this file.

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

[... previous entries remain unchanged ...]
