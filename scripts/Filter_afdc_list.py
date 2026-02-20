#!/usr/bin/env python3
"""
filter_afdc_plugins.py

Filtert einen AFDC-Light-Duty-Export auf BEV/PHEV und behält nur "nützliche" Spalten
für weiteres Matching/Enrichment (EU-Quelle, Scraping, Quellenpflege etc.).

Beispiel:
python filter_afdc_plugins.py \
  --input light-duty-vehicles-2026-02-17.csv \
  --output afdc_us_plugins_core.csv
"""

from __future__ import annotations

import argparse
import sys
import pandas as pd


# "Core"-Spalten: minimal, aber hilfreich fürs Matching + spätere Datenanreicherung
DEFAULT_KEEP = [
    # IDs / Keys
    "Vehicle ID",
    "Manufacturer",
    "Model",
    "Model Year",



    "Fuel Code",



    "Battery Capacity kWh",



    "Charging Rate Level 2 (kW)",
    "Charging Rate DC Fast (kW)",


    # Optional hilfreich für Quellen/Notizen
    "Notes",
    "Manufacturer URL",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Filter AFDC LDV export to BEV/PHEV + keep relevant columns.")
    p.add_argument(
        "--input",
        "-i",
        default="/Users/maxfroehner/Desktop/Lemonflow/light-duty-vehicles-2026-02-17.csv",
        help=(
            "Pfad zur Input-CSV (default: /Users/maxfroehner/Desktop/Lemonflow/light-duty-vehicles-2026-02-17.csv)"
        ),
    )
    p.add_argument(
        "--output",
        "-o",
        default="/Users/maxfroehner/Desktop/Lemonflow/afdc_us_plugins_core.csv",
        help="Pfad zur Output-CSV (default: /Users/maxfroehner/Desktop/Lemonflow/afdc_us_plugins_core.csv)",
    )
    p.add_argument(
        "--keep",
        nargs="*",
        default=None,
        help="Optional: Eigene Keep-Liste (Spaltennamen) statt DEFAULT_KEEP",
    )
    p.add_argument(
        "--no-fuel-filter",
        action="store_true",
        help="Wenn gesetzt: NICHT auf Fuel Code ELEC/PHEV filtern.",
    )
    p.add_argument(
        "--dedupe",
        action="store_true",
        help="Wenn gesetzt: entfernt Duplikate anhand Vehicle ID (falls vorhanden).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # CSV einlesen (robust: keep_default_na=False verhindert manche komischen NA-Interpretationen)
    df = pd.read_csv(args.input, low_memory=False)

    # Optional: nur Plug-ins (falls doch noch HYBR o.ä. drin sind)
    if not args.no_fuel_filter and "Fuel Code" in df.columns:
        df = df[df["Fuel Code"].isin(["ELEC", "PHEV"])].copy()

    # Spalten reduzieren
    keep = args.keep if args.keep is not None else DEFAULT_KEEP
    keep_existing = [c for c in keep if c in df.columns]

    if not keep_existing:
        print("ERROR: Keine der gewünschten Spalten in der Datei gefunden.", file=sys.stderr)
        print("Verfügbare Spalten:", list(df.columns), file=sys.stderr)
        return 2

    df_out = df[keep_existing].copy()

    # Dedupe optional
    if args.dedupe and "Vehicle ID" in df_out.columns:
        df_out = df_out.drop_duplicates(subset=["Vehicle ID"]).copy()

    # Sortierung (wenn Spalten existieren)
    sort_cols = [c for c in ["Model Year", "Manufacturer", "Model", "Fuel Code", "Vehicle ID"] if c in df_out.columns]
    if sort_cols:
        df_out = df_out.sort_values(sort_cols)

    # Speichern
    df_out.to_csv(args.output, index=False)

    # Kleine Summary in die Konsole
    print(f"Wrote: {args.output}")
    print(f"Rows: {len(df_out):,}")
    if "Fuel Code" in df_out.columns:
        print("Counts by Fuel Code:")
        print(df_out["Fuel Code"].value_counts(dropna=False).to_string())
    if "Model Year" in df_out.columns and "Fuel Code" in df_out.columns:
        pivot = pd.pivot_table(
            df_out,
            index="Model Year",
            columns="Fuel Code",
            values="Vehicle ID" if "Vehicle ID" in df_out.columns else df_out.columns[0],
            aggfunc="count",
            fill_value=0,
        )
        pivot["Total"] = pivot.sum(axis=1)
        print("\nCounts by Model Year (tail):")
        print(pivot.tail(15).to_string())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
