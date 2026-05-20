# Deployment Instructions

This project primarily consists of B2B sales collateral and documentation. However, it includes python utility scripts for data gathering (e.g., `scrape_leads.py`).

## Setup Environment
To run the lead generation tools locally, you must set up the Python environment:

1. Ensure Python 3.8+ is installed.
2. Create a virtual environment (optional but recommended):
   `python3 -m venv venv`
   `source venv/bin/activate`
3. Install the dependencies:
   `pip install -r requirements.txt`

## Running the Scraper
To execute the generic web scraper for Phase 2.1:
`python3 scrape_leads.py`
*(Note: You must first edit `scrape_leads.py` to point to a valid target directory and implement the site-specific parsing logic).*

## Secrets Management
If API keys, authentication cookies, or secrets become necessary for scraping (e.g., LinkedIn tokens), they must never be hard-coded or committed.
1. Create a `.env.example` file with placeholder variables.
2. Instruct operators to copy it to `.env` and fill in their credentials locally.