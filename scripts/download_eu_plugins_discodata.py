#!/usr/bin/env python3
"""
Download an (as-exhaustive-as-possible) EU plug‑in vehicle model list from the
European Environment Agency (EEA) "CO2 emissions from new passenger cars" dataset
via Discodata’s SQL REST API.

What you get:
- A CSV of DISTINCT model entries per reporting year:
  Year, Status, Mk (make), Cn (commercial name), Ft (fuel type), Fm (fuel mode)
- Filtered to plug‑in vehicles via Zr (electric range) > 0

Notes:
- This is an official, registration-based dataset (new registrations), not a
  "currently marketed models" catalogue.
- The dataset uses "Year" as reporting year and "Status" as Provisional/Final.
  It does NOT provide OEM "model year" like US AFDC, so treat Year as a proxy.

Requirements:
  pip install requests pandas

Usage (examples):
  python download_eu_plugins_discodata.py --out eu_plugins_models.csv
  python download_eu_plugins_discodata.py --years 2022 2025 --status P F
  python download_eu_plugins_discodata.py --last-n-years 3 --status P

"""
from __future__ import annotations

import argparse
import sys
import time
from urllib.parse import quote

import pandas as pd
import requests


BASE = "https://discodata.eea.europa.eu/sql"


def call_sql(query: str, page: int = 1, page_size: int = 1000, timeout: int = 30) -> dict:
    """
    Call Discodata SQL REST endpoint.

    The API returns JSON:
      {"results":[{...},{...}]}  or  {"errors":[{"error":"...", "errorcode":...}]}
    """
    url = f"{BASE}?query={quote(query)}&p={page}&nrOfHits={page_size}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_all_pages(query: str, page_size: int = 2000, sleep_s: float = 0.15) -> list[dict]:
    """Fetch all pages until results are empty."""
    out: list[dict] = []
    page = 1
    while True:
        payload = call_sql(query, page=page, page_size=page_size)
        if "errors" in payload:
            raise RuntimeError(payload["errors"][0].get("error", str(payload["errors"][0])))
        rows = payload.get("results", [])
        if not rows:
            break
        out.extend(rows)
        page += 1
        time.sleep(sleep_s)  # be kind to the endpoint
    return out


def get_max_year() -> int:
    q = "SELECT max(Year) as maxYear FROM [CO2Emission].[latest].[co2cars]"
    payload = call_sql(q, page=1, page_size=1)
    if "errors" in payload:
        raise RuntimeError(payload["errors"][0].get("error", str(payload["errors"][0])))
    rows = payload.get("results", [])
    if not rows or rows[0].get("maxYear") is None:
        raise RuntimeError("Could not determine max Year from the dataset.")
    return int(rows[0]["maxYear"])


def build_query(min_year: int, max_year: int, statuses: list[str]) -> str:
    # Plug‑in vehicles proxy: electric range (Zr) present and > 0
    status_clause = " OR ".join([f"Status = '{s}'" for s in statuses])
    q = f"""
SELECT DISTINCT
  Year, Status, Mk, Cn, Ft, Fm
FROM [CO2Emission].[latest].[co2cars]
WHERE Year >= {min_year}
  AND Year <= {max_year}
  AND ({status_clause})
  AND Zr IS NOT NULL
  AND Zr > 0
"""
    return " ".join(q.split())  # compact whitespace


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="eu_plugins_models.csv", help="Output CSV path")
    ap.add_argument("--page-size", type=int, default=2000, help="API page size (nrOfHits)")
    ap.add_argument("--sleep", type=float, default=0.15, help="Sleep between pages (seconds)")
    ap.add_argument("--status", nargs="+", default=["P", "F"], help="Status values to include (P and/or F)")
    ap.add_argument("--years", nargs=2, type=int, metavar=("MIN_YEAR", "MAX_YEAR"),
                    help="Explicit year range (inclusive). Example: --years 2022 2025")
    ap.add_argument("--since-year", type=int, default=2023,
                    help="If --years not provided: use since-year .. max-year (default 2023)")
    ap.add_argument("--max-year", type=int, default=2025,
                    help="When --years not provided: upper bound of the year range (default 2025). Will be capped at dataset max year if needed.")
    args = ap.parse_args()

    statuses = [s.strip().upper() for s in args.status]
    for s in statuses:
        if s not in {"P", "F"}:
            ap.error("Status must be P and/or F")

    if args.years:
        min_year, max_year = args.years
    else:
        dataset_max = get_max_year()
        min_year = args.since_year
        requested_max = args.max_year
        if dataset_max < min_year:
            print(
                f"Warning: dataset max year {dataset_max} is earlier than since-year {min_year}; adjusting since-year to {dataset_max}",
                file=sys.stderr,
            )
            min_year = dataset_max
        # Cap requested max to dataset max to avoid empty queries for future years
        max_year = min(requested_max, dataset_max)
        if max_year < min_year:
            ap.error("Computed max_year < min_year after capping to dataset max; try --years to specify an explicit valid range.")

    query = build_query(min_year=min_year, max_year=max_year, statuses=statuses)
    print(f"Querying Discodata for years {min_year}..{max_year}, status={statuses} ...")

    rows = fetch_all_pages(query, page_size=args.page_size, sleep_s=args.sleep)
    df = pd.DataFrame(rows)

    if df.empty:
        print("No rows returned. Try widening the year range or checking endpoint availability.", file=sys.stderr)
        return 2

    # Normalize + de-duplicate
    keep_cols = ["Year", "Status", "Mk", "Cn", "Ft", "Fm"]
    df = df[[c for c in keep_cols if c in df.columns]].copy()

    # Clean strings
    for c in ["Status", "Mk", "Cn", "Ft", "Fm"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    df = df.drop_duplicates().sort_values(["Year", "Status", "Mk", "Cn", "Ft", "Fm"], kind="mergesort")

    out_path = args.out
    df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Saved {len(df):,} distinct model rows to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
