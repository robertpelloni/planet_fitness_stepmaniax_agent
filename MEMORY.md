# Memory

## Architectural Observations
- **Hybrid Pillar Strategy:** The project architecture consists of three pillars: Markdown B2B Collateral, Python Lead Generation scripts, and a Flask-based Web Monitoring Dashboard.
- **Data Persistence:** Transitioned from flat JSON files to a structured SQLite database (`crm.db`) for scalable lead tracking and equipment telemetry.
- **Centralized Analytics:** Financial modeling (ROI/LTV) is consolidated in `analytics.py` to ensure consistency across CLI tools, automated asset generation, and the web dashboard.
- **The "Rogue Franchise Loophole":** This core strategic driver targets regional decision-makers instead of the corporate office, exploiting the operational autonomy of franchise owners.

## Discovered Traits
- **Franchise Site Autonomy:** Franchise Groups maintain independent web presences, which are rich sources of executive bios and operational regions often missing from corporate portals.
- **Pathing Standardization:** Use absolute path resolution for `crm.db` to prevent context issues when executing scripts from different directory levels.
- **Tone Consistency:** High-level stakeholders respond better to "Retention Lift" and "Gamified HIIT" than "Engagement" or "Exergaming."

## Design Preferences
- **Corporate Professionalism:** Maintain a professional B2B tone; strictly avoid "arcade" or "video game" terminology in all user-facing assets.
- **Single Source of Truth:** `VERSION.md` is the authoritative source for versioning.
- **Document-First Development:** Core strategies and scripts must be documented in Markdown before or alongside implementation.
- **Autonomous Ready:** Tools should be designed for one-button execution (e.g., `launch_campaign.sh`).
