import sqlite3
import argparse
import sys
from datetime import datetime

DB_NAME = "crm.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def list_leads(priority=None):
    conn = get_db()
    cursor = conn.cursor()
    if priority:
        cursor.execute("SELECT id, company, contact_name, status, priority FROM leads WHERE priority = ?", (priority,))
    else:
        cursor.execute("SELECT id, company, contact_name, status, priority FROM leads")

    leads = cursor.fetchall()
    print(f"{'ID':<10} | {'Company':<25} | {'Contact':<20} | {'Status':<20} | {'Priority'}")
    print("-" * 90)
    for lead in leads:
        print(f"{lead['id']:<10} | {lead['company']:<25} | {lead['contact_name']:<20} | {lead['status']:<20} | {lead['priority']}")
    conn.close()

def update_status(lead_id, status):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    if cursor.rowcount > 0:
        print(f"Successfully updated lead {lead_id} to status: {status}")
    else:
        print(f"Error: Lead ID {lead_id} not found.")
    conn.commit()
    conn.close()

def log_outreach(lead_id, channel, notes):
    conn = get_db()
    cursor = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO outreach_logs (lead_id, date_sent, channel, notes)
    VALUES (?, ?, ?, ?)
    """, (lead_id, date_str, channel, notes))
    print(f"Logged {channel} outreach for lead {lead_id} at {date_str}")
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="StepManiaX B2B CRM CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # List Leads
    list_parser = subparsers.add_parser("list", help="List all leads")
    list_parser.add_argument("--priority", help="Filter by priority (High, Medium, Low)")

    # Update Status
    status_parser = subparsers.add_parser("status", help="Update lead status")
    status_parser.add_argument("id", help="Lead ID")
    status_parser.add_argument("status", help="New status (e.g., 'Outreach Sent', 'Meeting Scheduled')")

    # Log Outreach
    log_parser = subparsers.add_parser("log", help="Log an outreach attempt")
    log_parser.add_argument("id", help="Lead ID")
    log_parser.add_argument("--channel", default="Email", help="Communication channel")
    log_parser.add_argument("--notes", default="", help="Outreach notes")

    args = parser.parse_args()

    if args.command == "list":
        list_leads(args.priority)
    elif args.command == "status":
        update_status(args.id, args.status)
    elif args.command == "log":
        log_outreach(args.id, args.channel, args.notes)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
