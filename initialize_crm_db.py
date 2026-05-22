import sqlite3
import json
import os

DB_NAME = "crm.db"
JSON_FILE = "crm.json"

def initialize_db():
    """
    Initializes the SQLite database and migrates data from crm.json.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Create Tables
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

    # 2. Migrate Data from JSON
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)

        for lead in data['leads']:
            roi = lead.get('roi_projection') or {}

            cursor.execute("""
            INSERT OR REPLACE INTO leads (
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

        print(f"Successfully migrated {len(data['leads'])} leads from {JSON_FILE} to {DB_NAME}.")
    else:
        print(f"Warning: {JSON_FILE} not found. Initialized empty database.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
