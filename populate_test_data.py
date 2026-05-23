import sqlite3
import os
from werkzeug.security import generate_password_hash

db_path = 'crm.db'

def populate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Leads
    leads = [
        ('EPIC-001', 'EPIC Fitness Group', 'John Doe', 'VP Operations', 'john@epicfitness.com', 'Midwest', 'Pilot MOU Signed', 'High', 15, 0.04, 20.0, 150000),
        ('FLY-002', 'Flynn Group', 'Jane Smith', 'Chief Operating Officer', 'jane@flynngroup.com', 'National', 'Identified', 'High', 120, 0.03, 15.0, 850000)
    ]
    cursor.executemany("INSERT OR REPLACE INTO leads (id, company, contact_name, title, email, region, status, priority, num_clubs, retention_lift, avg_monthly_fee, projected_annual_profit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", leads)

    # 2. Users (Admin, Franchisee, Staff)
    cursor.execute("DELETE FROM user")
    users = [
        (1, 'admin', generate_password_hash('admin123'), 'Admin', None),
        (2, 'franchisee', generate_password_hash('planet123'), 'Franchisee', 'EPIC-001'),
        (3, 'staff', generate_password_hash('staff123'), 'Staff', 'EPIC-001')
    ]
    cursor.executemany("INSERT INTO user (id, username, password_hash, role, franchise_id) VALUES (?, ?, ?, ?, ?)", users)

    # 3. Equipment Metrics
    cursor.execute("DELETE FROM equipment_metric")
    metrics = [
        (1, 'StepManiaX Unit A', 'EPIC Fitness - Detroit', 'EPIC-001', 98.5, 1250, '2026-05-01', 12.5, 100, 'Operational'),
        (2, 'StepManiaX Unit B', 'Flynn Group - Chicago', 'FLY-002', 92.0, 850, '2026-04-20', 10.2, 80, 'Needs Maintenance')
    ]
    cursor.executemany("INSERT INTO equipment_metric (id, equipment_name, location, franchise_id, uptime_percent, total_scans, last_service_date, avg_session_duration, total_sessions, maintenance_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", metrics)

    # 4. Alerts
    cursor.execute("DELETE FROM alert")
    alerts = [
        ('Critical', 'Low Uptime detected on StepManiaX Unit B at Flynn Group - Chicago: 92.0%', '2026-05-23 09:00', 0, 2)
    ]
    cursor.executemany("INSERT INTO alert (severity, message, timestamp, is_resolved, equipment_id) VALUES (?, ?, ?, ?, ?)", alerts)

    # 5. Members
    cursor.execute("DELETE FROM member")
    members = [
        ('Alice Wonder', 'alice@example.com', 'Completed', '2026-05-10', 'EPIC-001', None),
        ('Bob Builder', 'bob@example.com', 'Registered', '2026-05-15', 'EPIC-001', None)
    ]
    cursor.executemany("INSERT INTO member (name, email, onboarding_status, registration_date, franchise_id, user_id) VALUES (?, ?, ?, ?, ?, ?)", members)

    conn.commit()
    conn.close()
    print("Test data populated successfully.")

if __name__ == "__main__":
    populate()
