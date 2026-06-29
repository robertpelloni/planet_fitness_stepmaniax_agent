import os
import sqlite3
from datetime import datetime, timedelta
from app import app, db
from models import Lead, AuditLog, OutreachLog, Feedback
import analytics
from googletrans import Translator

DB_PATH = 'crm.db'

# Cadence configuration: (Days since last contact, tier_name)
CADENCE_SCHEDULE = {
    1: (3, "Day 3: Retention Data"),
    2: (7, "Day 7: Operational Ease"),
    3: (14, "Day 14: Final Slot")
}

def get_followup_template(tier, lead):
    """Returns the template for the specified follow-up tier."""

    # Analyze franchise size for dynamic corporate tone
    scale_mention = ""
    if lead.num_clubs and lead.num_clubs >= 100:
        scale_mention = f"Given {lead.company}'s scale of {lead.num_clubs} locations, "
    else:
        scale_mention = f"Given {lead.company}'s focus on high-quality fitness experiences, "

    if tier == 1:
        return f"""
Subject: Re: Strategic Amenity Pilot: Interactive HIIT / Member Retention

{lead.contact_name},

I’m following up on my previous note regarding the StepManiaX 90-day pilot.

One detail I didn’t emphasize: we’ve seen that gamified cardio doesn’t just attract Gen Z—it increases average session duration by up to 25% compared to traditional treadmills.

{scale_mention} this low-impact, high-engagement tool is specifically designed to reduce member churn by providing a structured, progression-based experience.

Do you have 5 minutes this Thursday or Friday for a quick sync?

Best,
B2B Sales Agent (Autonomous Dispatch)
"""
    elif tier == 2:
        return f"""
Subject: Zero-Risk Pilot: Footprint and Maintenance SLA

{lead.contact_name},

I understand that gym floor real estate is premium. To address any operational concerns:

The StepManiaX Kiosk requires a footprint of only 75"W x 95"D and runs on a standard 120V outlet. As part of our pilot agreement, we handle 100% of the maintenance with a guaranteed 48-hour service turnaround.

We handle the hardware; you get the data on how it impacts your club's retention metrics.

Is there a better contact on your operations team I should be speaking with, or are you available for a brief call next Tuesday?

Best,
B2B Sales Agent (Autonomous Dispatch)
"""
    elif tier == 3:
        return f"""
Subject: Final Pilot Slot for {lead.region} / Interactive Cardio

{lead.contact_name},

I’m circling back one last time as we are finalizing our pilot placements for the {lead.region} market for this quarter.

Because we prioritize working with established franchise groups like {lead.company}, I wanted to ensure you had a final opportunity to secure a $0 hardware lease for a StepManiaX unit before we allocate our remaining units to other regional partners.

If the timing isn't right now, I'd still value a 5-minute introductory call to keep us on your radar for future club expansions.

Best,
B2B Sales Agent (Autonomous Dispatch)
"""
    return None

