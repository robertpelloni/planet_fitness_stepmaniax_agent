import json
import os

def generate_personalized_assets(crm_file="crm.json", output_dir="outreach/generated"):
    """
    Generates personalized outreach emails based on lead data in crm.json.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(crm_file, 'r') as f:
        data = json.load(f)

    template = """# Personalized Outreach: {company}

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

    for lead in data['leads']:
        if lead['status'] == "Ready for Outreach":
            filename = f"{lead['company'].lower().replace(' ', '-')}.md"
            filepath = os.path.join(output_dir, filename)

            content = template.format(
                company=lead['company'],
                contact_name=lead['contact_name'],
                title=lead['title'],
                email=lead['email'],
                region=lead['region']
            )

            with open(filepath, 'w') as out:
                out.write(content)
            print(f"Generated asset: {filepath}")

if __name__ == "__main__":
    generate_personalized_assets()
