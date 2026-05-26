# Handoff

## Project Status: v4.3.0 - Staff Operations Milestone Complete
The StepManiaX B2B platform has successfully transitioned to a fully modular blueprint-driven architecture. The staff and facility operations portals are now fully reactive, providing real-time metrics and member engagement feeds.

## Major Accomplishments
1. **Full Blueprint Modularization:** The entire application logic has been migrated into logical blueprints (`auth`, `admin`, `staff`, `member`, `api`).
2. **Reactive Staff Dashboard:** Implemented HTMX polling for live equipment metrics, member activity feeds, and critical alerts.
3. **Namespaced URL Resolution:** Standardized all internal routing to use blueprint prefixes, improving maintainability.

## Implementation Details
- **Entry Point:** `app.py` is now a lean registration file.
- **Backend Logic:** Contained in `blueprints/` folder.
- **Frontend Real-time:** Uses HTMX with partial templates in `templates/partials/`.

## Critical Context for Next Model
- **Routing Convention:** Always use the blueprint name as a prefix in `url_for` (e.g., `admin.dashboard`).
- **Permissions:** Admin has global scope; others are filtered by `franchise_id`.
- **Database:** SQLite (`crm.db`) manages leads, members, telemetry, and audit logs.

## Immediate Next Steps
- Implement ML-based failure prediction in `analytics.py`.
- Expand the autonomous outreach engine with more personalized CRM-driven templates.
- Automate the generation of high-fidelity PDF pilot reports.

## Start Command
```bash
python3 app.py
```
To initialize/reset DB:
```bash
flask init-db
```
To populate with test data:
```bash
python3 populate_test_data.py
```
