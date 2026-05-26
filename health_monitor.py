import sqlite3
import os
from datetime import datetime, timedelta
import analytics
from notifications import send_notification
from app import app, db # Need context for SQLAlchemy models if we use them, or just raw SQL

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')

def monitor_health():
    """
    Scans equipment metrics and generates alerts for operational anomalies.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Health Monitor...")
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

        # B. Uptime check (Critical for < 95%) - already handled in app.py but good to have here too
        elif unit['uptime_percent'] < 95.0:
            generate_alert(cursor, "Critical", f"Low Uptime detected on {unit['equipment_name']} at {unit['location']}: {unit['uptime_percent']}%", unit['id'])

        # C. Session variance check (Warning if avg session is < 5 mins - potentially user frustration)
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

    # 2. Lead Cadence Processing (v3.9.0)
    process_cadence(cursor)

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
    print("Health Monitor check complete.")

def generate_alert(cursor, severity, message, equipment_id):
    """
    Inserts an alert if it doesn't already exist and is unresolved.
    """
    # Check for existing unresolved alert with same message
    cursor.execute("SELECT id FROM alert WHERE message = ? AND is_resolved = 0", (message,))
    if cursor.fetchone():
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("INSERT INTO alert (severity, message, timestamp, is_resolved, equipment_id) VALUES (?, ?, ?, 0, ?)",
                   (severity, message, timestamp, equipment_id))
    print(f"Alert Generated: [{severity}] {message}")

    # Send Notification (Franchise filtering)
    cursor.execute("SELECT location FROM equipment_metric WHERE id = ?", (equipment_id,))
    loc = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM leads WHERE ? LIKE '%' || company || '%'", (loc,))
    lead = cursor.fetchone()
    fid = lead[0] if lead else None

    emoji = "⚠️" if severity == "Warning" else "🚨"
    with app.app_context():
        send_notification(f"{emoji} [{severity}] {message}", franchise_id=fid)

def process_cadence(cursor):
    """
    Identifies leads due for follow-up and notifies the admin.
    """
    threshold_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    query = """
    SELECT id, company, follow_up_count FROM leads
    WHERE status = 'Outreach Active' AND last_contact_date < ?
    """
    cursor.execute(query, (threshold_date,))
    due_leads = cursor.fetchall()

    for lead in due_leads:
        msg = f"🔔 FOLLOW-UP DUE: {lead['company']} is ready for Cadence Touch #{lead['follow_up_count'] + 1}."
        print(msg)
        with app.app_context():
            send_notification(msg)

import time

if __name__ == "__main__":
    # In production, this script runs in a continuous loop via systemd
    while True:
        try:
            monitor_health()
        except Exception as e:
            print(f"Health Monitor encountered an error: {e}")

        # Check every 60 seconds
        time.sleep(60)
