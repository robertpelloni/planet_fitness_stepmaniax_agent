import sqlite3
import os
import secrets
from werkzeug.security import generate_password_hash
from datetime import datetime

db_path = 'crm.db'

def populate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = OFF")

    tables = [
        'user', 'leads', 'equipment_metric', 'alert', 'member',
        'member_schedule', 'telemetry_history', 'automation_heartbeat',
        'feedback', 'payment', 'workout_plan', 'webhook', 'audit_log',
        'outreach_logs', 'service_dispatch'
    ]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    cursor.execute("""
    CREATE TABLE leads (
        id TEXT PRIMARY KEY,
        company TEXT NOT NULL,
        contact_name TEXT,
        title TEXT,
        email TEXT,
        region TEXT,
        status TEXT DEFAULT 'Identified',
        priority TEXT DEFAULT 'Medium',
        notes TEXT,
        num_clubs INTEGER,
        retention_lift REAL DEFAULT 0.03,
        avg_monthly_fee REAL DEFAULT 15.0,
        projected_annual_profit REAL,
        follow_up_count INTEGER DEFAULT 0,
        last_contact_date TEXT,
        public_token TEXT UNIQUE,
        portal_views INTEGER DEFAULT 0,
        region_cluster TEXT DEFAULT 'US-EAST-1'
    )""")

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
        mfa_secret TEXT,
        mfa_enabled BOOLEAN DEFAULT 0,
        api_key TEXT UNIQUE,
        reset_token TEXT UNIQUE,
        reset_token_expiry TEXT,
        perm_crm_view BOOLEAN DEFAULT 1,
        perm_crm_edit BOOLEAN DEFAULT 0,
        perm_ops_view BOOLEAN DEFAULT 1,
        perm_revenue_view BOOLEAN DEFAULT 0,
        perm_admin_access BOOLEAN DEFAULT 0,
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

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
        region_cluster TEXT DEFAULT 'US-EAST-1',
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

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
        biometric_token TEXT UNIQUE,
        nfc_uid TEXT UNIQUE,
        FOREIGN KEY(user_id) REFERENCES user(id),
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

    cursor.execute("""
    CREATE TABLE workout_plan (
        id INTEGER PRIMARY KEY,
        member_id INTEGER NOT NULL UNIQUE,
        name TEXT NOT NULL,
        target_scans INTEGER DEFAULT 1000,
        target_duration INTEGER DEFAULT 300,
        created_at TEXT,
        FOREIGN KEY(member_id) REFERENCES member(id)
    )""")

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

    cursor.execute("""
    CREATE TABLE member_schedule (
        id INTEGER PRIMARY KEY,
        member_id INTEGER,
        member_name TEXT NOT NULL,
        start_time TEXT NOT NULL,
        duration_minutes INTEGER DEFAULT 10,
        equipment_id INTEGER,
        status TEXT DEFAULT 'Scheduled',
        FOREIGN KEY(member_id) REFERENCES member(id),
        FOREIGN KEY(equipment_id) REFERENCES equipment_metric(id)
    )""")

    cursor.execute("""
    CREATE TABLE automation_heartbeat (
        id INTEGER PRIMARY KEY,
        task_name TEXT UNIQUE NOT NULL,
        last_run TEXT NOT NULL,
        status TEXT DEFAULT 'Healthy'
    )""")

    cursor.execute("""
    CREATE TABLE telemetry_history (
        id INTEGER PRIMARY KEY,
        equipment_id INTEGER NOT NULL,
        member_id INTEGER,
        timestamp TEXT NOT NULL,
        scans_count INTEGER DEFAULT 0,
        duration_minutes REAL DEFAULT 0.0,
        FOREIGN KEY(equipment_id) REFERENCES equipment_metric(id),
        FOREIGN KEY(member_id) REFERENCES member(id)
    )""")

    cursor.execute("""
    CREATE TABLE feedback (
        id INTEGER PRIMARY KEY,
        member_id INTEGER,
        franchise_id TEXT,
        rating INTEGER NOT NULL,
        comment TEXT,
        category TEXT DEFAULT 'General',
        timestamp TEXT NOT NULL,
        FOREIGN KEY(member_id) REFERENCES member(id),
        FOREIGN KEY(franchise_id) REFERENCES leads(id)
    )""")

    cursor.execute("""
    CREATE TABLE payment (
        id INTEGER PRIMARY KEY,
        member_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        status TEXT DEFAULT 'Pending',
        transaction_id TEXT UNIQUE,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(member_id) REFERENCES member(id)
    )""")

    cursor.execute("""
    CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        action TEXT NOT NULL,
        ip_address TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )""")

    cursor.execute("""
    CREATE TABLE outreach_logs (
        id INTEGER PRIMARY KEY,
        lead_id TEXT NOT NULL,
        date_sent TEXT NOT NULL,
        channel TEXT,
        notes TEXT,
        FOREIGN KEY(lead_id) REFERENCES leads(id)
    )""")

    cursor.execute("""
    CREATE TABLE service_dispatch (
        id INTEGER PRIMARY KEY,
        ticket_id TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Pending',
        provider TEXT DEFAULT 'Internal',
        notes TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(equipment_id) REFERENCES equipment_metric(id)
    )""")

    cursor.execute("PRAGMA foreign_keys = ON")

    leads = [
        ('EPIC-001', 'EPIC Fitness Group', 'John Doe', 'VP Operations', 'john@epicfitness.com', 'Midwest', 'Pilot MOU Signed', 'High', 15, 0.04, 20.0, 150000, 'token-epic'),
        ('FLY-002', 'Flynn Group', 'Jane Smith', 'Chief Operating Officer', 'jane@flynngroup.com', 'National', 'Identified', 'High', 120, 0.03, 15.0, 850000, 'token-flynn')
    ]
    cursor.executemany("INSERT INTO leads (id, company, contact_name, title, email, region, status, priority, num_clubs, retention_lift, avg_monthly_fee, projected_annual_profit, public_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", leads)

    users = [
        (1, 'admin', generate_password_hash('admin123'), 'Admin', None, 1, 1, 1, 1, 1, secrets.token_urlsafe(32)),
        (2, 'franchisee', generate_password_hash('planet123'), 'Franchisee', 'EPIC-001', 1, 0, 1, 1, 0, secrets.token_urlsafe(32)),
        (3, 'staff', generate_password_hash('staff123'), 'Staff', 'EPIC-001', 0, 0, 1, 0, 0, secrets.token_urlsafe(32))
    ]
    cursor.executemany("""
        INSERT INTO user (id, username, password_hash, role, franchise_id,
                         perm_crm_view, perm_crm_edit, perm_ops_view, perm_revenue_view, perm_admin_access, api_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", users)

    metrics = [
        (1, 'StepManiaX Unit A', 'EPIC Fitness - Detroit', 'EPIC-001', 98.5, 1250, '2026-05-01', 12.5, 100, 'Operational'),
        (2, 'StepManiaX Unit B', 'Flynn Group - Chicago', 'FLY-002', 92.0, 850, '2026-04-20', 10.2, 80, 'Needs Maintenance')
    ]
    cursor.executemany("INSERT INTO equipment_metric (id, equipment_name, location, franchise_id, uptime_percent, total_scans, last_service_date, avg_session_duration, total_sessions, maintenance_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", metrics)

    cursor.execute("""
        INSERT INTO user (id, username, password_hash, role, franchise_id, api_key)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (4, 'member@flynngroup.com', generate_password_hash('member123'), 'Member', 'FLY-002', secrets.token_urlsafe(32)))

    members = [
        (1, 4, 'Flynn Member', 'member@flynngroup.com', 'Registered', '2026-05-20', 'FLY-002', 250, 0.5)
    ]
    cursor.executemany("INSERT INTO member (id, user_id, name, email, onboarding_status, registration_date, franchise_id, points, engagement_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", members)

    cursor.execute("INSERT INTO workout_plan (member_id, name, target_scans, target_duration, created_at) VALUES (?, ?, ?, ?, ?)",
                   (1, "Summer Challenge", 1000, 300, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    print("Test data populated successfully.")

if __name__ == "__main__":
    populate()
