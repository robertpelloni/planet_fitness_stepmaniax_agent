# StepManiaX B2B Agent: Production Deployment Guide

## Overview
This document details the professional deployment of the StepManiaX B2B Management platform using Gunicorn and systemd for maximum reliability and uptime.

## 1. Prerequisites
- Linux Server (Ubuntu 22.04 LTS recommended)
- Python 3.8+
- Nginx (for Reverse Proxy)

## 2. Standard Installation
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/robertpelloni/planet-fitness-smx-agent.git /opt/smx-agent
   cd /opt/smx-agent
   ```
2. **Setup Environment:**
   ```bash
   bash pipeline.sh
   cp .env.example .env
   # Edit .env with secure SECRET_KEY and SMX_API_KEY
   ```
3. **Run Readiness Check:**
   ```bash
   ./production_check.sh
   ```

## 3. Production Serving (Gunicorn)
The platform uses Gunicorn as a high-performance WSGI server.
- **Config:** `gunicorn_config.py`
- **Command:** `gunicorn --config gunicorn_config.py app:app`

## 4. Background Monitoring (Health Monitor)
The `health_monitor.py` script runs as a continuous service, scanning equipment metrics and firing real-time alerts.

## 5. Systemd Service Integration
For automatic startup and crash recovery, install the provided service templates.

1. **Install Web Dashboard Service:**
   ```bash
   sudo cp smx-dashboard.service.example /etc/systemd/system/smx-dashboard.service
   # Edit user/path in /etc/systemd/system/smx-dashboard.service
   sudo systemctl enable --now smx-dashboard
   ```
2. **Install Health Monitor Service:**
   ```bash
   sudo cp smx-monitor.service.example /etc/systemd/system/smx-monitor.service
   sudo systemctl enable --now smx-monitor
   ```

## 6. Nginx Reverse Proxy (Example)
```nginx
server {
    listen 80;
    server_name smx-dashboard.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 7. Operational Commands
- **Check Logs:** `journalctl -u smx-dashboard -f`
- **Restart Services:** `sudo systemctl restart smx-dashboard smx-monitor`
- **DB Maintenance:** Use `crm_tool.py` for user provisioning and lead management.
- **Enterprise Data Exchange:** (v4.8.0)
  - `GET /api/v1/enterprise/export`: Pull aggregated fleet telemetry, engagement, and sentiment.
  - `GET /api/v1/enterprise/leads`: Synchronize lead portfolio with corporate CRM.
- **Hardware Check-in Integration:** (v5.2.0)
  - `POST /api/v1/telemetry/check-in`: Process secure NFC/Biometric check-ins.

## 8. Multi-Factor Authentication & API Governance (v4.9.0)
### API Key Governance
API keys are now generated per-user. Users can rotate their keys in the **Settings > Enterprise Access** section. The global `SMX_API_KEY` in `config.py` is deprecated.

### MFA Enrollment
Management accounts should enable TOTP-based 2FA. Enrollment is available in **Settings > Enterprise Access**. Once enabled, a verification code is required during the login sequence.

## 9. Integration Testing (v4.5.0)
To verify UI integrity and core user flows, execute the Playwright integration suite:
```bash
pytest tests/integration/test_ui.py
```
Note: Ensure the development server is running on port 5000 before executing tests.

## 10. Phase 14: Custom Hardware & Telemetry Deployment Checklist (v9.2.0)
With the transition to custom 9-panel hardware and the `FitnessDifficulties.lua` real-time WebSocket integration, additional configuration is required to proxy biomechanical telemetry to the backend.

### 10.1 Nginx WebSocket Proxy Configuration
The new `/ws/telemetry` endpoint requires specific Nginx directives to upgrade HTTP requests to WebSocket connections. Update your Nginx configuration:

```nginx
server {
    listen 80;
    server_name smx-dashboard.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Phase 14: Real-time Biomechanical Telemetry
    location /ws/telemetry {
        proxy_pass http://127.0.0.1:5000/ws/telemetry;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Increase timeouts for long-running Marathon sessions
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

### 10.2 Service Configuration for Health Monitor
Ensure the `health_monitor.py` daemon is active to validate hardware telemetry offline states and automate Service Dispatch ticketing (simulate Andamiro SLAs). Use the provided `smx-monitor.service.example` file.

1. **Verify Configuration**:
   ```bash
   cat /etc/systemd/system/smx-monitor.service
   ```
   *(Ensure the working directory points to your production folder, e.g., `/opt/smx-agent`, and Python executes from the `venv/bin/python3`)*

2. **Reload and Restart**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart smx-monitor
   sudo systemctl status smx-monitor
   ```

3. **Verify WebSocket Sync**:
   Execute the `ws_client_simulator.py` script locally to confirm the bi-directional handshake against the telemetry endpoints.
