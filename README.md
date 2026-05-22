# Planet Fitness StepManiaX B2B Sales Agent

This repository serves as a hybrid **B2B sales workspace and automated data-gathering utility**. Its ultimate purpose is to act as a case study in autonomous AI agents, enabling an AI (like Hermes-Agent running GPT-5.5) to persuade regional Planet Fitness Franchise Groups to deploy StepManiaX (SMX) commercial cardio units—without further human input or intervention.

## Project Vision & Architecture

The overarching strategy relies on the **"Rogue Franchise Loophole"**: bypassing the rigid, exclusive corporate procurement contracts of Planet Fitness by directly targeting regional Franchise Group owners who possess local operational leeway. The core offering is a **Zero-Risk Pilot Framework**—a 90-day, $0 hardware lease trial designed to track member retention and serve as a trigger for larger commercial contracts.

To execute this, the project architecture is split into three components:
1. **Markdown Sales Collateral:** Professionally formatted, strictly corporate-toned B2B assets (pitch decks, outreach emails, MOUs) ready for dispatch.
2. **Python Lead Generation:** Automated scripting frameworks to scrape B2B directories and identify high-value regional targets.
3. **Sales Automation & Analytics:** Tools to model ROI (`roi_calculator.py`) and generate personalized outreach assets (`generate_personalized_assets.py`) dynamically from CRM data.

*All generated content rigorously adheres to a strict corporate fitness tone. Words like "arcade" or "gamer" are banned in favor of "Next-Generation Gamified HIIT" and "Member Retention."*

## Autonomous Agent Workflow: How to Use

This repository is optimized for autonomous execution. To launch the complete B2B campaign pipeline (Lead Gen -> ROI Analysis -> Asset Generation), execute:

```bash
bash launch_campaign.sh
```

### Components of the Campaign:
- **Lead Discovery:** `scrape_leads.py` targets regional franchise group directories.
- **Financial Modeling:** `roi_calculator.py` projects membership retention lift benefits.
- **Personalization:** `generate_personalized_assets.py` creates tailored emails in `outreach/generated/`.
- **Governance:** State is tracked in `crm.json` and performance in `kpi-tracker.md`.

This script will:
1. Verify Python 3 installation.
2. Build and activate a safe Python virtual environment (`venv`).
3. Install the required web scraping dependencies (`requests`, `beautifulsoup4`).
4. Check for the required `.env` secrets file (to prevent unauthenticated failure against directories like LinkedIn).
5. Execute the `scrape_leads.py` utility.

## The 4-Phase Standard Operating Procedure (SOP)

### Phase 1: Asset Preparation & Collateral Assembly
- Assemble the "Interactive Cardio" Pitch Deck (`pitch-deck.md`).
- Secure real-world hardware dimensions and manufacturer specifications.

### Phase 2: Lead Generation & Target Mapping
- Utilize `scrape_leads.py` to identify local franchise powerhouses in target regions (e.g., Michigan/Midwest).
- Extract contact information for Chief Operating Officers, VPs of Operations, or Regional Franchise Owners.

### Phase 3: Outreach & Objection Handling
- Execute a targeted cold-contact campaign using the established email templates and objection-handling scripts (`outreach-script.md`).
- Focus entirely on retention metrics, low impact, and gym floor etiquette.

### Phase 4: Contract Negotiation & Deal Closure
- Draft and negotiate the 90-day Pilot Memorandum of Understanding (`pilot-mou.md`).
- Utilize pilot engagement data to trigger the "Land and Expand" clause for regional procurement.

## Agent Tracking & KPIs
To ensure the commercial placement campaign is executing effectively, agents must track weekly metrics in the `kpi-tracker.md` file, logging Leads Generated, Outreach Volume, and Discovery Calls.

## Secrets Management
If API keys, authentication cookies, or secrets become necessary for scraping (e.g., LinkedIn Sales Navigator tokens), they must **never** be hard-coded or committed. Refer to `DEPLOY.md` and `.env.example` for secure local configuration.