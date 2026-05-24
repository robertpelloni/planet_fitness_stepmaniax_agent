import asyncio
from playwright.async_api import async_playwright
import os

async def verify_predictive_dashboards():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Login as Admin
        print("Logging in as admin...")
        await page.goto("http://localhost:5000/login")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin123")
        await page.click('button[type="submit"]')

        # 2. Navigate to Command Center
        print("Navigating to Command Center...")
        await page.goto("http://localhost:5000/admin/command-center")
        await page.screenshot(path="v370_command_center_predictive.png", full_page=True)

        # 3. Navigate to Facility Ops
        print("Navigating to Facility Ops...")
        await page.goto("http://localhost:5000/staff/operations")
        await page.screenshot(path="v370_facility_ops_predictive.png", full_page=True)

        print("Screenshots saved.")

        # 4. Verify elements
        content = await page.content()
        if "Stability" in content:
            print("SUCCESS: Stability metrics verified in UI.")
        else:
            print("FAILED: Stability metrics not found in UI.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_predictive_dashboards())
