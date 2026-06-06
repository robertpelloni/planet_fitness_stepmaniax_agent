import sqlite3
import argparse
import sys
from datetime import datetime
from analytics import calculate_detailed_metrics, calculate_propensity_score
from werkzeug.security import generate_password_hash
import secrets

DB_NAME = "crm.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def list_leads(priority=None, scoring=False):
    conn = get_db()
    cursor = conn.cursor()
    if priority:
        cursor.execute("SELECT * FROM leads WHERE priority = ?", (priority,))
    else:
        cursor.execute("SELECT * FROM leads")

    leads = [dict(row) for row in cursor.fetchall()]

    if scoring:
        for lead in leads:
            lead['score'] = calculate_propensity_score(lead)
        leads.sort(key=lambda x: x['score'], reverse=True)

    print(f"{'ID':<10} | {'Company':<25} | {'Status':<20} | {'Prio':<6} | {'F/U':<3} | {'Score'}")
    print("-" * 110)
    for lead in leads:
        score_str = f"{lead.get('score', 'N/A')}" if scoring else "-"
        fu_count = lead.get('follow_up_count', 0) or 0
        print(f"{lead['id']:<10} | {lead['company']:<25} | {lead['status']:<20} | {lead['priority']:<6} | {fu_count:<3} | {score_str}")
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

    print("   StepManiaX B2B Portfolio Analytics")
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
    conn.close()

def create_user(username, password, role='Franchisee', franchise_id=None):
    conn = get_db()
    cursor = conn.cursor()
    # Check if user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if not cursor.fetchone():
        print("Error: 'user' table not found. Please run 'flask init-db' first.")
        return

    password_hash = generate_password_hash(password)
    try:
        cursor.execute("INSERT INTO user (username, password_hash, role, franchise_id) VALUES (?, ?, ?, ?)", (username, password_hash, role, franchise_id))
        print(f"Successfully created {role} user: {username}")
    except sqlite3.IntegrityError:
        print(f"Error: User '{username}' already exists.")

    conn.commit()
    conn.close()

def manage_tokens(lead_id=None):
    conn = get_db()
    cursor = conn.cursor()

    if lead_id:
        cursor.execute("SELECT id, company, public_token FROM leads WHERE id = ?", (lead_id,))
        leads = cursor.fetchall()
    else:
        cursor.execute("SELECT id, company, public_token FROM leads")
        leads = cursor.fetchall()

    print(f"{'ID':<15} | {'Company':<25} | {'Public Token'}")
    print("-" * 80)

    updated_ids = []
    for lead in leads:
        token = lead['public_token']
        if not token:
            token = secrets.token_urlsafe(16)
            cursor.execute("UPDATE leads SET public_token = ? WHERE id = ?", (token, lead['id']))
            updated_ids.append(lead['id'])
        print(f"{lead['id']:<15} | {lead['company']:<25} | {token}")

    if updated_ids:
        conn.commit()
        print(f"\nSuccessfully generated tokens for {len(updated_ids)} leads.")
    conn.close()

def add_webhook(url, service='Discord', franchise_id=None):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO webhook (url, service, franchise_id) VALUES (?, ?, ?)", (url, service, franchise_id))
        print(f"Successfully added {service} webhook for franchise {franchise_id or 'Global'}")
    except sqlite3.Error as e:
        print(f"Error: {e}")
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="StepManiaX B2B CRM CLI Tool")
    subparsers = parser.add_subparsers(dest="command")

    # List Leads
    list_parser = subparsers.add_parser("list", help="List all leads")
    list_parser.add_argument("--priority", help="Filter by priority (High, Medium, Low)")
    list_parser.add_argument("--scoring", action="store_true", help="Sort and display by Propensity Score")

    # Tokens
    token_parser = subparsers.add_parser("tokens", help="Manage prospect access tokens")
    token_parser.add_argument("--id", help="Lead ID (None for all)")

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

    # User Management
    user_parser = subparsers.add_parser("create-user", help="Create a dashboard user")
    user_parser.add_argument("username", help="Username")
    user_parser.add_argument("password", help="Password")
    user_parser.add_argument("--role", default="Franchisee", help="User role (Admin/Franchisee)")
    user_parser.add_argument("--fid", help="Franchise ID (Lead ID)")

    # Webhook Management
    hook_parser = subparsers.add_parser("add-webhook", help="Add a notification webhook")
    hook_parser.add_argument("url", help="Webhook URL")
    hook_parser.add_argument("--service", default="Discord", help="Service (Discord/Slack)")
    hook_parser.add_argument("--fid", help="Franchise ID (Lead ID) - None for Global")

    args = parser.parse_args()

    if args.command == "list":
        list_leads(args.priority, args.scoring)
    elif args.command == "tokens":
        manage_tokens(args.id)
    elif args.command == "status":
        update_status(args.id, args.status)
    elif args.command == "log":
        log_outreach(args.id, args.channel, args.notes)
    elif args.command == "analytics":
        show_portfolio_analytics()
    elif args.command == "create-user":
        create_user(username=args.username, password=args.password, role=args.role, franchise_id=args.fid)
    elif args.command == "add-webhook":
        add_webhook(url=args.url, service=args.service, franchise_id=args.fid)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
