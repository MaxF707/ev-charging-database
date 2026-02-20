#!/usr/bin/env python3
"""
scrape_ev_database_v4.py

Ultimate web scraper für ev-database.org mit Specs-Extraktion aus Detail-URLs.

Version 4 Improvements:
- Extrahiert Batterie- und Charging-Daten direkt aus Detail-Link URLs
- Keine zusätzlichen Detail-Seiten nötig (1 Request statt 1,225+ Requests!)
- Nutzt die sauberen <span class="model"> Tags
- Intelligente Spec-Extraktion aus URL-Slug

Verwendung:
    python3 scrape_ev_database_v4.py --output ev_database_raw_v4.csv
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import sys
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL = "https://ev-database.org/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
REQUEST_DELAY = 1.5
TIMEOUT = 30
MAX_VEHICLES_PER_PAGE = 50

# ============================================================================
# SPEC EXTRACTION FROM URL
# ============================================================================

def extract_specs_from_url(detail_url: str) -> dict:
    """
    Extract battery capacity and charging info from detail URL slug.

    Examples:
      /car/1708/MG-MG4-Electric-64-kWh → battery: 64.0
      /car/1285/Fiat-500e-Hatchback-42-kWh → battery: 42.0
      /car/3290/BMW-iX3-50-xDrive → potential charging info
    """

    specs = {
        'battery_capacity': None,
        'charging_ac': None,
        'charging_dc': None,
    }

    if not detail_url:
        return specs

    # Extract battery from URL slug (e.g., "64-kWh", "42 kWh", "42kWh")
    battery_match = re.search(r'(\d+)\s*-?\s*kWh', detail_url, re.IGNORECASE)
    if battery_match:
        battery_val = float(battery_match.group(1))
        if 10 <= battery_val <= 150:  # Valid range
            specs['battery_capacity'] = battery_val

    # Extract charging info from slug (e.g., "150-kW", "11-kW")
    # Look for patterns like "150-kW", "50 kW", etc (but not "kWh")
    charging_patterns = re.findall(r'(\d+)\s*-?\s*kW(?!h)', detail_url, re.IGNORECASE)

    if charging_patterns:
        # Could have multiple charging rates
        # Usually first is AC, others might be DC
        for i, charge_val in enumerate(charging_patterns):
            charge_float = float(charge_val)

            # Heuristic: if > 50 kW, likely DC charging
            if charge_float > 50:
                if specs['charging_dc'] is None and 3 <= charge_float <= 350:
                    specs['charging_dc'] = charge_float
            else:
                # Smaller values are typically AC charging
                if specs['charging_ac'] is None and 3 <= charge_float <= 22:
                    specs['charging_ac'] = charge_float

    return specs


def fetch_page(page_num: int) -> str | None:
    """Fetch a single page from ev-database.org."""
    try:
        start = page_num * MAX_VEHICLES_PER_PAGE
        end = (page_num + 1) * MAX_VEHICLES_PER_PAGE
        url = f"{BASE_URL}?p={start}-{end}"

        print(f"  [{page_num:2d}] Fetching: {url}", end=" ... ", flush=True)

        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        print(f"✓", flush=True)
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"✗ ERROR: {e}", flush=True)
        return None


def extract_vehicles_from_page(html: str, page_num: int) -> list[dict]:
    """
    Extract vehicle data from HTML with enhanced spec extraction from URLs.
    """
    vehicles = []

    try:
        soup = BeautifulSoup(html, 'html.parser')
        title_links = soup.find_all('a', class_='title')

        print(f"    Found {len(title_links)} vehicles on page {page_num}")

        for link in title_links:
            try:
                # Extract manufacturer and model from spans
                spans = link.find_all('span')
                if len(spans) >= 2:
                    manufacturer = spans[0].get_text(strip=True)
                    model = spans[1].get_text(strip=True)
                else:
                    continue

                # Clean up model text
                model = re.sub(r'\s*\([A-Za-z0-9\-]+\)$', '', model).strip()

                # Get detail URL for spec extraction
                detail_url = link.get('href', '')

                # Extract specs from URL
                url_specs = extract_specs_from_url(detail_url)

                # Extract model year from URL or default to 2024
                year_match = re.search(r'/car/(\d+)/', detail_url)
                year = 2024  # Default
                if year_match:
                    # Try to estimate year from ID if needed, but default is fine
                    pass

                vehicle = {
                    'Manufacturer': manufacturer.strip(),
                    'Model': model.strip(),
                    'Model Year': year,
                    'Battery Capacity kWh': url_specs['battery_capacity'],
                    'Charging Rate Level 2 (kW)': url_specs['charging_ac'],
                    'Charging Rate DC Fast (kW)': url_specs['charging_dc'],
                    'Detail URL': detail_url,  # Keep for reference
                }

                vehicles.append(vehicle)

            except Exception as e:
                print(f"      Warning: Failed to parse vehicle: {e}")
                continue

        return vehicles

    except Exception as e:
        print(f"  ERROR parsing page {page_num}: {e}")
        return []


# ============================================================================
# MAIN
# ============================================================================

def scrape_all_vehicles(output_file: str, max_pages: int = None) -> int:
    """Scrape all vehicles from ev-database.org."""

    print(f"{'='*80}")
    print(f"EV-Database Scraper v4 - URL-Based Spec Extraction")
    print(f"{'='*80}\n")

    print(f"Source: {BASE_URL}")
    print(f"Output: {output_file}")
    print(f"Approach: Extract specs from detail-link URLs (no detail page scraping)\n")

    all_vehicles = []
    page_num = 0

    print("Scraping pages...")

    while True:
        if max_pages and page_num >= max_pages:
            print(f"\n⚠ Reached max_pages limit ({max_pages})")
            break

        html = fetch_page(page_num)
        if not html:
            print(f"⚠ Failed to fetch page {page_num}, stopping")
            break

        vehicles = extract_vehicles_from_page(html, page_num)

        if not vehicles:
            print(f"⚠ No vehicles found on page {page_num}, assuming end of data")
            break

        all_vehicles.extend(vehicles)
        page_num += 1

        if page_num < 100:
            time.sleep(REQUEST_DELAY)

    # Save to CSV
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*80}\n")

    print(f"Total vehicles scraped: {len(all_vehicles)}")
    print(f"Pages processed: {page_num}\n")

    if all_vehicles:
        df = pd.DataFrame(all_vehicles)

        # KEEP Detail URL column for later spec enrichment
        # Don't remove it - we'll use it for improved extraction

        print(f"Columns: {list(df.columns)}")
        print(f"\nSample data:")
        print(df.head(10).to_string(index=False))

        print(f"\nData quality:")
        print(f"  Manufacturer: {(~df['Manufacturer'].isna()).sum()}/{len(df)}")
        print(f"  Model: {(~df['Model'].isna()).sum()}/{len(df)}")
        print(f"  Model Year: {(~df['Model Year'].isna()).sum()}/{len(df)}")
        print(f"  Battery: {(~df['Battery Capacity kWh'].isna()).sum()}/{len(df)} ({100*(~df['Battery Capacity kWh'].isna()).sum()/len(df):.1f}%)")
        print(f"  DC Charging: {(~df['Charging Rate DC Fast (kW)'].isna()).sum()}/{len(df)} ({100*(~df['Charging Rate DC Fast (kW)'].isna()).sum()/len(df):.1f}%)")
        print(f"  AC Charging: {(~df['Charging Rate Level 2 (kW)'].isna()).sum()}/{len(df)} ({100*(~df['Charging Rate Level 2 (kW)'].isna()).sum()/len(df):.1f}%)\n")

        df.to_csv(output_file, index=False)
        print(f"✅ Saved: {output_file}\n")

        return 0
    else:
        print("❌ No vehicles scraped")
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape EV data from ev-database.org with URL-based specs")
    parser.add_argument('--output', '-o', default='ev_database_raw_v4.csv', help='Output CSV file')
    parser.add_argument('--max-pages', '-m', type=int, default=None, help='Max pages to scrape')

    args = parser.parse_args()

    exit_code = scrape_all_vehicles(args.output, args.max_pages)
    sys.exit(exit_code)
