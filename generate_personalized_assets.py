import json
import os

def calculate_roi_metrics(num_clubs, retention_lift, avg_monthly_fee):
    """
    Helper to calculate ROI metrics for the asset generator,
    syncing with roi_calculator.py logic.
    """
    avg_member_lifetime_months = 18
    smx_monthly_cost_per_club = 600.0
    members_per_club = 6000 # Sample size
    total_members = num_clubs * members_per_club

    base_ltv = avg_monthly_fee * avg_member_lifetime_months
    lifted_lifetime_months = avg_member_lifetime_months * (1 + retention_lift)
    lifted_ltv = avg_monthly_fee * lifted_lifetime_months

    total_portfolio_value_gain = (total_members * lifted_ltv) - (total_members * base_ltv)
    annual_revenue_gain = total_portfolio_value_gain / (lifted_lifetime_months / 12)

    total_annual_cost = num_clubs * smx_monthly_cost_per_club * 12
    annual_net_profit = annual_revenue_gain - total_annual_cost
    roi_multiple = annual_revenue_gain / total_annual_cost if total_annual_cost > 0 else 0

    return {
        "base_ltv": round(base_ltv, 2),
        "lifted_ltv": round(lifted_ltv, 2),
        "annual_net_profit": round(annual_net_profit, 2),
        "roi_multiple": round(roi_multiple, 2)
    }

def generate_personalized_assets(crm_file="crm.json", output_dir="outreach/generated"):
    """
    Generates personalized outreach emails and pitch decks based on lead data in crm.json.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(crm_file, 'r') as f:
        data = json.load(f)

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

    for lead in data['leads']:
        if lead['status'] == "Ready for Outreach":
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
            if lead.get('roi_projection'):
                deck_filename = f"pitch-{lead['company'].lower().replace(' ', '-')}.md"
                deck_filepath = os.path.join(output_dir, deck_filename)

                roi_data = lead['roi_projection']
                metrics = calculate_roi_metrics(
                    num_clubs=roi_data.get('num_clubs', 1),
                    retention_lift=roi_data.get('retention_lift', 0.03),
                    avg_monthly_fee=roi_data.get('avg_monthly_fee', 15.0)
                )

                deck_content = deck_template.format(
                    company=lead['company'],
                    region=lead['region'],
                    num_clubs=roi_data.get('num_clubs', 1),
                    lift_pct=int(roi_data.get('retention_lift', 0.03) * 100),
                    base_ltv=metrics['base_ltv'],
                    lifted_ltv=metrics['lifted_ltv'],
                    annual_net_profit=metrics['annual_net_profit'],
                    roi_multiple=metrics['roi_multiple']
                )

                with open(deck_filepath, 'w') as out:
                    out.write(deck_content)

            print(f"Generated assets for: {lead['company']}")

if __name__ == "__main__":
    generate_personalized_assets()
