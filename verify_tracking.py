from playwright.sync_api import sync_playwright, expect
import time
import os
import subprocess
from app import app, db
from models import Lead

def verify_interaction_tracking():
    # 1. Start the server
    server_process = subprocess.Popen(["python3", "app.py"], env=dict(os.environ, FLASK_DEBUG="false"))
    time.sleep(3) # Wait for server to start

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # 2. Go to a prospect portal
            token = "token-canada"
            page.goto(f"http://127.0.0.1:5000/prospect/{token}")

            # 3. Trigger interaction
            clubs_slider = page.locator("#clubs-slider")
            clubs_slider.fill("150")
            time.sleep(1) # Wait for fetch

            # 4. Check database for interaction log in notes
            with app.app_context():
                lead = Lead.query.filter_by(public_token=token).first()
                print(f"Lead Notes: {lead.notes}")
                assert "HIGH INTENT: Prospect interacted with ROI Simulator." in (lead.notes or "")
                print("Interaction successfully tracked in DB.")

            browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    verify_interaction_tracking()
