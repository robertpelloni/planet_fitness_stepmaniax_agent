from datetime import datetime, timedelta
from app import app, db
from models import Lead

def check_follow_ups():
    """
    Identifies leads that are due for follow-up based on a 7-day interval (v8.0.0 SQLAlchemy).
    """
    with app.app_context():
        # Threshold: 7 days since last contact
        threshold_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

        due_leads = Lead.query.filter(
            Lead.status == 'Outreach Active',
            Lead.last_contact_date < threshold_date
        ).all()

        if not due_leads:
            print("No leads are currently due for follow-up.")
            return

        print(f"{'ID':<10} | {'Company':<25} | {'Last Contact':<20} | {'Next Step'}")
        print("-" * 80)
        for lead in due_leads:
            next_count = (lead.follow_up_count or 0) + 1
            print(f"{lead.id:<10} | {lead.company:<25} | {lead.last_contact_date:<20} | Follow-up #{next_count}")

if __name__ == "__main__":
    check_follow_ups()
