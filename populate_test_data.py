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
    # Ensure leads table exists if not created by flask init-db
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY, company TEXT, contact_name TEXT, title TEXT, email TEXT,
        region TEXT, status TEXT, priority TEXT, num_clubs INTEGER,
        retention_lift REAL, avg_monthly_fee REAL, projected_annual_profit REAL,
        follow_up_count INTEGER DEFAULT 0, last_contact_date TEXT,
        public_token TEXT UNIQUE, portal_views INTEGER DEFAULT 0
    )""")
    cursor.executemany("INSERT OR REPLACE INTO leads (id, company, contact_name, title, email, region, status, priority, num_clubs, retention_lift, avg_monthly_fee, projected_annual_profit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", leads)

    # 2. Users (Admin, Franchisee, Staff)
    # New columns for v4.0.0 granular RBAC
    cursor.execute("DROP TABLE IF EXISTS user")
    cursor.execute("""
    CREATE TABLE user (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'Franchisee',
        franchise_id TEXT,
        last_login TEXT,
        failed_login_attempts INTEGER DEFAULT 0,
        is_locked BOOLEAN DEFAULT 0,
        perm_crm_view BOOLEAN DEFAULT 1,
        perm_crm_edit BOOLEAN DEFAULT 0,
        perm_ops_view BOOLEAN DEFAULT 1,
        perm_revenue_view BOOLEAN DEFAULT 0,
        perm_admin_access BOOLEAN DEFAULT 0,
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

    users = [
        (1, 'admin', generate_password_hash('admin123'), 'Admin', None, 0, 0, 1, 1, 1, 1, 1),
        (2, 'franchisee', generate_password_hash('planet123'), 'Franchisee', 'EPIC-001', 0, 0, 1, 0, 1, 1, 0),
        (3, 'staff', generate_password_hash('staff123'), 'Staff', 'EPIC-001', 0, 0, 0, 0, 1, 0, 0)
    ]
    cursor.executemany("""
        INSERT INTO user (id, username, password_hash, role, franchise_id, failed_login_attempts, is_locked,
                         perm_crm_view, perm_crm_edit, perm_ops_view, perm_revenue_view, perm_admin_access)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", users)

    # 3. Equipment Metrics
    cursor.execute("DROP TABLE IF EXISTS equipment_metric")
    cursor.execute("""
    CREATE TABLE equipment_metric (
        id INTEGER PRIMARY KEY,
        equipment_name TEXT NOT NULL,
        location TEXT NOT NULL,
        franchise_id TEXT,
        uptime_percent REAL DEFAULT 100.0,
        total_scans INTEGER DEFAULT 0,
        last_service_date TEXT,
        avg_session_duration REAL DEFAULT 0.0,
        total_sessions INTEGER DEFAULT 0,
        maintenance_status TEXT DEFAULT 'Operational',
        last_heartbeat TEXT,
        predictive_health_score REAL DEFAULT 100.0,
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

    metrics = [
        (1, 'StepManiaX Unit A', 'EPIC Fitness - Detroit', 'EPIC-001', 98.5, 1250, '2026-05-01', 12.5, 100, 'Operational'),
        (2, 'StepManiaX Unit B', 'Flynn Group - Chicago', 'FLY-002', 92.0, 850, '2026-04-20', 10.2, 80, 'Needs Maintenance')
    ]
    cursor.executemany("INSERT INTO equipment_metric (id, equipment_name, location, franchise_id, uptime_percent, total_scans, last_service_date, avg_session_duration, total_sessions, maintenance_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", metrics)

    # 4. Alerts
    cursor.execute("DROP TABLE IF EXISTS alert")
    cursor.execute("""
    CREATE TABLE alert (
        id INTEGER PRIMARY KEY,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        is_resolved BOOLEAN DEFAULT 0,
        acknowledged_by TEXT,
        resolved_at TEXT,
        resolved_by TEXT,
        equipment_id INTEGER,
        FOREIGN KEY(equipment_id) REFERENCES equipment_metric(id)
    )""")

    alerts = [
        ('Critical', 'Low Uptime detected on StepManiaX Unit B at Flynn Group - Chicago: 92.0%', '2026-05-23 09:00', 0, 2)
    ]
    cursor.executemany("INSERT INTO alert (severity, message, timestamp, is_resolved, equipment_id) VALUES (?, ?, ?, ?, ?)", alerts)

    # 5. Members and Member Users
    cursor.execute("DROP TABLE IF EXISTS member")
    cursor.execute("""
    CREATE TABLE member (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        onboarding_status TEXT DEFAULT 'Registered',
        registration_date TEXT NOT NULL,
        franchise_id TEXT,
        points INTEGER DEFAULT 0,
        engagement_score REAL DEFAULT 0.0,
        FOREIGN KEY(user_id) REFERENCES user(id),
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

    # Member user for Flynn Group
    flynn_member_user_id = 4
    cursor.execute("""
        INSERT INTO user (id, username, password_hash, role, franchise_id, failed_login_attempts, is_locked,
                         perm_crm_view, perm_crm_edit, perm_ops_view, perm_revenue_view, perm_admin_access)
        VALUES (?, ?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 0)""",
        (flynn_member_user_id, 'member@flynngroup.com', generate_password_hash('member123'), 'Member', 'FLY-002'))

    members = [
        ('Alice Wonder', 'alice@example.com', 'Completed', '2026-05-10', 'EPIC-001', None, 500, 0.8),
        ('Bob Builder', 'bob@example.com', 'Registered', '2026-05-15', 'EPIC-001', None, 100, 0.2),
        ('Flynn Member', 'member@flynngroup.com', 'Registered', '2026-05-20', 'FLY-002', flynn_member_user_id, 250, 0.5)
    ]
    cursor.executemany("INSERT INTO member (name, email, onboarding_status, registration_date, franchise_id, user_id, points, engagement_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", members)

    # 6. Automation Heartbeat
    cursor.execute("DROP TABLE IF EXISTS automation_heartbeat")
    cursor.execute("""
    CREATE TABLE automation_heartbeat (
        id INTEGER PRIMARY KEY,
        task_name TEXT UNIQUE NOT NULL,
        last_run TEXT NOT NULL,
        status TEXT DEFAULT 'Healthy'
    )""")

    conn.commit()
    conn.close()
    print("Test data populated successfully.")

if __name__ == "__main__":
    populate()
