#!/bin/bash
# Production Readiness Check for SMX Agent

echo "--- SMX Agent Production Readiness Check ---"

# 1. Environment Check
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file missing. Create one from .env.example."
    exit 1
fi

# 2. Database Check
if [ ! -f "crm.db" ]; then
    echo "⚠️ WARNING: crm.db not found. Initializing..."
    flask init-db
fi

# 3. Dependency Check
if ! pip freeze | grep -q "gunicorn"; then
    echo "⚠️ WARNING: gunicorn not installed. Installing..."
    pip install gunicorn
fi

# 4. API Key Check
if ! grep -q "SMX_API_KEY" .env; then
    echo "❌ ERROR: SMX_API_KEY not defined in .env."
    exit 1
fi

echo "✅ Readiness check passed. Ready for deployment."
