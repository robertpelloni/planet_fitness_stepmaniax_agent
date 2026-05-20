# Project Architecture, Patterns, and Decisions Summary

## 1. Repository Architecture & Purpose
This project operates as a hybrid **B2B sales workspace and data-gathering utility**. The primary architecture consists of structured Markdown documents designed to manage a multi-phase sales pipeline. The target is regional Planet Fitness Franchise Groups to deploy StepManiaX (SMX) commercial cardio units. Secondary to the documentation, it contains Python-based utility scaffolding (`scrape_leads.py`) for automated B2B lead generation.

## 2. Core Strategic Decisions
* **The "Rogue Franchise" Loophole:** The foundational sales strategy bypasses the impenetrable Planet Fitness corporate procurement process and exclusively targets regional Franchise Groups that possess local operational leeway.
* **Zero-Risk Pilot Framework:** The core B2B offer is a 90-day, $0 hardware lease trial designed to track member retention. This mitigates gym owner risk, solves immediate "maintenance/noise" objections upfront, and serves as a trigger for larger regional commercial contracts.

## 3. Communication Patterns & Terminology
All generated assets (pitch decks, outreach emails, MOUs) and internal documentation strictly adhere to a corporate fitness tone to align with gym executive expectations:
* **Banned Terminology:** "Arcade," "video game," "gamer," and typical rhythm game jargon.
* **Preferred Terminology:** "Next-Generation Gamified HIIT," "Interactive Cardio," "Member Retention," "Low-Impact Cardio," and "Commercial-Grade Kiosk."
* **Tone:** Professional, B2B sales-oriented, highly focused on ROI, member retention, liability mitigation, and cardio floor etiquette.

## 4. Documentation & State Management Patterns
The repository relies on standard open-source documentation practices to manage its workflow:
* **Strategic Foundation:** `VISION.md` and `ROADMAP.md` define the long-term goals and the 4-Phase execution pipeline.
* **Project Management & Handoff:** `TODO.md` tracks actionable priorities. `HANDOFF.md` acts as a rigorous state-tracker, recording completed work per cycle, missing files, test status, dependencies, and immediate next tasks/blockers.
* **Campaign Tracking:** `kpi-tracker.md` is utilized to monitor human and agent execution volume (Leads Generated, Outreach Volume, Discovery Calls).
* **AI Instruction Framework (DRY):** A central `AGENTS.md` file dictates universal AI rules (tone, versioning, secrets management), with model-specific files inheriting from it to keep behavioral instructions DRY.
* **Versioning:** `VERSION.md` is strictly maintained as the single source of truth (currently at `v0.1.7`), ensuring alignment with `CHANGELOG.md` and commit messages.

## 5. Security & Execution Boundaries
* **Secrets Management:** A strict rule prevents committing API keys, credentials, or proprietary URLs. The project relies on `.env.example` placeholders, and operators must define secrets locally in an untracked `.env` file (enforced by `.gitignore`).
* **Environment Integrity:** Python dependencies are tracked strictly in `requirements.txt`. The `.gitignore` file enforces that no compiled binaries (`__pycache__`) or local virtual environments (`venv`) are tracked.
* **Autonomous Stop Conditions:** The agent is trained to proactively halt cycles and mark tasks as "BLOCKED" if a task becomes ambiguous, requires manual external human action, or requires unavailable credentials/API keys (such as LinkedIn Sales Navigator credentials). This ensures the agent does not hallucinate data for Phase 2 tasks.