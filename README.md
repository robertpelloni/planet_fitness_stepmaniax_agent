# Planet Fitness StepManiaX B2B Sales Agent

A B2B sales workspace + automation toolkit for one specific campaign: getting **StepManiaX (SMX) commercial cardio units placed in Planet Fitness locations** by selling regional franchise groups — who have local operational leeway — on a zero-risk 90-day, $0-hardware-lease pilot framed around member retention, bypassing corporate procurement.

It doubles as a case study in autonomous sales agents: the repo is organized so an AI agent can run the campaign pipeline end to end.

## Components

1. **Sales collateral** (Markdown) — corporate-toned pitch decks, outreach emails, and MOU drafts, ready to send. (House style rule: fitness-industry language only — "Next-Generation Gamified HIIT", "Member Retention" — never "arcade" or "gamer".)
2. **Lead generation** (Python) — `scrape_leads.py` targets regional franchise-group directories
3. **Financial modeling** — `roi_calculator.py` projects the retention-lift case
4. **Personalization** — `generate_personalized_assets.py` generates tailored outreach into `outreach/generated/` from CRM data
5. **Governance** — campaign state in `crm.json`, performance in `kpi-tracker.md`

## Run the pipeline

```bash
bash launch_campaign.sh   # lead gen → ROI analysis → asset generation
                          # (sets up a venv and installs scraping deps)
```

## Status

A real campaign workspace from Robert Pelloni's dance-game/fitness work (alongside `fcdm`, his Fitness Center Dance Machine). The collateral and tooling are the deliverable; placement results, if any, live in `crm.json`/`kpi-tracker.md`, not in this README.
