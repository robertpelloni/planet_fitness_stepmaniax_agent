# Memory

## Core Vision & Progress
The repository is focused on the complete autonomous execution of a B2B sales pipeline for StepManiaX cardio units targeting Planet Fitness franchise groups.

## Architectural Observations (v4.3.0)
- **Blueprint Architecture:** The application has been fully refactored into modular Flask Blueprints (`auth`, `admin`, `staff`, `member`, `api`). This allows for clean separation of concerns and role-based data isolation.
- **Namespaced Routing:** All templates and redirects now use namespaced endpoints (e.g., `staff.facility_operations`) instead of global names.
- **HTMX Live Monitoring:** Real-time updates for equipment status, alerts, and member activity are powered by HTMX polling, providing staff with sub-minute visibility into club operations.
- **RBAC & Multi-Tenancy:** Robust role-based access control is enforced at the blueprint and decorator level, ensuring strict data isolation between different franchise groups.

## Key Design Traits
- **Lean Entry Point:** `app.py` serves as a minimal configuration and blueprint registration hub.
- **Partial Template Architecture:** Metrics and feeds are organized into `templates/partials/` for high-frequency HTMX updates.
- **Security-First:** Persistent audit logging and automated account lockout policies are standard across all portals.

## Future Milestones
- ML-based failure prediction for equipment maintenance.
- Automated generation of high-fidelity sales collateral based on real-time pilot engagement data.
