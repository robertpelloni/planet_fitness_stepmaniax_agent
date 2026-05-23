# Changelog

All notable changes to this project will be documented in this file.

## [1.9.0]
- **Telemetry Ingestion API:** Launched `/api/v1/telemetry` for real-time equipment data ingestion.
- **Automated Reporting:** Integrated `report_generator.py` to produce data-driven performance reports directly from the dashboard.
- **CRM Management UI:** Added lead status management to the dashboard, enabling direct sales funnel transitions.
- **Automated Health Monitoring:** Launched `health_monitor.py` to detect and alert on equipment operational anomalies.
- **Improved Security:** Enabled CSRF protection for all dashboard management actions.

## [1.8.0]
- **Enhanced Dashboard UI:** Implemented real-time usage metrics visualization using Chart.js.
- **Monitoring & Alerts:** Added a "System Alerts & Health" panel to track equipment maintenance and operational status.
- **Member Scheduling:** Integrated a "Member Booking Schedule" view to manage SMX unit sessions.
- **Security Hardening:** Implemented CSRF protection across the web dashboard and login interfaces.
- **Database Schema Expansion:** Added `Alert` and `MemberSchedule` models to `crm.db` to support advanced monitoring.

[... previous entries remain unchanged ...]
