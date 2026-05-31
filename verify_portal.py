from playwright.sync_api import sync_playwright, expect
import time
import os
import subprocess

def verify_prospect_portal():
    # 1. Start the server
    server_process = subprocess.Popen(["python3", "app.py"], env=dict(os.environ, FLASK_DEBUG="false"))
    time.sleep(3) # Wait for server to start

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # 2. Go to a prospect portal
            page.goto("http://127.0.0.1:5000/prospect/token-canada")

            # 3. Verify ROI Simulator is visible
            expect(page.get_by_text("Interactive ROI Simulator")).to_be_visible()

            # 4. Interact with sliders
            clubs_slider = page.locator("#clubs-slider")
            clubs_slider.fill("100")

            # 5. Check if profit value updated
            time.sleep(1)

            page.set_viewport_size({"width": 1280, "height": 1000})
            page.screenshot(path="/home/jules/verification/prospect_portal_simulator.png")
            print("Captured prospect portal with ROI simulator.")

            browser.close()
    finally:
        server_process.terminate()

if __name__ == "__main__":
    if not os.path.exists("/home/jules/verification"):
        os.makedirs("/home/jules/verification")
    verify_prospect_portal()
