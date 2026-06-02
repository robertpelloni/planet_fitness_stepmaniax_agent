import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import analytics
from notifications import send_notification
from app import app, db
from models import EquipmentMetric, Alert, AutomationHeartbeat, ServiceDispatch, Lead

# --- Log Rotation Setup ---
if not os.path.exists('logs'):
    os.mkdir('logs')

logger = logging.getLogger('health_monitor')
handler = RotatingFileHandler('logs/health_monitor.log', maxBytes=10240, backupCount=10)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def monitor_health():
    """
    Scans equipment metrics and generates alerts for operational anomalies.
    Refactored to use SQLAlchemy ORM (v7.7.0) to prevent SQLite concurrency issues.
    """
    with app.app_context():
        logger.info("Starting Health Monitor...")

        # Lead Cadence Processing (v6.6.0 Orchestration)
        from launch_outreach import launch_outreach
        try:
            launch_outreach()
        except Exception as e:
            logger.error(f"Error in launch_outreach() during health monitor cycle: {e}")

        # 1. Fetch all metrics
        units = EquipmentMetric.query.all()

        for unit in units:
            # A. Uptime check (Warning for < 98%)
            if unit.uptime_percent < 98.0 and unit.uptime_percent >= 95.0:
                generate_alert("Warning", f"Degraded performance on {unit.equipment_name} at {unit.location}: {unit.uptime_percent}%", unit.id)

            # B. Uptime check (Critical for < 95%)
            elif unit.uptime_percent < 95.0:
                generate_alert("Critical", f"Low Uptime detected on {unit.equipment_name} at {unit.location}: {unit.uptime_percent}%", unit.id)

            # C. Session variance check (Warning if avg session is < 5 mins)
            if unit.total_scans > 10 and unit.avg_session_duration < 5.0:
                 generate_alert("Warning", f"Short session duration anomaly on {unit.equipment_name} at {unit.location}: {unit.avg_session_duration}m avg.", unit.id)

            # D. Heartbeat / Offline Check (Critical if no heartbeat > 10 mins)
            if unit.last_heartbeat:
                last_hb = datetime.strptime(unit.last_heartbeat, "%Y-%m-%d %H:%M:%S")
                diff = (datetime.now() - last_hb).total_seconds()
                if diff > 600: # 10 minutes
                    generate_alert("Critical", f"UNIT OFFLINE: {unit.equipment_name} at {unit.location} has not reported a heartbeat for > 10 minutes.", unit.id)
            else:
                generate_alert("Warning", f"Heartbeat Missing: {unit.equipment_name} at {unit.location} has never reported a heartbeat.", unit.id)

            # E. Predictive Health Calculation (v3.7.0)
            # Create a dict from the unit object for analytics logic
            unit_data = {
                'total_sessions': unit.total_sessions,
                'uptime_percent': unit.uptime_percent,
                'total_scans': unit.total_scans,
                'avg_session_duration': unit.avg_session_duration
            }
            unit.predictive_health_score = analytics.calculate_predictive_health_score(unit_data)

        # Weekly Pilot Summary Generation (v6.2.0)
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 23:
            week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

            heartbeat = AutomationHeartbeat.query.filter_by(task_name='Weekly Summary Trigger').first()

            if not heartbeat or heartbeat.last_run[:10] < week_start:
                logger.info(f"Executing Weekly Pilot Summary generation for week starting {week_start}...")
                active_pilots = Lead.query.filter(Lead.status.contains('Pilot')).all()
                from report_generator import generate_weekly_summary
                for pilot in active_pilots:
                    generate_weekly_summary(pilot.id)

                if not heartbeat:
                    heartbeat = AutomationHeartbeat(task_name='Weekly Summary Trigger')
                    db.session.add(heartbeat)

                heartbeat.last_run = now.strftime("%Y-%m-%d %H:%M:%S")
                heartbeat.status = 'Healthy'

        # 3. Database Backup (v4.4.0)
        from backup_job import run_backup
        run_backup()

        # 4. Automation Heartbeat (v3.9.0)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        monitor_hb = AutomationHeartbeat.query.filter_by(task_name='Health Monitor').first()
        if not monitor_hb:
            monitor_hb = AutomationHeartbeat(task_name='Health Monitor')
            db.session.add(monitor_hb)
        monitor_hb.last_run = timestamp
        monitor_hb.status = 'Healthy'

        db.session.commit()
        logger.info("Health Monitor check complete.")

def generate_alert(severity, message, equipment_id):
    """
    Inserts an alert if it doesn't already exist and is unresolved.
    """
    existing = Alert.query.filter_by(message=message, is_resolved=False).first()
    if existing:
        return

    new_alert = Alert(
        severity=severity,
        message=message,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        is_resolved=False,
        equipment_id=equipment_id
    )
    db.session.add(new_alert)
    logger.warning(f"Alert Generated: [{severity}] {message}")

    # Automated Service Dispatch (v5.6.0)
    if severity == "Critical" and "OFFLINE" in message:
        import secrets
        ticket_id = f"AUTO-SRV-{secrets.token_hex(4).upper()}"
        new_dispatch = ServiceDispatch(
            ticket_id=ticket_id,
            equipment_id=equipment_id,
            provider='AutoDispatch-v7.7',
            notes='Heartbeat failure detected by SQLAlchemy monitor',
            status='Pending',
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.session.add(new_dispatch)
        unit = EquipmentMetric.query.get(equipment_id)
        if unit:
            unit.maintenance_status = 'Service Dispatched'
        logger.info(f"Automated Dispatch Triggered: {ticket_id} for Unit {equipment_id}")

    # Send Notification (Franchise filtering)
    unit = EquipmentMetric.query.get(equipment_id)
    if unit:
        lead = Lead.query.filter(Lead.company.contains(unit.location)).first()
        fid = lead.id if lead else None
        emoji = "⚠️" if severity == "Warning" else "🚨"
        send_notification(f"{emoji} [{severity}] {message}", franchise_id=fid)

import time

if __name__ == "__main__":
    while True:
        try:
            monitor_health()
        except Exception as e:
            logger.error(f"Health Monitor encountered an error: {e}")
        time.sleep(60)
