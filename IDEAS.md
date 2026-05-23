# Ideas

## Refactoring & Architecture
- **Headless Browser Integration:** Replace the basic `requests`-based scraper with Playwright or Selenium to handle JavaScript-heavy franchise portals and executive directories.
- **WebSocket Integration:** Transition from HTMX polling to WebSockets for sub-second telemetry updates in the Staff Portal.
- **Microservices Migration:** Decouple the telemetry ingestion API into a standalone Go or Rust service to handle ultra-high frequency metric streams.

## Feature Expansions
- **Automated LinkedIn Outreach:** Integrate with a headless browser to automate personalized connection requests using the `outreach-script.md` logic.
- **Live ROI Dashboard for Leads:** Create a "public" (password-protected) version of the dashboard that a lead can visit to see live ROI projections based on their specific number of clubs.
- **AI-Powered Lead Scoring:** Implement a machine learning model to rank leads based on group size, regional saturation, and past interaction sentiment.

## Strategic Pivots
- **Secondary Brands target:** Adapt the collateral for other "HVLP" (High Value Low Price) gym chains like Crunch Fitness or YouFit, using the same "Rogue Franchise" methodology.
- **Insurance Reimbursement Pitch:** Research and add a "Silver Sneakers" or insurance wellness pitch component to the ROI model, showing how SMX can attract older demographics or specialized wellness subsets.
- **Asset Management as a Service:** Pivot the dashboard as a standalone SaaS for gym franchisees to manage *all* their cardio equipment telemetry, not just SMX.
