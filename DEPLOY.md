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
