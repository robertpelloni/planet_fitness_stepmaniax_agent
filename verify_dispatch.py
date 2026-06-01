from playwright.sync_api import sync_playwright, expect
import time
import os
import subprocess
from app import app, db
from models import Lead

def verify_manual_dispatch_ui():
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

            # 3. Navigate to Leads Management (Clear region filter)
            page.goto("http://127.0.0.1:5000/admin/leads")

            # 4. Take a screenshot showing "Dispatch Initial" for Ready leads
            expect(page.get_by_text("Lead Management")).to_be_visible()

            # Use exact match or case-insensitive for the button text
            btn = page.locator("button:has-text('Dispatch Initial')").first
            expect(btn).to_be_visible()

            page.set_viewport_size({"width": 1280, "height": 800})
            page.screenshot(path="/home/jules/verification/dispatch_ui.png")
            print("Captured manual dispatch UI.")

            # 5. Verify Status Dropdown
            expect(page.locator("select[name='status']").first).to_be_visible()

            browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    verify_manual_dispatch_ui()
