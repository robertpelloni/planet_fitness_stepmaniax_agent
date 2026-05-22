#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "==========================================================="
echo "   StepManiaX B2B Campaign Launch Sequence (v1.0.0)"
echo "==========================================================="

# 1. Lead Generation Phase
echo "[1/4] Starting Regional Lead Discovery..."
bash pipeline.sh

# 2. Financial Modeling Phase
echo "[2/4] Executing ROI Projections..."
python3 roi_calculator.py

# 3. Asset Generation Phase
echo "[3/4] Generating Personalized Sales Collateral..."
python3 generate_personalized_assets.py

# 4. Final Verification
echo "[4/4] Finalizing Campaign Assets..."
ls -R outreach/generated/

echo "==========================================================="
echo "   Campaign Launch Sequence Complete."
echo "   Ready for Outreach Execution."
echo "==========================================================="
