import sqlite3
import json
import os

DB_NAME = "crm.db"
JSON_FILE = "crm.json"

def initialize_db():
    """
    Initializes the SQLite database and migrates data from crm.json.
    Includes schema enhancements for follow-up tracking.
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
        projected_annual_profit REAL
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

    # 2. Schema Migrations (Add columns if missing)
    cursor.execute("PRAGMA table_info(leads)")
    columns = [column[1] for column in cursor.fetchall()]

    if "follow_up_count" not in columns:
        print("Adding follow_up_count column...")
        cursor.execute("ALTER TABLE leads ADD COLUMN follow_up_count INTEGER DEFAULT 0")

    if "last_contact_date" not in columns:
        print("Adding last_contact_date column...")
        cursor.execute("ALTER TABLE leads ADD COLUMN last_contact_date TEXT")

    # 3. Migrate Data from JSON (Idempotent)
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)

        for lead in data['leads']:
            roi = lead.get('roi_projection') or {}

            # Check if lead exists
            cursor.execute("SELECT id FROM leads WHERE id = ?", (lead['id'],))
            exists = cursor.fetchone()

            if exists:
                cursor.execute("""
                UPDATE leads SET
                    company=?, contact_name=?, title=?, email=?, region=?, status=?, priority=?, notes=?,
                    num_clubs=?, retention_lift=?, avg_monthly_fee=?, projected_annual_profit=?
                WHERE id=?
                """, (
                    lead['company'], lead['contact_name'], lead['title'], lead['email'], lead['region'],
                    lead['status'], lead['priority'], lead['notes'],
                    roi.get('num_clubs'), roi.get('retention_lift'), roi.get('avg_monthly_fee'),
                    roi.get('projected_annual_profit'), lead['id']
                ))
            else:
                cursor.execute("""
                INSERT INTO leads (
                    id, company, contact_name, title, email, region, status, priority, notes,
                    num_clubs, retention_lift, avg_monthly_fee, projected_annual_profit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    roi.get('projected_annual_profit')
                ))

        print(f"Successfully synchronized leads from {JSON_FILE} to {DB_NAME}.")
    else:
        print(f"Warning: {JSON_FILE} not found. DB structure updated.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
