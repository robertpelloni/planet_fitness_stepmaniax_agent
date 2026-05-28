import sqlite3
import os
import analytics

DB_PATH = "crm.db"
OUTPUT_DIR = "outreach/generated_messages"

def generate_outreach_bundle():
    """
    Generates personalized outreach messages (LinkedIn/Email) for high-propensity leads.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch top 10 high-propensity leads
    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()

    # Calculate scores manually to sort
    scored_leads = []
    for lead in leads:
        score = analytics.calculate_propensity_score(dict(lead))
        scored_leads.append((score, lead))

    scored_leads.sort(key=lambda x: x[0], reverse=True)

    for score, lead in scored_leads[:10]:
        company = lead['company']
        contact = lead['contact_name'] or "Team"
        clubs = lead['num_clubs']
        token = lead['public_token']
        if not token:
            # Generate one-time if missing (should be handled by app/cli)
            import secrets
            token = secrets.token_urlsafe(16)
        portal_url = f"http://smx-agent.fit/prospect/{token}" # Placeholder domain

        metrics = analytics.calculate_detailed_metrics(num_clubs=clubs)
        profit = metrics['annual_net_profit']

        # 1. LinkedIn Message (Short & Punchy)
        li_msg = f"Hi {contact.split()[0]},\n\nI’ve been following {company}’s expansion in {lead['region']}—impressive footprint of {clubs} clubs. We’ve modeled a 90-day pilot for StepManiaX that projects a ${profit:,.0f} annual profit lift across your portfolio via retention gains. No capital risk. \n\nCalculations here: {portal_url}\n\nWorth a 10-min chat?\n- Jules"

        # 2. Email Sequence (More detailed)
        email_msg = f"Subject: Retention strategy for {company}’s {clubs} locations\n\nDear {contact},\n\nI’m reaching out because {company}’s commitment to the {lead['region']} market aligns perfectly with our regional StepManiaX pilot program.\n\nWe’ve developed a data-driven ROI model for your specific portfolio size, projecting a significant lift in member LTV. You can view your personalized partnership dashboard here:\n\n{portal_url}\n\nOur 'Rogue Pilot' program offers a $0 hardware lease for the first 90 days, allowing you to verify these retention metrics using real-time telemetry before any long-term commitment.\n\nAre you available for a brief discovery call next Tuesday or Wednesday?\n\nBest regards,\n\nJules\nStepManiaX B2B Agent"

        # Save to bundle
        bundle_path = os.path.join(OUTPUT_DIR, f"{company.replace(' ', '_')}_outreach.txt")
        with open(bundle_path, "w") as f:
            f.write("--- LINKEDIN MESSAGE ---\n")
            f.write(li_msg)
            f.write("\n\n--- EMAIL TEMPLATE ---\n")
            f.write(email_msg)

        print(f"Generated outreach bundle for {company} (Score: {score})")

    conn.close()

if __name__ == "__main__":
    generate_outreach_bundle()
