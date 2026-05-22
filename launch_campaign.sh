#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "==========================================================="
echo "   StepManiaX B2B Campaign Launch Sequence (v1.4.0)"
echo "==========================================================="

# 1. Database Initialization & Lead Migration
echo "[1/5] Initializing CRM Database..."
python3 initialize_crm_db.py

# 2. Lead Generation Phase
echo "[2/5] Starting Regional Lead Discovery..."
bash pipeline.sh

# 3. Financial Modeling Phase
echo "[3/5] Executing ROI Projections..."
python3 roi_calculator.py

# 4. Asset Generation Phase
echo "[4/5] Generating Personalized Sales Collateral from CRM DB..."
python3 generate_personalized_assets.py

# 5. Final Verification
echo "[5/5] Finalizing Campaign Assets..."
ls -R outreach/generated/

echo "==========================================================="
echo "   Campaign Launch Sequence Complete."
echo "   Use 'python3 crm_tool.py list' to view targets."
echo "==========================================================="
