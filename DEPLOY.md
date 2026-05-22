# Deployment & Setup Instructions

## Overview
The StepManiaX B2B Sales Agent consists of a document suite for collateral and a Python-based automation stack for lead generation, CRM management, and performance monitoring.

## 1. Automation Environment Setup
The project uses a unified execution pipeline to manage dependencies and virtual environments.

1. **System Requirements:** Python 3.8+, SQLite3, Bash.
2. **One-Button Setup:**
   ```bash
   bash launch_campaign.sh
   ```
   This script will:
   - Create a virtual environment (`venv/`).
   - Install dependencies from `requirements.txt`.
   - Initialize the CRM database (`crm.db`) if it doesn't exist.
   - Run the automated lead generation and asset production sequence.

## 2. Web Dashboard Deployment
The Flask-based monitoring dashboard provides a real-time view of the sales funnel and equipment telemetry.

1. **Start the Dashboard:**
   ```bash
   python app.py
   ```
2. **Access:** Navigate to `http://localhost:5000` in your browser.
3. **User Management:** Create a dashboard user via the CRM CLI:
   ```bash
   python crm_tool.py create-user <username> <password>
   ```

## 3. CRM Management (CLI)
Interact with the lead database directly via `crm_tool.py`:
- `list`: View all leads and their current status.
- `add`: Manually add a new franchise group.
- `log-outreach`: Record a contact attempt and update follow-up counters.
- `analytics`: View aggregated ROI potential across the portfolio.

## 4. Secrets Management
The agent uses a `.env` file for sensitive configurations (e.g., LinkedIn tokens or Dashboard secret keys).
1. Copy `.env.example` to `.env`.
2. Populate the required variables.
3. Never commit the `.env` file to version control.

## 5. Directory Structure
- `/outreach`: Tailored sales scripts and follow-up templates.
- `/templates`: HTML layouts for the web dashboard.
- `crm.db`: SQLite database (Auto-generated).
- `analytics.py`: Core logic for LTV/ROI calculations.
