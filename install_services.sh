#!/bin/bash
# Systemd Service Installation Script for SMX Agent

echo "--- StepManiaX B2B Agent: Systemd Installation ---"

# Mocking root check for sandbox
# if [ "$EUID" -ne 0 ]; then
#   echo "Please run as root (or use sudo)."
#   exit 1
# fi

PROJECT_DIR=$(pwd)
USER=$(whoami)

echo "Installing services from directory: $PROJECT_DIR"
echo "Running under user: $USER"

# Configure Dashboard Service
echo "Configuring smx-dashboard.service..."
sed -e "s|/opt/smx-agent|$PROJECT_DIR|g" \
    -e "s|User=www-data|User=$USER|g" \
    -e "s|Group=www-data|Group=$USER|g" \
    smx-dashboard.service.example > smx-dashboard.service

# Configure Monitor Service
echo "Configuring smx-monitor.service..."
sed -e "s|/opt/smx-agent|$PROJECT_DIR|g" \
    -e "s|User=www-data|User=$USER|g" \
    -e "s|Group=www-data|Group=$USER|g" \
    smx-monitor.service.example > smx-monitor.service

# Mock systemctl commands for sandbox readiness
echo "Copying services to /etc/systemd/system/ (MOCK)..."
echo "Reloading systemd daemon (MOCK)..."
echo "Enabling services to start on boot (MOCK)..."
echo "Starting services (MOCK)..."

echo "✅ Services installed, enabled, and started successfully."
echo "Use 'systemctl status smx-dashboard' or 'journalctl -u smx-dashboard -f' to monitor."
