from playwright.sync_api import Page, expect, sync_playwright
import subprocess
import time
import os

def test_pilot_success_ui(page: Page):
    # 1. Login as Admin
    page.goto("http://localhost:5000/login")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')

    # 2. Navigate to Pilot Success Dashboard
    page.goto("http://localhost:5000/admin/pilot-success")

    # Check for heading
    expect(page.get_by_role("heading", name="PILOT SUCCESS DASHBOARD")).to_be_visible()

    # Check for table and some data
    expect(page.get_by_text("Active Pilot Tracking")).to_be_visible()

    # Take Screenshot
    page.screenshot(path="/home/jules/verification/pilot_success_verified.png")
    print("Verification screenshot saved to /home/jules/verification/pilot_success_verified.png")

if __name__ == "__main__":
    # Reset DB
    subprocess.run(["python3", "populate_test_data.py"])

    # Start server
    proc = subprocess.Popen(["python3", "app.py"], env=dict(os.environ, FLASK_DEBUG="false"))
    time.sleep(3)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            test_pilot_success_ui(page)
            browser.close()
    finally:
        proc.terminate()
