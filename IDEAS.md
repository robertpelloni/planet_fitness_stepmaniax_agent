# Ideas

## Refactoring & Architecture
- **Multi-Tenant Dashboard:** Refactor `app.py` to support multi-tenant views, allowing different regional managers to see only their specific club data.
- **Headless Browser Integration:** Replace the basic `requests`-based scraper with Playwright or Selenium to handle JavaScript-heavy franchise portals and executive directories.
- **Webhook Alerts:** Implement Discord/Slack webhooks for the CRM to notify the agent of new leads or high-priority follow-up triggers.

## Feature Expansions
- **Automated LinkedIn Outreach:** Integrate with a headless browser to automate personalized connection requests using the `outreach-script.md` logic.
- **Live ROI Dashboard for Leads:** Create a "public" (password-protected) version of the dashboard that a lead can visit to see live ROI projections based on their specific number of clubs.
- **Equipment Health API:** Mock or integrate a real API for SMX machines to populate the dashboard with actual uptime data and maintenance alerts.

## Strategic Pivots
- **Secondary Brands target:** Adapt the collateral for other "HVLP" (High Value Low Price) gym chains like Crunch Fitness or YouFit, using the same "Rogue Franchise" methodology.
- **Insurance Reimbursement Pitch:** Research and add a "Silver Sneakers" or insurance wellness pitch component to the ROI model, showing how SMX can attract older demographics or specialized wellness subsets.
