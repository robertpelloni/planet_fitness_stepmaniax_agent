import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')
TEMPLATE_PATH = "pilot-performance-report.md"
REPORTS_DIR = "outreach/reports"

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

    # 2. Prepare Data
    report_data = {
        "[Date]": datetime.now().strftime("%Y-%m-%d"),
        "[Unit ID]": unit['equipment_name'],
        "[Location]": unit['location'],
        "[Uptime %]": f"{unit['uptime_percent']}%",
        "[Total Scans]": str(unit['total_scans']),
        "[Avg Session Duration]": f"{unit['avg_session_duration']} minutes",
        "[Actual]": str(unit['total_scans'])
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

if __name__ == "__main__":
    # Example: Generate report for unit ID 1 if it exists
    generate_report(1)
