import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')
TEMPLATE_PATH = "pilot-performance-report.md"
WEEKLY_TEMPLATE_PATH = "weekly-pilot-summary-template.md"
COMMERCIAL_TEMPLATE_PATH = "commercial-proposal-template.md"
REPORTS_DIR = "outreach/reports"
WEEKLY_REPORTS_DIR = "outreach/reports/weekly"
PROPOSALS_DIR = "outreach/proposals"

def generate_report(unit_id):
    """
    Generates a personalized pilot performance report for a specific unit.
    """
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch Unit Data
    cursor.execute("SELECT * FROM equipment_metric WHERE id = ?", (unit_id,))
    unit = cursor.fetchone()
    if not unit:
        print(f"Error: Unit ID {unit_id} not found.")
        return

    # 2. Fetch Onboarding Data
    # Schema uses franchise_id as the link.
    cursor.execute("SELECT count(*) as total, SUM(CASE WHEN onboarding_status='Completed' THEN 1 ELSE 0 END) as completed FROM member WHERE franchise_id = ?", (unit['franchise_id'],))
    onboarding = cursor.fetchone()
    total_onboarded = onboarding['total'] or 0
    completed_onboarding = onboarding['completed'] or 0
    conv_rate = (completed_onboarding / total_onboarded * 100) if total_onboarded > 0 else 0

    # 3. Prepare Data
    report_data = {
        "[Date]": datetime.now().strftime("%Y-%m-%d"),
        "[Unit ID]": unit['equipment_name'],
        "[Location]": unit['location'],
        "[Uptime %]": f"{unit['uptime_percent']}%",
        "[Total Scans]": str(unit['total_scans']),
        "[Avg Session Duration]": f"{unit['avg_session_duration']} minutes",
        "[Actual]": str(unit['total_scans']),
        "[Onboarding Conversion]": f"{conv_rate:.1f}%",
        "[Total Registered Members]": str(total_onboarded)
    }

    # 3. Read Template
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: Template {TEMPLATE_PATH} not found.")
        return

    with open(TEMPLATE_PATH, "r") as f:
        content = f.read()

    # 4. Replace Placeholders
    for key, value in report_data.items():
        content = content.replace(key, value)

    # 5. Save Report
    filename = f"Performance_Report_{unit['equipment_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    filepath = os.path.join(REPORTS_DIR, filename)

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Report generated: {filepath}")
    conn.close()
    return filepath

