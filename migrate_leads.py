import json
import sqlite3
import os
import re
import secrets

DB_PATH = 'crm.db'
CRM_JSON_PATH = 'crm.json'
LEADS_MD_PATH = 'LEADS.md'

def migrate_from_json():
    if not os.path.exists(CRM_JSON_PATH):
        print(f"{CRM_JSON_PATH} not found.")
        return

    with open(CRM_JSON_PATH, 'r') as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for lead in data.get('leads', []):
        lid = lead.get('id')
        company = lead.get('company')
        contact = lead.get('contact_name')
        title = lead.get('title')
        email = lead.get('email')
        region = lead.get('region')
        status = lead.get('status')
        priority = lead.get('priority')
        notes = lead.get('notes')

        roi = lead.get('roi_projection') or {}
        num_clubs = roi.get('num_clubs')
        retention_lift = roi.get('retention_lift', 0.03)
        avg_fee = roi.get('avg_monthly_fee', 15.0)
        profit = roi.get('projected_annual_profit')

        cursor.execute("SELECT id FROM leads WHERE id = ?", (lid,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE leads SET
                company=?, contact_name=?, title=?, email=?, region=?, status=?,
                priority=?, notes=?, num_clubs=?, retention_lift=?, avg_monthly_fee=?,
                projected_annual_profit=?
                WHERE id=?
            """, (company, contact, title, email, region, status, priority, notes, num_clubs, retention_lift, avg_fee, profit, lid))
            print(f"Updated lead: {company}")
        else:
            cursor.execute("""
                INSERT INTO leads (id, company, contact_name, title, email, region, status, priority, notes, num_clubs, retention_lift, avg_monthly_fee, projected_annual_profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (lid, company, contact, title, email, region, status, priority, notes, num_clubs, retention_lift, avg_fee, profit))
            print(f"Inserted lead: {company}")

    conn.commit()
    conn.close()

def migrate_from_md():
    if not os.path.exists(LEADS_MD_PATH):
        print(f"{LEADS_MD_PATH} not found.")
        return

    with open(LEADS_MD_PATH, 'r') as f:
        content = f.read()

    # Simple regex to find sections starting with ## <Number>. <Company Name>
    sections = re.split(r'\n## \d+\. ', content)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for section in sections[1:]: # Skip preamble
        lines = section.split('\n')
        company = lines[0].strip()

        # Try to find ID if it exists in DB already by matching company name
        cursor.execute("SELECT id FROM leads WHERE company = ?", (company,))
        row = cursor.fetchone()

        lid = row[0] if row else f"{company[:3].upper()}-{secrets.token_hex(2).upper()}" if 'secrets' in globals() else f"{company[:3].upper()}-NEW"

        # Basic parsing of the section
        metadata = {}
        for line in lines[1:]:
            if line.startswith('- **Base:**'): metadata['base'] = line.split('**Base:**')[1].strip()
            if line.startswith('- **Scale:**'): metadata['scale'] = line.split('**Scale:**')[1].strip()
            if line.startswith('- **CEO:**'): metadata['ceo'] = line.split('**CEO:**')[1].strip()
            if line.startswith('- **Website:**'): metadata['website'] = line.split('**Website:**')[1].strip()
            if line.startswith('- **LinkedIn:**'): metadata['linkedin'] = line.split('**LinkedIn:**')[1].strip()

        notes_str = f"MD Notes: {metadata.get('base', '')} | {metadata.get('scale', '')} | {metadata.get('website', '')}"

        if row:
            # Update notes or other fields if they are missing
            cursor.execute("UPDATE leads SET notes = notes || ? WHERE id = ?", (f" | {notes_str}", lid))
        else:
            # Insert new lead from MD
            cursor.execute("""
                INSERT INTO leads (id, company, contact_name, status, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (lid, company, metadata.get('ceo'), 'Identified', notes_str))
            print(f"Inserted new lead from MD: {company}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate_from_json()
    # migrate_from_md() # JSON is more reliable, MD parsing is heuristic
