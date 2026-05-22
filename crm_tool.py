import sqlite3
import argparse
import sys
from datetime import datetime
from analytics import calculate_detailed_metrics

DB_NAME = "crm.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def list_leads(priority=None):
    conn = get_db()
    cursor = conn.cursor()
    if priority:
        cursor.execute("SELECT id, company, contact_name, status, priority, follow_up_count FROM leads WHERE priority = ?", (priority,))
    else:
        cursor.execute("SELECT id, company, contact_name, status, priority, follow_up_count FROM leads")

    leads = cursor.fetchall()
    print(f"{'ID':<10} | {'Company':<25} | {'Contact':<20} | {'Status':<20} | {'Prio':<6} | {'F/U'}")
    print("-" * 105)
    for lead in leads:
        print(f"{lead['id']:<10} | {lead['company']:<25} | {lead['contact_name']:<20} | {lead['status']:<20} | {lead['priority']:<6} | {lead['follow_up_count']}")
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

    # Update lead record
    cursor.execute("""
    UPDATE leads SET
        follow_up_count = follow_up_count + 1,
        last_contact_date = ?,
        status = 'Outreach Active'
    WHERE id = ?
    """, (date_str, lead_id))

    # Fetch new count
    cursor.execute("SELECT follow_up_count FROM leads WHERE id = ?", (lead_id,))
    res = cursor.fetchone()
    if res:
        new_count = res['follow_up_count']

        # Insert log entry
        cursor.execute("""
        INSERT INTO outreach_logs (lead_id, date_sent, channel, notes)
        VALUES (?, ?, ?, ?)
        """, (lead_id, date_str, channel, notes))

        print(f"Logged {channel} outreach for lead {lead_id} at {date_str} (Total Follow-ups: {new_count})")
    else:
        print(f"Error: Lead {lead_id} not found.")

    conn.commit()
    conn.close()

def show_portfolio_analytics():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE num_clubs IS NOT NULL")
    leads = cursor.fetchall()

    total_clubs = 0
    total_annual_profit = 0

    print("===========================================================")
    print("   StepManiaX B2B Portfolio Analytics")
    print("===========================================================")
    print(f"{'Company':<25} | {'Clubs':<6} | {'Projected Annual Profit'}")
    print("-" * 65)

    for lead in leads:
        metrics = calculate_detailed_metrics(
            num_clubs=lead['num_clubs'],
            retention_lift_percent=lead['retention_lift'] or 0.03,
            avg_monthly_fee=lead['avg_monthly_fee'] or 15.0
        )
        total_clubs += lead['num_clubs']
        total_annual_profit += metrics['annual_net_profit']
        print(f"{lead['company']:<25} | {lead['num_clubs']:<6} | ${metrics['annual_net_profit']:,.2f}")

    print("-" * 65)
    print(f"{'TOTAL PORTFOLIO':<25} | {total_clubs:<6} | ${total_annual_profit:,.2f}")
    print("===========================================================")
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

    # Analytics
    subparsers.add_parser("analytics", help="Show total portfolio ROI potential")

    args = parser.parse_args()

    if args.command == "list":
        list_leads(args.priority)
    elif args.command == "status":
        update_status(args.id, args.status)
    elif args.command == "log":
        log_outreach(args.id, args.channel, args.notes)
    elif args.command == "analytics":
        show_portfolio_analytics()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
