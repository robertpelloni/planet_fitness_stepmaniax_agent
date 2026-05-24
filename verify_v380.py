import asyncio
from playwright.async_api import async_playwright
import os

async def verify_v380_crm_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Login as Admin
        print("Logging in as admin...")
        await page.goto("http://localhost:5000/login")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin123")
        await page.click('button[type="submit"]')

        # 2. View CRM Dashboard
        print("Viewing CRM Dashboard...")
        await page.goto("http://localhost:5000/dashboard")
        await page.screenshot(path="v380_crm_engagement.png", full_page=True)

        print("Screenshots saved.")

        # 3. Verify elements
        content = await page.content()
        if "Engagement" in content and "Views" in content:
            print("SUCCESS: Engagement metrics verified in CRM Dashboard.")
        else:
            print("FAILED: Engagement metrics not found in CRM Dashboard.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_v380_crm_dashboard())
