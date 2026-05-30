import sqlite3
import json
import os
import secrets

DB_NAME = "crm.db"
JSON_FILE = "crm.json"

def initialize_db():
    """
    Initializes the SQLite database and migrates data from crm.json.
    Includes schema enhancements for follow-up tracking.
    Includes schema synchronization with SQLAlchemy models (v4.4.0).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create Tables (Base Schema)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY,
        company TEXT,
        contact_name TEXT,
        title TEXT,
        email TEXT,
        region TEXT,
        status TEXT,
        priority TEXT,
        notes TEXT,
        num_clubs INTEGER,
        retention_lift REAL,
        avg_monthly_fee REAL,
        projected_annual_profit REAL,
        follow_up_count INTEGER DEFAULT 0,
        last_contact_date TEXT,
        public_token TEXT UNIQUE,
        portal_views INTEGER DEFAULT 0,
        region_cluster TEXT DEFAULT 'US-EAST-1'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outreach_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id TEXT,
        date_sent TEXT,
        channel TEXT,
        notes TEXT,
        FOREIGN KEY (lead_id) REFERENCES leads (id)
    )
    """)

    # 2. Schema Migrations (Add columns if missing for existing DBs)
    cursor.execute("PRAGMA table_info(leads)")
    columns = [column[1] for column in cursor.fetchall()]

    migrations = {
        "follow_up_count": "INTEGER DEFAULT 0",
        "last_contact_date": "TEXT",
        "public_token": "TEXT UNIQUE",
        "portal_views": "INTEGER DEFAULT 0",
        "region_cluster": "TEXT DEFAULT 'US-EAST-1'"
    }
    for col, definition in migrations.items():
        if col not in columns:
            print(f"Adding {col} column to leads...")
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} {definition}")

    # User table migrations (v4.9.0)
    # Ensure table exists first if using raw SQL migration script
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'Franchisee'
    )""")

    cursor.execute("PRAGMA table_info(user)")
    user_columns = [column[1] for column in cursor.fetchall()]
    user_migrations = {
        "franchise_id": "TEXT",
        "last_login": "TEXT",
        "failed_login_attempts": "INTEGER DEFAULT 0",
        "is_locked": "BOOLEAN DEFAULT 0",
        "mfa_secret": "TEXT",
        "mfa_enabled": "BOOLEAN DEFAULT 0",
        "api_key": "TEXT UNIQUE",
        "reset_token": "TEXT UNIQUE",
        "reset_token_expiry": "TEXT",
        "perm_crm_view": "BOOLEAN DEFAULT 1",
        "perm_crm_edit": "BOOLEAN DEFAULT 0",
        "perm_ops_view": "BOOLEAN DEFAULT 1",
        "perm_revenue_view": "BOOLEAN DEFAULT 0",
        "perm_admin_access": "BOOLEAN DEFAULT 0"
    }
    for col, definition in user_migrations.items():
        if col not in user_columns:
            print(f"Adding {col} column to user table...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col} {definition}")

    # Regional Cluster migrations (v5.1.0)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment_metric (
        id INTEGER PRIMARY KEY,
        equipment_name TEXT NOT NULL,
        location TEXT NOT NULL
    )""")
    cursor.execute("PRAGMA table_info(equipment_metric)")
    eq_columns = [column[1] for column in cursor.fetchall()]
    if "region_cluster" not in eq_columns:
        print("Adding region_cluster to equipment_metric...")
        cursor.execute("ALTER TABLE equipment_metric ADD COLUMN region_cluster TEXT DEFAULT 'US-EAST-1'")

    # Hardware Check-in migrations (v5.2.0)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS member (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )""")
    cursor.execute("PRAGMA table_info(member)")
    member_columns = [column[1] for column in cursor.fetchall()]
    if "biometric_token" not in member_columns:
        print("Adding biometric_token to member table...")
        cursor.execute("ALTER TABLE member ADD COLUMN biometric_token TEXT UNIQUE")
    if "nfc_uid" not in member_columns:
        print("Adding nfc_uid to member table...")
        cursor.execute("ALTER TABLE member ADD COLUMN nfc_uid TEXT UNIQUE")

    # Service Dispatch migrations (v5.6.0)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_dispatch (
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

    # 3. Migrate Data from JSON (Idempotent)
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)

        for lead in data['leads']:
            roi = lead.get('roi_projection') or {}

            # Check if lead exists
            cursor.execute("SELECT id, public_token FROM leads WHERE id = ?", (lead['id'],))
            exists = cursor.fetchone()

            if exists:
                token = exists[1] or secrets.token_urlsafe(16)
                cursor.execute("""
                UPDATE leads SET
                    company=?, contact_name=?, title=?, email=?, region=?, status=?, priority=?, notes=?,
                    num_clubs=?, retention_lift=?, avg_monthly_fee=?, projected_annual_profit=?,
                    public_token=?
                WHERE id=?
                """, (
                    lead['company'], lead['contact_name'], lead['title'], lead['email'], lead['region'],
                    lead['status'], lead['priority'], lead['notes'],
                    roi.get('num_clubs'), roi.get('retention_lift'), roi.get('avg_monthly_fee'),
                    roi.get('projected_annual_profit'), token, lead['id']
                ))
            else:
                token = secrets.token_urlsafe(16)
                cursor.execute("""
                INSERT INTO leads (
                    id, company, contact_name, title, email, region, status, priority, notes,
                    num_clubs, retention_lift, avg_monthly_fee, projected_annual_profit, public_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead['id'],
                    lead['company'],
                    lead['contact_name'],
                    lead['title'],
                    lead['email'],
                    lead['region'],
                    lead['status'],
                    lead['priority'],
                    lead['notes'],
                    roi.get('num_clubs'),
                    roi.get('retention_lift'),
                    roi.get('avg_monthly_fee'),
                    roi.get('projected_annual_profit'),
                    token
                ))

        print(f"Successfully synchronized leads from {JSON_FILE} to {DB_NAME}.")
    else:
        print(f"Warning: {JSON_FILE} not found. DB structure updated.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
