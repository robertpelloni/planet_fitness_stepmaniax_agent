# Autonomous Development & Governance Protocol (v8.0.0)

This document formalizes the operational framework for AI-driven development and repository maintenance for the StepManiaX B2B Platform.

## 1. Principle Directive: Continuous Autonomous Execution
The development agent operates under a mandate of total autonomy. This includes:
- Sequential roadmap execution without manual pause.
- Mandatory `git commit` and `git push` after every major feature.
- Recursive submodule updates and intelligent branch merging.

## 2. Repository Synchronization Protocol (RSP)
At the start of every session, the agent must perform:
1. **Fetch & Pull:** Sync with upstream and origin.
2. **Intelligent Merge:** Reconcile local feature branches (especially those under `github.com/robertpelloni`) into `main`.
3. **Submodule Sanitization:** Update all nested submodules to their latest tracking commits.

## 3. Documentation Governance
All repository state changes must be reflected in the core documentation suite:
- `VERSION.md`: Single source of truth for the global version string.
- `CHANGELOG.md`: Detailed log of features, security hardening, and refactors.
- `ROADMAP.md`: Long-term structural milestones.
- `TODO.md`: Immediate granular tasks and bug fixes.
- `MEMORY.md`: Architectural observations and design preferences.
- `HANDOFF.md`: Session summary for successor model resumption.

## 4. UI Quality & Wiring Standard
- Every backend feature **must** be wired to a corresponding UI component.
- Interactive forms must include clear labels, descriptions, and tooltips.
- HTMX is the preferred standard for asynchronous updates (polling and partials).

## 5. Security & Infrastructure Standard
- **Secrets Management:** Binary assets and sensitive logs are excluded from Git tracking via `.gitignore`.
- **Database Resilience:** Automated backups via `backup_job.py` and integrity testing are mandatory.
- **Log Hygiene:** Use `RotatingFileHandler` for all primary service logs (`server.log`, `health_monitor.log`, etc.).

## 6. Verification Workflow
1. **Backend:** Execution of all relevant integration and unit tests via `pytest`.
2. **Frontend:** Visual verification using Playwright scripts with screenshots saved to `/home/jules/verification/`.
3. **Audit:** All administrative actions must be logged in the `AuditLog` for security visualization.
