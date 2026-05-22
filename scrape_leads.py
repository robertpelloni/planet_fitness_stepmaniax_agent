import requests
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
]

OUTPUT_FILE = "franchise_leads.csv"

def scrape_leadership(group):
    """
    Scrapes a franchise group's leadership/team page.
    """
    name = group['name']
    url = group['url']
    print(f"--- Scraping {name} at {url} ---")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    leads = []

    # NFP Specific Parsing
    if "nfpfit.com" in url:
        # Based on search snippet: Meet the NFP Leadership Team
        # Common pattern: h3 or h4 for names, p or span for titles
        for person in soup.find_all(['h3', 'h4']):
            full_name = person.text.strip()
            title = person.find_next(['p', 'span']).text.strip() if person.find_next(['p', 'span']) else "Unknown"
            if len(full_name.split()) > 1: # Basic filter for noise
                leads.append({'Franchise Group': name, 'Name': full_name, 'Title': title})

    # United FP / PFIFC Specific Parsing
    elif "pffranchisee.org" in url:
        # Looking for names mentioned in the article
        content = soup.find('div', class_='entry-content') or soup.body
        if content:
            # Simple heuristic: capitalized names near titles like CEO, CFO, VP
            text = content.get_text()
            keywords = ["CEO", "CFO", "President", "VP", "Director"]
            # This is a bit complex for a simple scraper, so we might just log that we found content
            print(f"Found article content for {name}, manually extracting top names for LEADS.md")

    # Generic Fallback
    else:
        print(f"No specific parser for {url}, using generic heuristic.")
        for item in soup.find_all(['h2', 'h3']):
            text = item.text.strip()
            if any(key in text for key in ["Team", "Leadership", "Executive"]):
                continue
            leads.append({'Franchise Group': name, 'Name': text, 'Title': "Consult LEADS.md"})

    print(f"Found {len(leads)} potential leads for {name}.")
    return leads

def save_to_csv(leads, filename):
    """
    Saves the extracted leads to a CSV file.
    """
    if not leads:
        print("No leads found to save in this run.")
        return

    keys = leads[0].keys()
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(leads)
        print(f"Successfully saved leads to {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    all_leads = []
    for group in TARGET_GROUPS:
        time.sleep(1) # Polite delay
        all_leads.extend(scrape_leadership(group))

    save_to_csv(all_leads, OUTPUT_FILE)
