#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "==========================================================="
echo "   StepManiaX B2B Lead Generation Pipeline Setup"
echo "==========================================================="

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 could not be found. Please install Python 3.8+ to run the scraper."
    exit 1
fi
echo "[OK] Python 3 is installed."

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "[INFO] Virtual environment not found. Creating 'venv'..."
    python3 -m venv venv
else
    echo "[OK] Virtual environment 'venv' already exists."
fi

# 3. Activate Virtual Environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# 4. Install Dependencies
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing dependencies from requirements.txt..."
    pip install -r requirements.txt --quiet
    echo "[INFO] Installing Playwright browsers..."
    playwright install --with-deps chromium
    echo "[OK] Dependencies installed."
else
    echo "[WARNING] requirements.txt not found. Skipping dependency installation."
fi

# 5. Check for Secrets / .env configuration
if [ ! -f ".env" ]; then
    echo "-----------------------------------------------------------"
    echo "[WARNING] .env file not found!"
    echo "To run the scraper against authenticated targets (e.g., LinkedIn),"
    echo "you must copy .env.example to .env and configure your secrets."
    echo ""
    echo "Would you like to run the scraper anyway? (It will likely fail if it requires auth)"
    read -p "Continue? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Pipeline execution aborted by user. Please configure .env and try again."
        deactivate
        exit 0
    fi
else
    echo "[OK] .env file found."
fi

# 6. Run the Scraper
echo "==========================================================="
echo "   Executing Lead Scraper..."
echo "==========================================================="
python3 scrape_leads.py

echo "==========================================================="
echo "   Pipeline Complete."
echo "==========================================================="

deactivate