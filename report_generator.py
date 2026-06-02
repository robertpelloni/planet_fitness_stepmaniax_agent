import os
from datetime import datetime, timedelta
from app import app, db
from models import Lead, EquipmentMetric, Member, TelemetryHistory, OutreachLog

TEMPLATE_PATH = "pilot-performance-report.md"
WEEKLY_TEMPLATE_PATH = "weekly-pilot-summary-template.md"
COMMERCIAL_TEMPLATE_PATH = "commercial-proposal-template.md"
REPORTS_DIR = "outreach/reports"
WEEKLY_REPORTS_DIR = "outreach/reports/weekly"
PROPOSALS_DIR = "outreach/proposals"

def generate_report(unit_id):
    """
    Generates a personalized pilot performance report for a specific unit (v7.8.0 SQLAlchemy).
    """
    with app.app_context():
        if not os.path.exists(REPORTS_DIR):
            os.makedirs(REPORTS_DIR)

        # 1. Fetch Unit Data
        unit = db.session.get(EquipmentMetric, unit_id)
        if not unit:
            print(f"Error: Unit ID {unit_id} not found.")
            return

        # 2. Fetch Onboarding Data
        total_onboarded = Member.query.filter_by(franchise_id=unit.franchise_id).count()
        completed_onboarding = Member.query.filter_by(franchise_id=unit.franchise_id, onboarding_status='Completed').count()
        conv_rate = (completed_onboarding / total_onboarded * 100) if total_onboarded > 0 else 0

        # 3. Prepare Data
        report_data = {
            "[Date]": datetime.now().strftime("%Y-%m-%d"),
            "[Unit ID]": unit.equipment_name,
            "[Location]": unit.location,
            "[Uptime %]": f"{unit.uptime_percent}%",
            "[Total Scans]": str(unit.total_scans),
            "[Avg Session Duration]": f"{unit.avg_session_duration} minutes",
            "[Actual]": str(unit.total_scans),
            "[Onboarding Conversion]": f"{conv_rate:.1f}%",
            "[Total Registered Members]": str(total_onboarded)
        }

        # 4. Read Template
        if not os.path.exists(TEMPLATE_PATH):
            print(f"Error: Template {TEMPLATE_PATH} not found.")
            return

        with open(TEMPLATE_PATH, "r") as f:
            content = f.read()

        # 5. Replace Placeholders
        for key, value in report_data.items():
            content = content.replace(key, value)

        # 6. Save Report
        filename = f"Performance_Report_{unit.equipment_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(REPORTS_DIR, filename)

        with open(filepath, "w") as f:
            f.write(content)

        print(f"Report generated: {filepath}")
        return filepath

