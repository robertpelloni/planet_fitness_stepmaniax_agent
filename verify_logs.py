import asyncio
from playwright.async_api import async_playwright

async def verify_command_center_logs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Login as Admin
        await page.goto("http://localhost:5000/login")
        await page.fill('input[name="username"]', "admin")
        await page.fill('input[name="password"]', "admin123")
        await page.click('button[type="submit"]')

        # Go to Command Center
        await page.goto("http://localhost:5000/admin/command-center")

        # Check for Log Stream component
        await page.wait_for_selector('h3:has-text("System Log Stream")')

        # Check if content updates from "Initializing stream..."
        # We might need to wait a few seconds for the first poll
        await page.wait_for_timeout(6000)

        log_content = await page.inner_text('div[hx-get*="/admin/api/logs"]')
        print(f"Log content retrieved: {log_content[:50]}...")

        if "Waiting for system logs..." in log_content or "server.log" in log_content:
            print("SUCCESS: System Log Stream verified.")
        else:
            print("FAILED: System Log Stream content not as expected.")

        # Take screenshot
        await page.screenshot(path="v390_command_center_logs_verify.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_command_center_logs())
