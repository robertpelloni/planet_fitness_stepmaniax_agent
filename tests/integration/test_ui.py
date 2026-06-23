import pytest
from playwright.sync_api import Page, expect

def test_admin_login_and_command_center(page: Page):
    # 1. Login
    page.goto("http://localhost:5000/login")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')

    expect(page).to_have_url("http://localhost:5000/admin/dashboard")

    # 2. Navigate to Command Center
    page.goto("http://localhost:5000/admin/command-center")
    expect(page.get_by_role("heading", name="Global Command Center")).to_be_visible()

    # 3. Verify KPI Grid
    expect(page.get_by_text("Total Fleet Units")).to_be_visible()
    expect(page.get_by_text("Fleet Avg Uptime")).to_be_visible()

def test_staff_dashboard_realtime(page: Page):
    # Login as admin (or staff if available)
    page.goto("http://localhost:5000/login")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')

    page.goto("http://localhost:5000/staff/dashboard")
    expect(page.get_by_role("heading", name="Staff Portal")).to_be_visible()

    # Check for HTMX-loaded content placeholders
    expect(page.get_by_text("Live Equipment Status")).to_be_visible()
    expect(page.get_by_text("Critical Alerts")).to_be_visible()
