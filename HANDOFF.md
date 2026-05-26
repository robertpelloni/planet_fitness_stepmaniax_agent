# Handoff

## Project Status: v4.2.0 - Blueprint Architecture Complete
The application has successfully transitioned from a monolithic `app.py` to a modular, blueprint-driven architecture. The core sales automation engine and pilot management platform are fully operational.

## Recent Achievements
1. **Full Blueprint Migration:** Routes are now organized into `blueprints/auth.py`, `blueprints/admin.py`, `blueprints/staff.py`, `blueprints/member.py`, and `blueprints/api.py`.
2. **Security Intelligence Dashboard:** A new administrative portal (`/admin/security`) provides visual insights into system security and audit logs.
3. **Template Standardization:** All UI components have been updated to use namespaced routing.

## Critical Context for Next Model
- **Routing:** Always use namespaced `url_for` (e.g., `url_for('staff.staff_dashboard')`).
- **Permissions:** Admin has global access; others are restricted by `role` and granular `perm_` flags in the `User` model.
- **Database:** `crm.db` (SQLite) is the source of truth for leads, members, and telemetry.

## Pending Tasks (See TODO.md)
- [ ] Implement advanced telemetry anomaly detection.
- [ ] Automate high-fidelity PDF report generation for franchisees.
- [ ] Expand the autonomous outreach cadence with personalized AI messaging.

## Execution Command
To start the application:
```bash
python3 app.py
```
To initialize the database:
```bash
flask init-db
```
