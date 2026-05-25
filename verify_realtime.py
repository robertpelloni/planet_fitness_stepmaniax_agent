import asyncio
from playwright.async_api import async_playwright
import requests
import json
import time

def ingest_telemetry():
    url = "http://localhost:5000/api/v1/telemetry"
    headers = {"X-API-KEY": "dev-api-key-999"} # Assuming this is the key from config.py
    data = {
        "equipment_id": 1,
        "member_id": 1,
        "scans_increment": 5
    }
    r = requests.post(url, headers=headers, json=data)
    print(f"Telemetry ingestion status: {r.status_code}")

async def verify_realtime_updates():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto("http://localhost:5000/login")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin123")
        await page.click('button[type="submit"]')

        # Go to Manager Dashboard
        await page.goto("http://localhost:5000/manager/dashboard")

        # Initial check
        initial_content = await page.content()

        # Ingest telemetry
        ingest_telemetry()

        # Wait for HTMX or manual refresh (since manager dashboard doesn't have polling yet)
        # Actually, let's refresh the page to see the new activity
        await page.reload()

        await page.wait_for_selector('span:has-text("5 Scans")')
        print("Real-time update (via refresh) verified: New telemetry scans visible.")

        # Take screenshot
        await page.screenshot(path="v390_manager_realtime_verify.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    verify_realtime_updates_async = verify_realtime_updates()
    asyncio.run(verify_realtime_updates_async)
