# Project Architecture, Patterns, and Decisions Summary

## 1. Project Nature & Architecture
This repository functions exclusively as a **B2B sales and business development workspace**. There is no traditional executable software code. The architecture is composed of interconnected Markdown documents organized to manage a multi-phase sales pipeline, specifically targeting regional Planet Fitness Franchise Groups to deploy StepManiaX (SMX) commercial units.

## 2. Core Strategic Decisions
* **The "Rogue Franchise" Loophole:** A central strategic decision to bypass the impenetrable Planet Fitness corporate procurement process and exclusively target regional Franchise Groups with local operational leeway.
* **Zero-Risk Pilot Framework:** The core sales offer revolves around proposing a 90-day, $0 hardware lease trial to track member retention and engagement metrics to prove value before attempting larger procurement contracts.

## 3. Communication Patterns & Terminology
All assets and AI-generated content adhere to a strict corporate fitness tone:
* **Banned Terminology:** "Arcade", "video game", "gamer".
* **Preferred Terminology:** "Next-Generation Gamified HIIT", "Interactive Cardio", "Member Retention", "Low-Impact Cardio", "Commercial-Grade Kiosk".
* **Tone:** Professional, B2B sales-oriented, focusing on ROI, member retention, and gym floor etiquette.

## 4. Documentation & File Structure Patterns
The repository uses standard open-source documentation file structures, adapted for business development:
* **Strategic Foundation:** `VISION.md` and `ROADMAP.md` define the long-term goal and the 4-Phase pipeline.
* **Project Management:** `TODO.md` tracks actionable priorities, and `HANDOFF.md` rigorously records the current project state, completed work per cycle, missing files, and next immediate tasks.
* **Assets / Deliverables:** Tangible business collateral is created as separate markdown files, such as `pitch-deck.md` (Phase 1) and `outreach-script.md` (Phase 3).
* **AI Instruction Framework:** A central `AGENTS.md` file dictates universal rules (tone, versioning, secrets), with model-specific files (`CLAUDE.md`, `GPT.md`, etc.) inheriting from it, keeping behavioral instructions DRY (Don't Repeat Yourself).

## 5. Versioning & Deployment Decisions
* **Single Source of Truth:** `VERSION.md` is strictly maintained as the single source of truth for the project version (currently at `0.1.2`), which must align with `CHANGELOG.md` and commit messages. 
* **Deployment & Testing:** As there is no executable code, deployment and testing are currently non-applicable. Any future scripts must document their setup in `DEPLOY.md`.
* **Secrets Management:** A strict rule prevents committing API keys. Any future secrets must use `.env.example` placeholders, as noted in `DEPLOY.md` and `AGENTS.md`.