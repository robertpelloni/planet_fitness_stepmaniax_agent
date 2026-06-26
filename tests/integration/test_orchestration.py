import pytest
from app import app, db
from models import Lead, AuditLog
from health_monitor import monitor_health
from launch_outreach import launch_outreach
from datetime import datetime, timedelta

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        pass
        yield app.test_client()

def test_health_monitor_orchestration(client):
    with app.app_context():
        # Setup a lead ready for outreach
        lead = Lead(id="ORCH-1", company="Orch Corp", status="Ready for Outreach", region="Michigan")
        db.session.add(lead)
        db.session.commit()

        # Trigger health monitor (which should call launch_outreach)
        monitor_health()

        updated_lead = Lead.query.get("ORCH-1")
        assert updated_lead.status == "Outreach Active"
        print("Health Monitor orchestration verified.")

def test_manual_forced_dispatch(client):
    with app.app_context():
        # Setup a lead that is ACTIVE but NOT DUE for follow-up yet
        last_contact = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        lead = Lead(id="FORCE-1", company="Force Corp", status="Outreach Active",
                    follow_up_count=1, last_contact_date=last_contact, region="Michigan")
        db.session.add(lead)
        db.session.commit()

        # Call launch_outreach normally (should skip)
        launch_outreach()
        assert Lead.query.get("FORCE-1").follow_up_count == 1

        # Call with forced ID
        launch_outreach(force_lead_id="FORCE-1")

        # Refresh to see changes from the other session/context
        db.session.expire_all()
        assert Lead.query.get("FORCE-1").follow_up_count == 2
        print("Manual forced dispatch verified.")
