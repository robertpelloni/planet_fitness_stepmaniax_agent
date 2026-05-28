import sqlite3
import os
from analytics import calculate_detailed_metrics

def generate_personalized_assets(db_name="crm.db", output_dir="outreach/generated"):
    """
    Generates personalized outreach emails and pitch decks based on lead data in SQLite DB.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    email_template = """# Personalized Outreach: {company}

**Target:** {contact_name}, {title}
**Email:** {email}
**Subject:** Strategic Amenity Pilot: Interactive HIIT / Member Retention for {region}

{contact_name},

I’ve been following {company}’s impressive presence in {region}. Given your commitment to providing a high-quality fitness experience in the "Judgement Free Zone," I believe there is a unique opportunity to enhance member retention at your clubs.

We are proposing a 100% risk-mitigated, 90-day placement of a commercial-grade StepManiaX All-In-One unit. This transforms traditional cardio into a gamified experience that significantly increases session duration and frequency of visits among Gen Z and Millennial demographics.

**The Pilot Terms:**
- **Cost:** $0 hardware lease to {company}.
- **Requirements:** Standard 120V outlet and minimal floor space.
- **Maintenance:** We handle 100% of the maintenance with a 48-hour SLA.

Do you have 5 minutes for a brief introductory call this week to discuss a potential pilot at one of your locations?

Best regards,
[Agent Name]
"""

    deck_template = """# StepManiaX: Strategic Proposal for {company}

## Regional Focus: {region}
*A zero-risk, high-retention amenity pilot proposal for Regional Franchise Partners.*

---

## The Opportunity: {company} Portfolio Lift
Gyms lose a massive percentage of members to cardio boredom. For a group of your scale ({num_clubs} locations), even a 2-3% lift in retention results in significant revenue gains.

## Financial Impact Projection (LTV Model)
Based on our analysis of your {num_clubs} locations:
- **Base Member Lifetime Value:** ${base_ltv}
- **Projected Lifted LTV ({lift_pct}% Retention Lift):** ${lifted_ltv}
- **Projected Annual Net Profit across Portfolio:** ${annual_net_profit}
- **Projected ROI Multiple:** {roi_multiple}x

---

## The Hardware: Commercial Grade. Gym Ready.
The SMX Kiosk is designed for the rigorous demands of commercial environments, completely distinct from older arcade hardware.

- **Industrial-Grade Construction:** Heavy-duty steel and reinforced load cells.
- **Compact Footprint:** Fits into any cardio or functional fitness zone (75" x 95").
- **Quiet Operation:** Can be configured to run exclusively via headphone jack.

---

## Next Steps: 90-Day Zero-Risk Pilot
We propose a trial placement at a priority {region} location to gather real-world usage data before any regional commitment.

*Contact us to schedule a brief introductory call.*
"""

    cursor.execute("SELECT * FROM leads WHERE status = 'Ready for Outreach'")
    leads = cursor.fetchall()

    for lead in leads:
        # Generate Email
        email_filename = f"email-{lead['company'].lower().replace(' ', '-')}.md"
        email_filepath = os.path.join(output_dir, email_filename)

        email_content = email_template.format(
            company=lead['company'],
            contact_name=lead['contact_name'],
            title=lead['title'],
            email=lead['email'],
            region=lead['region']
        )

        with open(email_filepath, 'w') as out:
            out.write(email_content)

        # Generate Pitch Deck (if ROI data is present)
        if lead['num_clubs']:
            deck_filename = f"pitch-{lead['company'].lower().replace(' ', '-')}.md"
            deck_filepath = os.path.join(output_dir, deck_filename)

            metrics = calculate_detailed_metrics(
                num_clubs=lead['num_clubs'],
                retention_lift_percent=lead['retention_lift'] or 0.03,
                avg_monthly_fee=lead['avg_monthly_fee'] or 15.0
            )

            deck_content = deck_template.format(
                company=lead['company'],
                region=lead['region'],
                num_clubs=lead['num_clubs'],
                lift_pct=int((lead['retention_lift'] or 0.03) * 100),
                base_ltv=metrics['base_ltv'],
                lifted_ltv=metrics['lifted_ltv'],
                annual_net_profit=metrics['annual_net_profit'],
                roi_multiple=metrics['roi_multiple']
            )

            with open(deck_filepath, 'w') as out:
                out.write(deck_content)

        print(f"Generated assets from DB for: {lead['company']}")

    conn.close()

if __name__ == "__main__":
    generate_personalized_assets()