def generate_weekly_summary(franchise_id):
    """
    Generates an aggregate weekly performance summary for a franchise (v6.1.0).
    """
    if not os.path.exists(WEEKLY_REPORTS_DIR):
        os.makedirs(WEEKLY_REPORTS_DIR)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch Franchise & Metrics
    cursor.execute("SELECT company FROM leads WHERE id = ?", (franchise_id,))
    franchise = cursor.fetchone()
    if not franchise:
        print(f"Error: Franchise ID {franchise_id} not found.")
        return

    # 2. Last 7 Days Scans
    from datetime import datetime, timedelta
    last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        SELECT SUM(scans_count) as total_scans, AVG(duration_minutes) as avg_intensity
        FROM telemetry_history
        WHERE equipment_id IN (SELECT id FROM equipment_metric WHERE franchise_id = ?)
        AND timestamp >= ?
    """, (franchise_id, last_week))
    stats = cursor.fetchone()

    total_scans = stats['total_scans'] or 0
    avg_intensity = round(stats['avg_intensity'] or 0, 1)

    # 3. Avg Uptime
    cursor.execute("SELECT AVG(uptime_percent) as avg_uptime FROM equipment_metric WHERE franchise_id = ?", (franchise_id,))
    uptime_stats = cursor.fetchone()
    avg_uptime = round(uptime_stats['avg_uptime'] or 0, 1)

    # 4. Active Pilot Members
    cursor.execute("SELECT COUNT(*) FROM member WHERE franchise_id = ? AND onboarding_status = 'Completed'", (franchise_id,))
    active_members = cursor.fetchone()[0]

    # 5. Prepare Data
    report_data = {
        "[Franchise Name]": franchise['company'],
        "[Week Ending]": datetime.now().strftime("%Y-%m-%d"),
        "[Total Weekly Scans]": str(total_scans),
        "[Trend]": "Rising" if total_scans > 100 else "Stable",
        "[Avg Uptime]": str(avg_uptime),
        "[Uptime Status]": "Optimal" if avg_uptime > 98 else "Action Required",
        "[Active Members]": str(active_members),
        "[Intensity]": str(avg_intensity),
        "[Engagement Trend Description]": f"Weekly scan volume reached {total_scans} with an average session intensity of {avg_intensity} scans per minute.",
        "[Operational Notes]": f"Fleet uptime averaged {avg_uptime}% over the past 7 days.",
        "[Weekly Recommendation]": "Maintain current pilot parameters and focus on Gen-Z onboarding conversion."
    }

    # 6. Read Template
    if not os.path.exists(WEEKLY_TEMPLATE_PATH):
        print(f"Error: Template {WEEKLY_TEMPLATE_PATH} not found.")
        return

    with open(WEEKLY_TEMPLATE_PATH, "r") as f:
        content = f.read()

    # 7. Replace Placeholders
    for key, value in report_data.items():
        content = content.replace(key, value)

    # 8. Save Report
    filename = f"Weekly_Summary_{franchise['company'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    filepath = os.path.join(WEEKLY_REPORTS_DIR, filename)

    with open(filepath, "w") as f:
        f.write(content)

    # Log to OutreachLog
    cursor.execute("""
        INSERT INTO outreach_logs (lead_id, date_sent, channel, notes)
        VALUES (?, ?, 'Automated Report', ?)
    """, (franchise_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"Generated weekly summary: {filename}"))

    conn.commit()
    print(f"Weekly Summary generated: {filepath}")
    conn.close()
    return filepath

def generate_commercial_proposal(lead_id):
    """
    Generates a tailored commercial expansion proposal for a lead based on their pilot performance.
    """
    if not os.path.exists(PROPOSALS_DIR):
        os.makedirs(PROPOSALS_DIR)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Fetch Lead Data
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()
    if not lead:
        print(f"Error: Lead ID {lead_id} not found.")
        conn.close()
        return

    # 2. Fetch Pilot Location (from equipment_metric)
    cursor.execute("SELECT location FROM equipment_metric WHERE franchise_id = ? LIMIT 1", (lead_id,))
    equipment = cursor.fetchone()
    pilot_location = equipment['location'] if equipment else "your primary pilot facility"

    # 3. Prepare Data
    report_data = {
        "[Franchisee Name]": lead['company'],
        "[Pilot Location]": pilot_location
    }

    # 4. Read Template
    if not os.path.exists(COMMERCIAL_TEMPLATE_PATH):
        print(f"Error: Template {COMMERCIAL_TEMPLATE_PATH} not found.")
        conn.close()
        return

    with open(COMMERCIAL_TEMPLATE_PATH, "r") as f:
        content = f.read()

    # 5. Replace Placeholders
    for key, value in report_data.items():
        content = content.replace(key, value)

    # 6. Save Proposal
    filename = f"Commercial_Proposal_{lead['company'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    filepath = os.path.join(PROPOSALS_DIR, filename)

    with open(filepath, "w") as f:
        f.write(content)

    # Log to OutreachLog
    cursor.execute("""
        INSERT INTO outreach_logs (lead_id, date_sent, channel, notes)
        VALUES (?, ?, 'Commercial Proposal', ?)
    """, (lead_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"Generated commercial proposal: {filename}"))

    conn.commit()
    print(f"Commercial Proposal generated: {filepath}")
    conn.close()
    return filepath

if __name__ == "__main__":
    # Example: Generate report for unit ID 1 if it exists
    generate_report(1)
