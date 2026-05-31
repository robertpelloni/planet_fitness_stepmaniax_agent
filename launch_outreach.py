import os
import sqlite3
from datetime import datetime
from app import app, db
from models import Lead, AuditLog, OutreachLog, Feedback
import analytics

DB_PATH = 'crm.db'

def launch_outreach():
    """
    Identifies leads ready for outreach and generates simulation messages.
    (v5.9.0): Enhanced with ML-based optimization simulation and sentiment awareness.
    """
    print("--- Starting Automated Outreach Dispatcher (Optimized v5.9.0) ---")

    with app.app_context():
        # Optimization: Prioritize high-propensity leads
        leads = Lead.query.filter_by(status='Ready for Outreach').all()

        # Calculate propensity scores before filtering
        for lead in leads:
            member_count = db.session.query(db.func.count(Lead.id)).filter_by(id=lead.id).scalar() # Placeholder for complex logic
            lead_dict = {
                'num_clubs': lead.num_clubs,
                'region': lead.region,
                'status': lead.status,
                'priority': lead.priority,
                'pilot_engagement': {'member_count': 0, 'total_points': 0},
                'portal_views': lead.portal_views or 0,
                'avg_feedback_rating': 5.0
            }
            lead.propensity_score = analytics.calculate_propensity_score(lead_dict)

        # Sort and prioritize leads with high propensity
        leads.sort(key=lambda x: x.propensity_score, reverse=True)
        high_propensity_leads = [l for l in leads if l.propensity_score >= 80]
        other_leads = [l for l in leads if l.propensity_score < 80]

        leads_to_process = high_propensity_leads + other_leads

        if not leads_to_process:
            print("No leads currently 'Ready for Outreach'.")
            return

        for lead in leads_to_process:
            print(f"Processing Outreach for: {lead.company} ({lead.contact_name}) [Score: {lead.propensity_score}]")

            # Sentiment Awareness Simulation: Check feedback from same region
            avg_regional_feedback = db.session.query(db.func.avg(Feedback.rating))\
                .join(Lead, Feedback.franchise_id == Lead.id)\
                .filter(Lead.region_cluster == lead.region_cluster).scalar() or 4.5

            sentiment_modifier = ""
            if avg_regional_feedback < 4.0:
                sentiment_modifier = f"\n\nI've noticed that member satisfaction in {lead.region} is a key focus right now. Our platform is specifically designed to boost retention and positive engagement during periods of flux."
            elif avg_regional_feedback >= 4.8:
                sentiment_modifier = f"\n\nWith {lead.region} clubs performing at peak satisfaction levels, StepManiaX offers the 'next-level' engagement to keep that momentum growing."

            # Simulation of message generation
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"""
Subject: Strategic Amenity Pilot: Interactive HIIT / Member Retention ({lead.region})

{lead.contact_name},

I represent an initiative looking to deploy a high-engagement, interactive HIIT platform to a select club in the {lead.region} market as a zero-cost pilot program.

We are targeting a specific demographic—members looking for gamified, high-retention cardio alternatives. We would like to pitch a 100% risk-mitigated, 90-day placement of a commercial-grade StepManiaX All-In-One unit at a pilot location under your management.{sentiment_modifier}

Do you have 5 minutes for a brief introductory call later this week?

Best regards,
B2B Sales Agent (Autonomous Dispatch)
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
                action=f"Automated Outreach Sent (Optimized): {lead.company} [Score: {lead.propensity_score}]",
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
