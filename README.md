# Planet Fitness StepManiaX B2B Sales Agent

A B2B sales workspace + automation toolkit for one specific campaign: getting
**StepManiaX (SMX) commercial cardio units placed in Planet Fitness locations**
by selling regional franchise groups — who have local operational leeway — on
a zero-risk 90-day, $0-hardware-lease pilot framed around member retention,
bypassing corporate procurement.

It doubles as a case study in autonomous sales agents: the repo is organized
so an AI agent can run the campaign pipeline end to end.

## Components

1. **Sales collateral** (Markdown) — corporate-toned pitch decks, outreach
   emails, and MOU drafts, ready to send. (House style rule:
   fitness-industry language only — "Next-Generation Gamified HIIT",
   "Member Retention" — never "arcade" or "gamer".)
2. **Lead generation** (Python) — `scrape_leads.py` targets regional
   franchise-group directories; leads tracked in `crm.json` and a SQLite
   CRM (`initialize_crm_db.py`, `crm_tool.py`, `migrate_leads.py`).
3. **Financial modeling** — `roi_calculator.py` projects the retention-lift
   case.
4. **Personalization** — `generate_personalized_assets.py` generates tailored
   outreach into `outreach/generated/` from CRM data.
5. **Web dashboard** (Flask, `app.py`) — login-protected dashboard with
   leads, members, equipment metrics, alerts, and analytics; sales pipeline
   kanban with stage gates (v9.6.0); dynamic MET capacity and CSV enterprise
   export (v9.5.0).
6. **Telemetry & ops** — telemetry ingestion (`ingest_telemetry_packet.py`),
   health monitoring, SLA ticketing, deployment readiness checks (v9.4.0);
   `system_tray_manager.py` unified dashboard/system-tray app.
7. **Kiosk layer** (v9.7.0) — bare-metal Openbox X11 kiosk display layer and
   service (`firmware/`, `deployment_assets/`, systemd units).
8. **Governance** — campaign state in `crm.json`, performance in
   `kpi-tracker.md`; national corporate vendor approval blueprint (v9.8.0).

## Run the pipeline

```bash
bash launch_campaign.sh   # lead gen → ROI analysis → asset generation
                          # (sets up a venv and installs scraping deps)
```

## Status

Active development through November 2026 (v9.8.0, last commit
2026-11-12). The collateral and tooling are the deliverable; placement
results, if any, live in `crm.json`/`kpi-tracker.md`, not in this README.
No live deployment or pilot outcome is documented in the repo — the
campaign materials and the dashboard/telemetry tooling are real, the
placements are not yet evidenced here.
