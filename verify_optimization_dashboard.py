import asyncio
from playwright.async_api import async_playwright
import os

async def verify_optimization_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 1. Login as Admin
        print("Logging in as admin...")
        await page.goto("http://localhost:5000/login")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin123")
        await page.click('button[type="submit"]')

        # 2. Navigate to Optimization Dashboard
        print("Navigating to Optimization Dashboard...")
        await page.goto("http://localhost:5000/admin/optimization")

        # 3. Take Screenshot
        await page.screenshot(path="v360_optimization_verify.png", full_page=True)
        print("Screenshot saved to v360_optimization_verify.png")

        # 4. Verify elements
        content = await page.content()
        if "Optimization Intelligence" in content and "Optimization Strategies" in content:
            print("SUCCESS: Optimization Dashboard elements verified.")
        else:
            print("FAILED: Optimization Dashboard elements not found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_optimization_dashboard())
