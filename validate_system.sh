#!/usr/bin/env bash

# StepManiaX B2B Platform - End-to-End Validation Suite
# This script automates the full initialization and testing flow as per GOVERNANCE.md

set -e

echo "--- Initializing System State ---"
# 1. Reset Database
rm -f crm.db
python3 populate_test_data.py

# 2. Run Backend Integration Tests
echo "--- Running Backend Integration Tests ---"
PYTHONPATH=. pytest tests/integration/test_checkin.py \
                   tests/integration/test_enterprise_api.py \
                   tests/integration/test_live_ops.py \
                   tests/integration/test_mfa_api.py \
                   tests/test_backup.py \
                   tests/test_restoration.py

# 3. Run Frontend UI Tests (Playwright)
echo "--- Running Frontend UI Tests ---"
# Ensure no server is running
kill $(lsof -t -i :5000) 2>/dev/null || true

# Repopulate DB for UI tests (since backend tests may have cleared it)
rm -f crm.db
python3 populate_test_data.py
# Ensure the database file and directory are writable by the server process
chmod 666 crm.db
chmod 777 .

# Start the server in the background
FLASK_DEBUG=false flask run --port 5000 > logs/server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready
sleep 5

# Execute Playwright tests
if PYTHONPATH=. pytest tests/integration/test_ui.py; then
    echo "✅ UI Tests Passed"
else
    echo "❌ UI Tests Failed"
    kill $SERVER_PID
    exit 1
fi

# Clean up
kill $SERVER_PID
echo "--- Validation Suite Complete: 100% Success ---"