def launch_outreach(force_lead_id=None):
    """
    Identifies leads ready for outreach and follow-up, generating simulation messages.
    (v6.6.0): Added support for forced dispatch of a specific lead.
    """
    print(f"--- Starting Automated Outreach Dispatcher (Cadence v6.6.0) {'[FORCE:' + force_lead_id + ']' if force_lead_id else ''} ---")
    translator = Translator()
    now = datetime.now()

    with app.app_context():
        if force_lead_id:
            lead = db.session.get(Lead, force_lead_id)
            if not lead: return
            if lead.status == 'Ready for Outreach':
                leads_to_process = [(lead, 0)]
            elif lead.status == 'Outreach Active':
                leads_to_process = [(lead, lead.follow_up_count)]
            else:
                print(f"Lead {force_lead_id} is not in a dispatchable state ({lead.status})")
                return
        else:
            # 1. Process Initial Outreach (Ready for Outreach)
            initial_leads = Lead.query.filter_by(status='Ready for Outreach').all()

            # 2. Process Follow-ups (Outreach Active & Not Paused)
            active_leads = Lead.query.filter_by(status='Outreach Active', cadence_paused=False).all()

            followup_leads = []
            for lead in active_leads:
                if lead.follow_up_count in CADENCE_SCHEDULE:
                    days_required, tier_name = CADENCE_SCHEDULE[lead.follow_up_count]
                    if lead.last_contact_date:
                        last_contact = datetime.strptime(lead.last_contact_date, "%Y-%m-%d %H:%M:%S")
                        if now >= last_contact + timedelta(days=days_required):
                            followup_leads.append((lead, lead.follow_up_count))

            leads_to_process = [(l, 0) for l in initial_leads] + followup_leads

        if not leads_to_process:
            print("No leads currently due for initial outreach or follow-up.")
            return

        for lead, tier in leads_to_process:
            print(f"Processing Tier {tier} Outreach for: {lead.company} ({lead.contact_name})")

            # Sentiment Awareness Modifier
            avg_regional_feedback = db.session.query(db.func.avg(Feedback.rating))\
                .join(Lead, Feedback.franchise_id == Lead.id)\
                .filter(Lead.region_cluster == lead.region_cluster).scalar() or 4.5

            sentiment_modifier = ""
            if tier == 0:
                if avg_regional_feedback < 4.0:
                    sentiment_modifier = f"\n\nI've noticed that member satisfaction in {lead.region} is a key focus right now. Our platform is specifically designed to boost retention and positive engagement during periods of flux."
                elif avg_regional_feedback >= 4.8:
                    sentiment_modifier = f"\n\nWith {lead.region} clubs performing at peak satisfaction levels, StepManiaX offers the 'next-level' engagement to keep that momentum growing."

            # Template Selection
            if tier == 0:
                message = f"""
Subject: Strategic Amenity Pilot: Interactive HIIT / Member Retention ({lead.region})

{lead.contact_name},

I represent an initiative looking to deploy a high-engagement, interactive HIIT platform to a select club in the {lead.region} market as a zero-cost pilot program.

We are targeting a specific demographic—members looking for gamified, high-retention cardio alternatives. We would like to pitch a 100% risk-mitigated, 90-day placement of a commercial-grade StepManiaX All-In-One unit at a pilot location under your management.{sentiment_modifier}

Do you have 5 minutes for a brief introductory call later this week?

Best regards,
B2B Sales Agent (Autonomous Dispatch)
"""
            else:
                message = get_followup_template(tier, lead)

            # Region-based Translation
            target_lang = None
            if lead.region == 'Mexico':
                target_lang = 'es'
            elif lead.region in ['Quebec', 'Canada']:
                target_lang = 'fr'

            if target_lang:
                try:
                    print(f"Translating tier {tier} message to {target_lang} for {lead.region}...")
                    translated = translator.translate(message, dest=target_lang)
                    message = translated.text
                except Exception as e:
                    print(f"Translation failed for {lead.company}: {e}")

            # Save generated message
            outreach_dir = 'outreach/generated_messages'
            if not os.path.exists(outreach_dir):
                os.makedirs(outreach_dir)

            tier_suffix = "initial" if tier == 0 else f"followup_d{CADENCE_SCHEDULE[tier][0]}"
            filename = f"{lead.company.replace(' ', '_')}_{tier_suffix}_{now.strftime('%Y%m%d')}.txt"
            with open(os.path.join(outreach_dir, filename), 'w') as f:
                f.write(message)

            # Log Outreach Attempt
            log = OutreachLog(
                lead_id=lead.id,
                date_sent=now.strftime("%Y-%m-%d %H:%M:%S"),
                channel='Email',
                notes=f"Tier {tier} outreach sent. Message saved to {filename}"
            )
            db.session.add(log)

            # Log Security/Audit Event
            audit = AuditLog(
                user_id=None,
                action=f"Automated Outreach Tier {tier} Sent: {lead.company}",
                ip_address='127.0.0.1',
                timestamp=now.strftime("%Y-%m-%d %H:%M:%S")
            )
            db.session.add(audit)

            # Update Lead State
            lead.status = 'Outreach Active'
            lead.last_contact_date = now.strftime("%Y-%m-%d %H:%M:%S")
            lead.follow_up_count += 1

            if lead.follow_up_count > 3:
                lead.status = 'Outreach Exhausted'
                print(f"Lead {lead.company} has exhausted the cadence.")

            print(f"Success: {lead.company} tier {tier} processed.")

        db.session.commit()
        print(f"Outreach cycle complete. {len(leads_to_process)} leads processed.")

if __name__ == "__main__":
    launch_outreach()
