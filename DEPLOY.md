# Deployment Instructions

As this project currently consists of B2B sales collateral and documentation, there is no software deployment process.

If software scripts (e.g., for data scraping or CRM integration) are added in the future, document their setup here.

## Secrets Management
If API keys or secrets become necessary, they must never be hard-coded or committed.
1. Create a `.env.example` file with placeholder variables.
2. Instruct users to copy it to `.env` and fill in their credentials locally.