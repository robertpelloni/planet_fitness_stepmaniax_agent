
import os
import sqlite3
from app import app
from models import db, Lead, AuditLog

def verify_demo_request():
    with app.app_context():
        # 1. Create/Find a lead
        lead = Lead.query.first()
        if not lead:
            print("No lead found.")
            return

        token = lead.public_token
        print(f"Testing demo request for lead: {lead.company} (Token: {token})")

        # 2. Simulate POST request
        with app.test_client() as client:
            response = client.post(f'/admin/prospect/request-demo/{token}', data={
                'name': 'Test Requester',
                'email': 'test@example.com',
                'preferred_time': 'Tomorrow 10AM'
            })

            # 3. Verify Response
            if response.status_code == 200 and b"Request Received" in response.data:
                print("SUCCESS: Endpoint returned confirmation HTML.")
            else:
                print(f"FAILURE: Endpoint returned status {response.status_code}")
                return

        # 4. Verify DB State
        db.session.refresh(lead)
        if lead.status == 'Discovery Call Scheduled':
             print("SUCCESS: Lead status updated.")
        else:
             print(f"FAILURE: Lead status is {lead.status}")

        if "DEMO REQUESTED: Test Requester" in (lead.notes or ""):
             print("SUCCESS: Lead notes updated.")
        else:
             print("FAILURE: Lead notes not updated.")

if __name__ == "__main__":
    verify_demo_request()
