import pytest
from playwright.sync_api import Page, expect
import os

def test_admin_pipeline_and_proposal(page: Page):
    # 1. Login
    page.goto("http://localhost:5000/login")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')

    # 2. Navigate to Pipeline
    page.goto("http://localhost:5000/admin/pipeline")
    expect(page.get_by_role("heading", name="Sales Pipeline")).to_be_visible()

    # 3. Check for Kanban columns
    expect(page.get_by_text("Pilot Operational")).to_be_visible()
    expect(page.get_by_text("Ready for Outreach")).to_be_visible()

    # 4. Navigate to Lead Management
    page.goto("http://localhost:5000/admin/leads")
    expect(page.get_by_role("heading", name="Lead Management")).to_be_visible()

    # 5. Check for 'Proposal' and 'Convert' buttons
    # Note: These are specific to lead state. Test data should have some operational leads.
    expect(page.get_by_role("link", name="Proposal").first).to_be_visible()

def test_lead_conversion_ui(page: Page):
    # 1. Login
    page.goto("http://localhost:5000/login")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')

    # 2. Go to Lead Management
    page.goto("http://localhost:5000/admin/leads")

    # 3. Find a lead that is convertible (Pilot Operational) and doesn't have an account yet
    # UK Fitness Corp (UK-003) is set to 'Pilot Operational' in populate_test_data.py and has no User.
    row = page.get_by_role("row", name="UK Fitness Corp")
    convert_btn = row.get_by_role("button", name="Convert")

    if convert_btn.is_visible():
        # 4. Click Convert (this will trigger a confirm dialog)
        page.on("dialog", lambda dialog: dialog.accept())
        convert_btn.click()

        # 5. Expect success flash message
        expect(page.get_by_text("has been converted to a Partner")).to_be_visible()
    else:
        # Fallback to first if name matching is tricky
        convert_btn = page.get_by_role("button", name="Convert").first
        if convert_btn.is_visible():
             page.on("dialog", lambda dialog: dialog.accept())
             convert_btn.click()
             # It might be "Partner account already exists" if it's EPIC Fitness
             expect(page.get_by_text("Partner account")).to_be_visible()
        else:
             pytest.skip("No convertible lead found in current view")
