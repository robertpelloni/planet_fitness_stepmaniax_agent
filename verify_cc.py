
import asyncio
from playwright.async_api import async_playwright

async def verify_command_center():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Login as admin
        await page.goto("http://127.0.0.1:5000/login")
        await page.fill('input[name="username"]', 'admin')
        await page.fill('input[name="password"]', 'admin123')
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard")

        # Navigate to Command Center
        await page.goto("http://127.0.0.1:5000/admin/command-center")

        # Check title
        h1 = await page.inner_text("h1")
        print(f"H1: {h1}")

        # Check for Fleet Map section
        h3 = await page.inner_text("h3")
        print(f"H3 (Map): {h3}")

        # Screenshot
        await page.screenshot(path="command_center_verify.png")
        print("Screenshot saved.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_command_center())
