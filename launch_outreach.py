import os
import sqlite3
from datetime import datetime
from app import app, db
from models import Lead, AuditLog, OutreachLog

DB_PATH = 'crm.db'

def launch_outreach():
    """
    Identifies leads ready for outreach and generates simulation messages.
    """
    print("--- Starting Automated Outreach Dispatcher ---")

    with app.app_context():
        leads = Lead.query.filter_by(status='Ready for Outreach').all()

        if not leads:
            print("No leads currently 'Ready for Outreach'.")
            return

        for lead in leads:
            print(f"Processing Outreach for: {lead.company} ({lead.contact_name})")

            # Simulation of message generation
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"""
Subject: Strategic Amenity Pilot: Interactive HIIT / Member Retention ({lead.region})

{lead.contact_name},

I represent an initiative looking to deploy a high-engagement, interactive HIIT platform to a select club in the {lead.region} market as a zero-cost pilot program.

We are targeting a specific demographic—members looking for gamified, high-retention cardio alternatives. We would like to pitch a 100% risk-mitigated, 90-day placement of a commercial-grade StepManiaX All-In-One unit at a pilot location under your management.

Do you have 5 minutes for a brief introductory call later this week?

Best regards,
B2B Sales Agent
            """

            # Save generated message for record
            outreach_dir = 'outreach/generated_messages'
            if not os.path.exists(outreach_dir):
                os.makedirs(outreach_dir)

            filename = f"{lead.company.replace(' ', '_')}_outreach_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(os.path.join(outreach_dir, filename), 'w') as f:
                f.write(message)

            # Log Outreach Attempt
            log = OutreachLog(
                lead_id=lead.id,
                date_sent=timestamp,
                channel='Email',
                notes=f"Initial outreach sent to {lead.email}. Message saved to {filename}"
            )
            db.session.add(log)

            # Log Security Event (Audit)
            audit = AuditLog(
                user_id=None, # System Automated
                action=f"Automated Outreach Sent: {lead.company}",
                ip_address='127.0.0.1',
                timestamp=timestamp
            )
            db.session.add(audit)

            # Update Lead Status
            lead.status = 'Outreach Active'
            lead.last_contact_date = timestamp
            lead.follow_up_count += 1

            print(f"Success: {lead.company} status updated to 'Outreach Active'.")

        db.session.commit()
        print(f"Outreach complete. {len(leads)} leads processed.")

if __name__ == "__main__":
    launch_outreach()