def generate_weekly_summary(franchise_id):
    """
    Generates an aggregate weekly performance summary for a franchise (v7.8.0 SQLAlchemy).
    """
    with app.app_context():
        if not os.path.exists(WEEKLY_REPORTS_DIR):
            os.makedirs(WEEKLY_REPORTS_DIR)

        # 1. Fetch Franchise
        franchise = db.session.get(Lead, franchise_id)
        if not franchise:
            print(f"Error: Franchise ID {franchise_id} not found.")
            return

        # 2. Last 7 Days Scans
        last_week = datetime.now() - timedelta(days=7)
        unit_ids = [u.id for u in EquipmentMetric.query.filter_by(franchise_id=franchise_id).all()]

        stats = db.session.query(
            db.func.sum(TelemetryHistory.scans_count),
            db.func.avg(TelemetryHistory.duration_minutes)
        ).filter(
            TelemetryHistory.equipment_id.in_(unit_ids),
            TelemetryHistory.timestamp >= last_week.strftime("%Y-%m-%d %H:%M:%S")
        ).first()

        total_scans = stats[0] or 0
        avg_intensity = round(stats[1] or 0, 1)

        # 3. Avg Uptime
        avg_uptime = db.session.query(db.func.avg(EquipmentMetric.uptime_percent))\
            .filter_by(franchise_id=franchise_id).scalar() or 0
        avg_uptime = round(avg_uptime, 1)

        # 4. Active Pilot Members
        active_members = Member.query.filter_by(franchise_id=franchise_id, onboarding_status='Completed').count()

        # 5. Prepare Data
        report_data = {
            "[Franchise Name]": franchise.company,
            "[Week Ending]": datetime.now().strftime("%Y-%m-%d"),
            "[Total Weekly Scans]": str(total_scans),
            "[Trend]": "Rising" if total_scans > 100 else "Stable",
            "[Avg Uptime]": str(avg_uptime),
            "[Uptime Status]": "Optimal" if avg_uptime > 98 else "Action Required",
            "[Active Members]": str(active_members),
            "[Intensity]": str(avg_intensity),
            "[Engagement Trend Description]": f"Weekly scan volume reached {total_scans} with an average session intensity of {avg_intensity} scans per minute.",
            "[Operational Notes]": f"Fleet uptime averaged {avg_uptime}% over the past 7 days.",
            "[Weekly Recommendation]": "Maintain current pilot parameters and focus on Gen-Z onboarding conversion."
        }

        # 6. Read Template
        if not os.path.exists(WEEKLY_TEMPLATE_PATH):
            print(f"Error: Template {WEEKLY_TEMPLATE_PATH} not found.")
            return

        with open(WEEKLY_TEMPLATE_PATH, "r") as f:
            content = f.read()

        # 7. Replace Placeholders
        for key, value in report_data.items():
            content = content.replace(key, value)

        # 8. Save Report
        filename = f"Weekly_Summary_{franchise.company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(WEEKLY_REPORTS_DIR, filename)

        with open(filepath, "w") as f:
            f.write(content)

        # Log to OutreachLog
        log = OutreachLog(
            lead_id=franchise_id,
            date_sent=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            channel='Automated Report',
            notes=f"Generated weekly summary: {filename}"
        )
        db.session.add(log)
        db.session.commit()

        print(f"Weekly Summary generated: {filepath}")
        return filepath

def generate_commercial_proposal(lead_id):
    """
    Generates a tailored commercial expansion proposal for a lead (v7.8.0 SQLAlchemy).
    """
    with app.app_context():
        if not os.path.exists(PROPOSALS_DIR):
            os.makedirs(PROPOSALS_DIR)

        # 1. Fetch Lead Data
        lead = db.session.get(Lead, lead_id)
        if not lead:
            print(f"Error: Lead ID {lead_id} not found.")
            return

        # 2. Fetch Pilot Location
        equipment = EquipmentMetric.query.filter_by(franchise_id=lead_id).first()
        pilot_location = equipment.location if equipment else "your primary pilot facility"

        # 3. Prepare Data
        report_data = {
            "[Franchisee Name]": lead.company,
            "[Pilot Location]": pilot_location
        }

        # 4. Read Template
        if not os.path.exists(COMMERCIAL_TEMPLATE_PATH):
            print(f"Error: Template {COMMERCIAL_TEMPLATE_PATH} not found.")
            return

        with open(COMMERCIAL_TEMPLATE_PATH, "r") as f:
            content = f.read()

        # 5. Replace Placeholders
        for key, value in report_data.items():
            content = content.replace(key, value)

        # 6. Save Proposal
        filename = f"Commercial_Proposal_{lead.company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(PROPOSALS_DIR, filename)

        with open(filepath, "w") as f:
            f.write(content)

        # Log to OutreachLog
        log = OutreachLog(
            lead_id=lead_id,
            date_sent=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            channel='Commercial Proposal',
            notes=f"Generated commercial proposal: {filename}"
        )
        db.session.add(log)
        db.session.commit()

        print(f"Commercial Proposal generated: {filepath}")
        return filepath

if __name__ == "__main__":
    generate_report(1)
