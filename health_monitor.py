import sqlite3
import os
import analytics
from datetime import datetime
from notifications import send_notification
from app import app, db # Need context for SQLAlchemy models if we use them, or just raw SQL

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')

def get_historical_avg(cursor, equipment_id):
    """Calculates average scans per hour for a unit."""
    cursor.execute("SELECT scans_count FROM telemetry_history WHERE equipment_id = ?", (equipment_id,))
    rows = cursor.fetchall()
    if not rows: return 0
    return sum(r[0] for r in rows) / len(rows)

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

        # D. Real-time Usage Anomaly Check
        hist_avg = get_historical_avg(cursor, unit['id'])
        # Get latest scans from history
        cursor.execute("SELECT scans_count FROM telemetry_history WHERE equipment_id = ? ORDER BY timestamp DESC LIMIT 1", (unit['id'],))
        latest = cursor.fetchone()
        if latest:
            is_anomaly, score, reason = analytics.detect_usage_anomaly({'scans_count': latest[0]}, hist_avg)
            if is_anomaly:
                severity = "Critical" if score > 80 else "Warning"
                generate_alert(cursor, severity, f"Usage Anomaly on {unit['equipment_name']}: {reason} (Score: {score})", unit['id'])

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
    cursor.execute("INSERT INTO alert (severity, message, timestamp, is_resolved) VALUES (?, ?, ?, 0)",
                   (severity, message, timestamp))
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
