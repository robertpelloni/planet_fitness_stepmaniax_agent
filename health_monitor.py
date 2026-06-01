import sqlite3
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import analytics
from notifications import send_notification
from app import app, db

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')

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
    """
    logger.info("Starting Health Monitor...")

    # Lead Cadence Processing (v6.6.0 Orchestration)
    # Automatically process multi-tier follow-up cadence
    # Move this BEFORE opening the SQLite connection to avoid 'database is locked'
    # when launch_outreach() uses SQLAlchemy's session.
    from launch_outreach import launch_outreach
    try:
        launch_outreach()
    except Exception as e:
        logger.error(f"Error in launch_outreach() during health monitor cycle: {e}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch all metrics
    cursor.execute("SELECT * FROM equipment_metric")
    units = cursor.fetchall()

    for unit in units:
        # A. Uptime check (Warning for < 98%)
        if unit['uptime_percent'] < 98.0 and unit['uptime_percent'] >= 95.0:
            generate_alert(cursor, "Warning", f"Degraded performance on {unit['equipment_name']} at {unit['location']}: {unit['uptime_percent']}%", unit['id'])

        # B. Uptime check (Critical for < 95%)
        elif unit['uptime_percent'] < 95.0:
            generate_alert(cursor, "Critical", f"Low Uptime detected on {unit['equipment_name']} at {unit['location']}: {unit['uptime_percent']}%", unit['id'])

        # C. Session variance check (Warning if avg session is < 5 mins)
        if unit['total_scans'] > 10 and unit['avg_session_duration'] < 5.0:
             generate_alert(cursor, "Warning", f"Short session duration anomaly on {unit['equipment_name']} at {unit['location']}: {unit['avg_session_duration']}m avg.", unit['id'])

        # D. Heartbeat / Offline Check (Critical if no heartbeat > 10 mins)
        if unit['last_heartbeat']:
            last_hb = datetime.strptime(unit['last_heartbeat'], "%Y-%m-%d %H:%M:%S")
            diff = (datetime.now() - last_hb).total_seconds()
            if diff > 600: # 10 minutes
                generate_alert(cursor, "Critical", f"UNIT OFFLINE: {unit['equipment_name']} at {unit['location']} has not reported a heartbeat for > 10 minutes.", unit['id'])
        else:
            generate_alert(cursor, "Warning", f"Heartbeat Missing: {unit['equipment_name']} at {unit['location']} has never reported a heartbeat.", unit['id'])

        # E. Predictive Health Calculation (v3.7.0)
        unit_data = dict(unit)
        score = analytics.calculate_predictive_health_score(unit_data)
        cursor.execute("UPDATE equipment_metric SET predictive_health_score = ? WHERE id = ?", (score, unit['id']))

    # Weekly Pilot Summary Generation (v6.2.0)
    # Checks if today is Sunday night (23:00 - 23:59) and if we've already run it this week.
    now = datetime.now()
    if now.weekday() == 6 and now.hour == 23:
        # Get the start of the current week (Monday)
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")

        cursor.execute("SELECT last_run FROM automation_heartbeat WHERE task_name = 'Weekly Summary Trigger'")
        last_trigger = cursor.fetchone()

        # Only run if not already triggered this week
        if not last_trigger or last_trigger[0][:10] < week_start:
            logger.info(f"Executing Weekly Pilot Summary generation for week starting {week_start}...")
            cursor.execute("SELECT id FROM leads WHERE status LIKE '%Pilot%'")
            active_pilots = cursor.fetchall()
            from report_generator import generate_weekly_summary
            for pilot in active_pilots:
                generate_weekly_summary(pilot['id'])

            # Update trigger heartbeat
            cursor.execute("""
                INSERT INTO automation_heartbeat (task_name, last_run, status)
                VALUES ('Weekly Summary Trigger', ?, 'Healthy')
                ON CONFLICT(task_name) DO UPDATE SET last_run=excluded.last_run, status='Healthy'
            """, (now.strftime("%Y-%m-%d %H:%M:%S"),))

    # 3. Database Backup (v4.4.0)
    from backup_job import run_backup
    run_backup()

    # 4. Automation Heartbeat (v3.9.0)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO automation_heartbeat (task_name, last_run, status)
        VALUES ('Health Monitor', ?, 'Healthy')
        ON CONFLICT(task_name) DO UPDATE SET last_run=excluded.last_run, status='Healthy'
    """, (timestamp,))

    conn.commit()
    conn.close()
    logger.info("Health Monitor check complete.")

def generate_alert(cursor, severity, message, equipment_id):
    """
    Inserts an alert if it doesn't already exist and is unresolved.
    """
    cursor.execute("SELECT id FROM alert WHERE message = ? AND is_resolved = 0", (message,))
    if cursor.fetchone():
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO alert (severity, message, timestamp, is_resolved, equipment_id) VALUES (?, ?, ?, 0, ?)",
                   (severity, message, timestamp, equipment_id))
    logger.warning(f"Alert Generated: [{severity}] {message}")

    # Automated Service Dispatch (v5.6.0)
    # Trigger dispatch for OFFLINE critical events
    if severity == "Critical" and "OFFLINE" in message:
        import secrets
        ticket_id = f"AUTO-SRV-{secrets.token_hex(4).upper()}"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO service_dispatch (ticket_id, equipment_id, provider, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ticket_id, equipment_id, 'AutoDispatch-v5.6', 'Heartbeat failure detected by monitor', 'Pending', created_at))
        cursor.execute("UPDATE equipment_metric SET maintenance_status = 'Service Dispatched' WHERE id = ?", (equipment_id,))
        logger.info(f"Automated Dispatch Triggered: {ticket_id} for Unit {equipment_id}")

    # Send Notification (Franchise filtering)
    cursor.execute("SELECT location FROM equipment_metric WHERE id = ?", (equipment_id,))
    loc = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM leads WHERE ? LIKE '%' || company || '%'", (loc,))
    lead = cursor.fetchone()
    fid = lead[0] if lead else None

    emoji = "⚠️" if severity == "Warning" else "🚨"
    with app.app_context():
        send_notification(f"{emoji} [{severity}] {message}", franchise_id=fid)

import time

if __name__ == "__main__":
    while True:
        try:
            monitor_health()
        except Exception as e:
            logger.error(f"Health Monitor encountered an error: {e}")
        time.sleep(60)
