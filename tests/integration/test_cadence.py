import pytest
from datetime import datetime, timedelta
from app import app, db
from models import Lead, OutreachLog
from launch_outreach import launch_outreach
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        pass
        yield app.test_client()

def test_initial_outreach(client):
    with app.app_context():
        lead = Lead(id="TEST-1", company="Test Corp", contact_name="John", status="Ready for Outreach", region="Michigan", follow_up_count=0)
        db.session.add(lead)
        db.session.commit()

        launch_outreach()

        updated_lead = Lead.query.get("TEST-1")
        assert updated_lead.status == "Outreach Active"
        assert updated_lead.follow_up_count == 1
        assert updated_lead.last_contact_date is not None

def test_day3_followup_timing(client):
    with app.app_context():
        # Last contact 2 days ago (Should NOT trigger)
        last_contact = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        lead = Lead(id="TEST-2", company="Test Corp", contact_name="John", status="Outreach Active",
                    region="Michigan", follow_up_count=1, last_contact_date=last_contact)
        db.session.add(lead)
        db.session.commit()

        launch_outreach()

        updated_lead = Lead.query.get("TEST-2")
        assert updated_lead.follow_up_count == 1 # Still Tier 1

        # Last contact 3.1 days ago (Should trigger)
        last_contact = (datetime.now() - timedelta(days=3.1)).strftime("%Y-%m-%d %H:%M:%S")
        updated_lead.last_contact_date = last_contact
        db.session.commit()

        launch_outreach()

        updated_lead = Lead.query.get("TEST-2")
        assert updated_lead.follow_up_count == 2
        assert updated_lead.status == "Outreach Active"

def test_cadence_paused(client):
    with app.app_context():
        last_contact = (datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
        lead = Lead(id="TEST-3", company="Test Corp", contact_name="John", status="Outreach Active",
                    region="Michigan", follow_up_count=1, last_contact_date=last_contact, cadence_paused=True)
        db.session.add(lead)
        db.session.commit()

        launch_outreach()

        updated_lead = Lead.query.get("TEST-3")
        assert updated_lead.follow_up_count == 1 # Should not have progressed

def test_cadence_exhaustion(client):
    with app.app_context():
        last_contact = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d %H:%M:%S")
        lead = Lead(id="TEST-4", company="Test Corp", contact_name="John", status="Outreach Active",
                    region="Michigan", follow_up_count=3, last_contact_date=last_contact)
        db.session.add(lead)
        db.session.commit()

        launch_outreach()

        updated_lead = Lead.query.get("TEST-4")
        assert updated_lead.status == "Outreach Exhausted"
        assert updated_lead.follow_up_count == 4
