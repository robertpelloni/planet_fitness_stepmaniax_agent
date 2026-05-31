from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import time
import os

# Target URLs for Planet Fitness Franchise Groups
TARGET_GROUPS = [
    {"name": "National Fitness Partners", "url": "https://www.nfpfit.com/our-team"},
    {"name": "Excel Fitness", "url": "https://www.excelfitness.com/leadership"}, # Inferred
    {"name": "Grand Fitness Partners", "url": "https://grandfitnesspartners.com/team"}, # Inferred
    {"name": "United Fitness Partners", "url": "https://pffranchisee.org/united-fp-rings-in-the-new-year-with-big-leadership-changes/"},
    {"name": "United Fitness Partners", "url": "https://www.unitedpf.com/leadership/"}, # Updated URL
    {"name": "Flynn Group", "url": "https://flynn.com/flynn-fitness/"},
    {"name": "CDM Fitness Holdings", "url": "https://www.fitearth.com/"},
    {"name": "Ohana Growth Partners", "url": "https://www.ohanagp.com/team"},
    {"name": "EPIC Fitness Group", "url": "https://www.epicfitnessgroup.com/"}
]

OUTPUT_FILE = "franchise_leads.csv"

def scrape_leadership(group):
    """
    Scrapes a franchise group's leadership/team page.
    """
def is_junk(text):
    junk_keywords = [
        "lorem", "ipsum", "dolor", "sit", "amet",
        "locations totals", "loading details", "loading location",
        "apply now", "join our team", "careers",
        "premier zone", "judgement free", "all rights reserved"
    ]
    if not text: return True
    text_lower = text.lower()
    if any(junk in text_lower for junk in junk_keywords): return True
    if len(text) < 3 or len(text) > 100: return True
    return False

def scrape_leadership_playwright(browser, group):
    name = group['name']
    url = group['url']
    print(f"--- Scraping {name} via Playwright at {url} ---")

    page = browser.new_page()
    try:
        page.goto(url, wait_until="load", timeout=30000)
        # Scroll to ensure dynamic content loads
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        content = page.content()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []
    finally:
        page.close()

    soup = BeautifulSoup(content, 'html.parser')
    leads = []

    # NFP Specific Parsing
    if "nfpfit.com" in url:
        # Common pattern: h3/h4 for names, p/span for titles
        for person in soup.find_all(['h3', 'h4']):
            full_name = person.text.strip()
            title_tag = person.find_next(['p', 'span'])
            title = title_tag.text.strip() if title_tag else "Leadership"
            if len(full_name.split()) > 1 and not is_junk(full_name):
                leads.append({'Franchise Group': name, 'Name': full_name, 'Title': title})

    # Ohana Growth Partners Parsing
    elif "ohanagp.com" in url:
        # Often uses cards with names and titles
        for person in soup.find_all(['h5', 'h4']):
            full_name = person.text.strip()
            title_tag = person.find_next(['p', 'span', 'div'])
            title = title_tag.text.strip() if title_tag else "Leadership"
            if len(full_name.split()) > 1 and not is_junk(full_name):
                leads.append({'Franchise Group': name, 'Name': full_name, 'Title': title})

    # Flynn Group Parsing
    elif "flynn.com" in url:
        for person in soup.find_all(['h3', 'strong']):
            full_name = person.text.strip()
            if len(full_name.split()) > 1 and not is_junk(full_name):
                leads.append({'Franchise Group': name, 'Name': full_name, 'Title': "Leadership"})

    # United FP / PFIFC Specific Parsing
    elif "pffranchisee.org" in url or "unitedpf.com" in url:
        content = soup.find('div', class_='entry-content') or soup.find('main') or soup.body
        if content:
            for item in content.find_all(['h2', 'h3', 'h4', 'strong']):
                text = item.text.strip()
                if len(text.split()) > 1 and not is_junk(text):
                    leads.append({'Franchise Group': name, 'Name': text, 'Title': "Executive"})

    # Generic Fallback
    else:
        print(f"No specific parser for {url}, using generic heuristic.")
        for item in soup.find_all(['h2', 'h3', 'h4']):
            text = item.text.strip()
            if not is_junk(text) and len(text.split()) > 1:
                leads.append({'Franchise Group': name, 'Name': text, 'Title': "Leadership"})

    print(f"Found {len(leads)} potential leads for {name}.")
    return leads
    # Improved Parsing Heuristics
    # Look for common containers like 'team-member', 'person', 'staff'
    potential_leads = []

    # Try finding elements with 'CEO', 'President', 'Director', 'Manager'
    keywords = ["CEO", "President", "Director", "Manager", "Founder", "VP", "Vice President"]

    for tag in soup.find_all(['h2', 'h3', 'h4', 'h5', 'strong']):
        text = tag.get_text(separator=' ').strip()
        if is_junk(text): continue

        # Check if this element or its siblings contain a leadership keyword
        parent = tag.parent
        combined_text = parent.get_text(separator=' ')

        if any(kw in combined_text for kw in keywords):
            # Attempt to extract Name and Title
            # Usually the heading is the name
            full_name = text
            # Find the title (often in a p or span sibling or child)
            title = "Leadership"
            for sibling in tag.find_next_siblings(['p', 'span', 'div']):
                sib_text = sibling.get_text().strip()
                if any(kw in sib_text for kw in keywords):
                    title = sib_text
                    break

            if len(full_name.split()) > 1 and len(full_name.split()) < 5:
                leads.append({'Franchise Group': name, 'Name': full_name, 'Title': title})

    # Deduplicate
    unique_leads = []
    seen = set()
    for lead in leads:
        key = (lead['Name'], lead['Franchise Group'])
        if key not in seen:
            unique_leads.append(lead)
            seen.add(key)

    print(f"Found {len(unique_leads)} potential leads for {name}.")
    return unique_leads

def save_to_csv(leads, filename):
    if not leads:
        print("No leads found to save.")
        return
    keys = leads[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(leads)
    print(f"Saved {len(leads)} leads to {filename}")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        all_leads = []
        for group in TARGET_GROUPS:
            all_leads.extend(scrape_leadership_playwright(browser, group))
        browser.close()
    save_to_csv(all_leads, OUTPUT_FILE)
