#!/usr/bin/env bash
# StepManiaX B2B Lead Generation & Operations Orchestrator (v9.3.0)
# Consolidated pipeline for scraping leads, generating personalized outreach,
# auditing system readiness, and launching sales campaigns.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "==========================================================="
echo "   StepManiaX B2B Lead Generation & Operations Pipeline"
echo "==========================================================="

# 1. Environment & Python Validation
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 could not be found. Please install Python 3.10+."
    return 1 2>/dev/null || exit 1
fi
echo "[OK] Python environment verified."

# 2. Database Initialization
if [ ! -f "crm.db" ]; then
    echo "[INFO] Initializing CRM database from schema..."
    python3 initialize_crm_db.py
else
    echo "[OK] Database crm.db exists."
fi

# 3. Optional Lead Scrape Step
if [ "$1" == "--scrape" ]; then
    echo "[INFO] Running automated franchise lead scraper..."
    python3 scrape_leads.py
fi

# 4. Generate Personalized Outreach Assets
echo "[INFO] Generating personalized sales assets & cadences..."
python3 generate_personalized_assets.py

# 5. System Health & Production Audit
echo "[INFO] Performing production readiness audit..."
bash production_check.sh

echo "==========================================================="
echo " Pipeline execution completed successfully."
echo " Launch the Operations Center via: ./system_tray_manager.py --start"
echo "==========================================================="
