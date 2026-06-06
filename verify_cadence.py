from playwright.sync_api import sync_playwright, expect
import time
import os
import subprocess
from app import app, db
from models import Lead
from launch_outreach import launch_outreach

def setup_outreach_state():
    with app.app_context():
        # Ensure UK Fitness Corp is ready for outreach
        lead = Lead.query.get("UKF-1")
        if lead:
            lead.status = "Ready for Outreach"
            db.session.commit()

    # Run outreach engine to advance them to Tier 1
    launch_outreach()

def verify_cadence_ui():
    setup_outreach_state()

    # 1. Start the server
    server_process = subprocess.Popen(["python3", "app.py"], env=dict(os.environ, FLASK_DEBUG="false"))
    time.sleep(3) # Wait for server to start

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # 2. Login as Admin
            page.goto("http://127.0.0.1:5000/login")
            page.fill("input[name='username']", "admin")
            page.fill("input[name='password']", "admin123")
            page.click("button[type='submit']")

            # 3. Navigate to Leads Management
            page.goto("http://127.0.0.1:5000/admin/leads")

            # 4. Take a screenshot showing Tier 1 status
            expect(page.get_by_text("Tier 1")).to_be_visible()
            page.set_viewport_size({"width": 1280, "height": 800})
            page.screenshot(path="/home/jules/verification/cadence_active.png")
            print("Captured active cadence UI.")

            # 5. Click Pause
            pause_btn = page.locator("button:has-text('Pause')").first
            pause_btn.click()

            # 6. Verify "Paused" appears via HTMX
            expect(page.get_by_text("(Paused)")).to_be_visible()
            page.screenshot(path="/home/jules/verification/cadence_paused.png")
            print("Captured paused cadence UI.")

            # 7. Click Reset
            # Note: handle the confirm dialog
            page.on("dialog", lambda dialog: dialog.accept())
            reset_btn = page.locator("button:has-text('Reset')").first
            reset_btn.click()

            # 8. Verify status returns to "Ready for Outreach"
            expect(page.get_by_text("Ready for Outreach")).to_be_visible()
            page.screenshot(path="/home/jules/verification/cadence_reset.png")
            print("Captured reset cadence UI.")

            browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    if not os.path.exists("/home/jules/verification"):
        os.makedirs("/home/jules/verification")
    verify_cadence_ui()
