#!/usr/bin/env python3
"""
enrich_from_detail_pages_v5.py

Enriches EV data by fetching specs from detail pages in parallel.
Uses multi-threading to maximize efficiency while respecting rate limits.

Fetches battery capacity and charging rates from:
- https://ev-database.org/car/1708/MG-MG4-Electric-64-kWh
- etc.

Verwendung:
    python3 enrich_from_detail_pages_v5.py \
        --input ev_database_normalized_v4.csv \
        --output ev_database_enriched_details.csv \
        --workers 5 \
        --max-vehicles 100
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from collections import defaultdict

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
TIMEOUT = 15
REQUEST_DELAY = 0.3  # Zwischen Requests

# ============================================================================
# SPEC EXTRACTION
# ============================================================================

def extract_specs_from_detail_html(html: str) -> dict:
    """Extract battery and charging specs from detail page HTML."""

    specs = {
        'battery_capacity': None,
        'charging_ac': None,
        'charging_dc': None,
    }

    if not html:
        return specs

    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()

        # ===== BATTERIE CAPACITY =====
        # Patterns: "108.7 kWh", "115.0 kWh"
        battery_match = re.search(r'(\d+(?:\.\d+)?)\s*kWh(?:\s+Useable)?', text)
        if battery_match:
            battery_val = float(battery_match.group(1))
            if 10 <= battery_val <= 150:
                specs['battery_capacity'] = battery_val

        # ===== AC CHARGING =====
        # Patterns: "11 kW AC", "11.0 kW On-Board"
        ac_match = re.search(r'(\d+(?:\.\d+)?)\s*kW\s+(?:AC|On-Board)', text, re.IGNORECASE)
        if ac_match:
            ac_val = float(ac_match.group(1))
            if 3 <= ac_val <= 22:
                specs['charging_ac'] = ac_val

        # ===== DC CHARGING =====
        # Patterns: "400 kW DC", "230 kW DC", "350 kW DC"
        # Find the MAIN DC rate (usually first or max value)
        dc_matches = re.findall(r'(\d+(?:\.\d+)?)\s*kW\s+DC', text, re.IGNORECASE)
        if dc_matches:
            # Use first occurrence (usually the main charging capability)
            dc_val = float(dc_matches[0])
            if 50 <= dc_val <= 350:  # DC is typically > 50 kW
                specs['charging_dc'] = dc_val

        return specs

    except Exception as e:
        print(f"      Error parsing HTML: {e}")
        return specs


def fetch_detail_page(detail_url: str, request_delay: float = 0.3) -> str | None:
    """Fetch a single detail page."""

    if not detail_url:
        return None

    try:
        full_url = f"https://ev-database.org{detail_url}" if detail_url.startswith('/') else detail_url

        time.sleep(request_delay)  # Rate limiting

        response = requests.get(full_url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        return response.text

    except Exception as e:
        return None


def enrich_single_vehicle(index: int, row: pd.Series, request_delay: float = 0.3) -> tuple[int, dict]:
    """
    Enrich a single vehicle by fetching detail page.

    Returns:
        (index, specs_dict)
    """

    detail_url = row.get('Detail URL', '') if hasattr(row, 'get') else row['Detail URL']

    html = fetch_detail_page(detail_url, request_delay)
    specs = extract_specs_from_detail_html(html) if html else {}

    return (index, specs)


# ============================================================================
# MAIN
# ============================================================================

def enrich_from_details(input_file: str, output_file: str, workers: int = 5, max_vehicles: int = None) -> int:
    """
    Enrich vehicle specs by fetching detail pages in parallel.
    """

    print(f"{'='*80}")
    print(f"EV Database - Enrichment from Detail Pages (v5)")
    print(f"{'='*80}\n")

    # Load data
    try:
        print(f"Lade: {input_file}")
        df = pd.read_csv(input_file)
        print(f"✅ {len(df)} Zeilen geladen\n")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Limit vehicles if specified
    if max_vehicles:
        df = df.iloc[:max_vehicles]
        print(f"⚠ Limited to {max_vehicles} vehicles\n")

    print(f"Datenqualität VORHER:")
    battery_missing = df['Battery Capacity kWh'].isna().sum()
    dc_missing = df['Charging Rate DC Fast (kW)'].isna().sum()
    ac_missing = df['Charging Rate Level 2 (kW)'].isna().sum()

    print(f"  Battery: {len(df) - battery_missing}/{len(df)} ({100*(len(df)-battery_missing)/len(df):.1f}%)")
    print(f"  DC Charging: {len(df) - dc_missing}/{len(df)} ({100*(len(df)-dc_missing)/len(df):.1f}%)")
    print(f"  AC Charging: {len(df) - ac_missing}/{len(df)} ({100*(len(df)-ac_missing)/len(df):.1f}%)\n")

    # Find vehicles that need enrichment (with Detail URL)
    needs_details = (
        (df['Battery Capacity kWh'].isna() | df['Charging Rate DC Fast (kW)'].isna()) &
        (df['Detail URL'].notna())
    )

    vehicles_to_process = df[needs_details].index.tolist()

    print(f"Fahrzeuge mit fehlenden Specs: {len(vehicles_to_process)}")
    print(f"Fetching Detail-Seiten mit {workers} parallel workers...\n")

    # Fetch in parallel
    specs_dict = {}
    processed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}

        for idx in vehicles_to_process:
            future = executor.submit(enrich_single_vehicle, idx, df.loc[idx], REQUEST_DELAY)
            futures[future] = idx

        for future in as_completed(futures):
            idx, specs = future.result()
            specs_dict[idx] = specs
            processed += 1

            if processed % max(1, len(vehicles_to_process) // 10) == 0:
                print(f"  Progress: {processed}/{len(vehicles_to_process)}")

    print(f"\n✅ Fetched {processed} detail pages\n")

    # Apply enrichment to DataFrame
    print(f"Applying enrichment to DataFrame...")

    enriched_count = {'battery': 0, 'ac': 0, 'dc': 0}

    for idx, specs in specs_dict.items():
        if specs.get('battery_capacity') and pd.isna(df.loc[idx, 'Battery Capacity kWh']):
            df.loc[idx, 'Battery Capacity kWh'] = specs['battery_capacity']
            enriched_count['battery'] += 1

        if specs.get('charging_ac') and pd.isna(df.loc[idx, 'Charging Rate Level 2 (kW)']):
            df.loc[idx, 'Charging Rate Level 2 (kW)'] = specs['charging_ac']
            enriched_count['ac'] += 1

        if specs.get('charging_dc') and pd.isna(df.loc[idx, 'Charging Rate DC Fast (kW)']):
            df.loc[idx, 'Charging Rate DC Fast (kW)'] = specs['charging_dc']
            enriched_count['dc'] += 1

    print(f"\n✅ Enriched:")
    print(f"  Battery: +{enriched_count['battery']} vehicles")
    print(f"  AC Charging: +{enriched_count['ac']} vehicles")
    print(f"  DC Charging: +{enriched_count['dc']} vehicles")

    print(f"\nDatenqualität NACHHER:")
    print(f"  Battery: {(~df['Battery Capacity kWh'].isna()).sum()}/{len(df)} ({100*(~df['Battery Capacity kWh'].isna()).sum()/len(df):.1f}%)")
    print(f"  DC Charging: {(~df['Charging Rate DC Fast (kW)'].isna()).sum()}/{len(df)} ({100*(~df['Charging Rate DC Fast (kW)'].isna()).sum()/len(df):.1f}%)")
    print(f"  AC Charging: {(~df['Charging Rate Level 2 (kW)'].isna()).sum()}/{len(df)} ({100*(~df['Charging Rate Level 2 (kW)'].isna()).sum()/len(df):.1f}%)\n")

    # Remove Detail URL column before saving
    if 'Detail URL' in df.columns:
        df = df.drop('Detail URL', axis=1)

    df.to_csv(output_file, index=False)
    print(f"✅ Saved: {output_file}\n")

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich EV data from detail pages")
    parser.add_argument('--input', '-i', required=True, help='Input CSV')
    parser.add_argument('--output', '-o', required=True, help='Output CSV')
    parser.add_argument('--workers', '-w', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--max-vehicles', '-m', type=int, default=None, help='Max vehicles to process (for testing)')

    args = parser.parse_args()

    exit_code = enrich_from_details(args.input, args.output, args.workers, args.max_vehicles)
    sys.exit(exit_code)
