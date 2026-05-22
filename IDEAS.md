# Ideas

## Refactoring & Architecture
- **API Integration:** Integrate with a B2B data API (like Apollo.io or Hunter.io) to automate email discovery once Franchise Groups are identified.
- **CRM Lite:** Transition `LEADS.md` or `kpi-tracker.md` into a more robust local database (SQLite) to track the outreach funnel (Sent -> Opened -> Replied -> Meeting).

## Feature Expansions
- **Dynamic Pitch Generator:** Create a script that populates the `pitch-deck.md` with location-specific data (e.g., "Grand Fitness Partners' California locations").
- **ROI Calculator:** Add a spreadsheet or script that calculates potential ROI based on member retention lift and increased visit frequency.
- **Video Demo:** Include a script or instructions for generating a high-quality "commercial" video of StepManiaX in a gym setting (non-arcade).

## Language Porting
- Port the lead generation logic to Go or Rust if performance becomes a bottleneck for wide-scale scraping (unlikely for this specific use case but good for "autonomous agent" case study).
