import sqlite3
from datetime import datetime, timedelta

DB_NAME = "crm.db"

def check_follow_ups():
    """
    Identifies leads that are due for follow-up based on a 7-day interval.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Threshold: 7 days since last contact
    threshold_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    query = """
    SELECT id, company, contact_name, follow_up_count, last_contact_date
    FROM leads
    WHERE status = 'Outreach Active'
    AND last_contact_date < ?
    """

    cursor.execute(query, (threshold_date,))
    due_leads = cursor.fetchall()

    if not due_leads:
        print("No leads are currently due for follow-up.")
        return

    print(f"{'ID':<10} | {'Company':<25} | {'Last Contact':<20} | {'Next Step'}")
    print("-" * 80)
    for lead in due_leads:
        next_count = lead['follow_up_count'] + 1
        print(f"{lead['id']:<10} | {lead['company']:<25} | {lead['last_contact_date']:<20} | Follow-up #{next_count}")

    conn.close()

if __name__ == "__main__":
    check_follow_ups()
