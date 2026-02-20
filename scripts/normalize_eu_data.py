#!/usr/bin/env python3
"""
normalize_eu_data.py

Normalisiert die rohen ev-database.org Daten und mapped sie auf AFDC-Schema.
Ziel: Kompatibilität mit US-EV-Daten für einheitliche Anreicherung.

Verwendung:
    python3 normalize_eu_data.py --input ev_database_raw_fixed.csv --output ev_database_normalized.csv
"""

from __future__ import annotations

import argparse
import sys
import pandas as pd
import re
from typing import Optional


# ============================================================================
# NORMALISIERUNGSFUNKTIONEN
# ============================================================================

def normalize_manufacturer(mfr: str) -> str:
    """
    Normalisiere Herstellernamen.

    Args:
        mfr: Rohname

    Returns:
        Normalisierter Name
    """
    if not isinstance(mfr, str):
        return "Unknown"

    mfr = mfr.strip()

    # Mapping für häufige Variationen
    mappings = {
        "MGMG": "MG",
        "Ład": "Łąd",  # Polish characters
    }

    for old, new in mappings.items():
        if mfr.startswith(old):
            mfr = new + mfr[len(old):]
            break

    # Standardisierung
    mfr = mfr.strip()

    return mfr if mfr else "Unknown"


def normalize_model(model: str, manufacturer: str = "") -> str:
    """
    Normalisiere Modellname.

    Args:
        model: Rohname
        manufacturer: Herstellername (für Entfernung am Ende)

    Returns:
        Normalisierter Name
    """
    if not isinstance(model, str):
        return "Unknown"

    model = model.strip()

    # Entferne Herstellernamen am Ende (z.B. "iX3BMW" → "iX3")
    if manufacturer and isinstance(manufacturer, str):
        for mfr in [manufacturer, "Tesla", "BMW", "Audi", "Volkswagen", "Mercedes", "Hyundai", "Kia"]:
            if mfr and model.endswith(mfr):
                model = model[:-len(mfr)].strip()
                break

    # Entferne Variant-Notationen in Klammern am Ende (z.B. "(Juniper)", "(Highland)", "(MY22-24)" → "")
    model = re.sub(r'\s*\([A-Za-z0-9\-]+\)$', '', model).strip()  # Alles in Klammern am Ende
    model = re.sub(r'\(MY\d{2}-\d{2}\)', '', model).strip()
    model = re.sub(r'\(MY\d{4}\)', '', model).strip()

    # Entferne doppelte Text (z.B. "Model ModelName")
    parts = model.split()
    if len(parts) > 1:
        # Prüfe auf Duplikate (z.B. "Born 150 kW - 58 kWh CUPRA Born")
        if model.count(parts[0]) > 1:
            # Finde den eindeutigen Teil
            for i in range(1, len(parts)):
                if parts[i].lower() != parts[0].lower():
                    model = " ".join(parts[i:])
                    break

    # Entferne Batterie-Info am Ende (wenn vorhanden)
    if "kWh" in model:
        # Entferne alles nach dem letzten kWh
        model = model.split("kWh")[0].strip()

    # Entferne allgemeine Power-Notationen (z.B. "150 kW", "58 kWh")
    model = re.sub(r'\b\d+\s*(kW|kWh)\b', '', model).strip()

    return model if model else "Unknown"


def normalize_year(year) -> int:
    """
    Normalisiere Baujahr.

    Args:
        year: Baujahr (int oder str)

    Returns:
        Baujahr als int
    """
    try:
        year = int(year)
        # Validiere Range
        if 2010 <= year <= 2030:
            return year
        else:
            return 2024  # Default
    except (ValueError, TypeError):
        return 2024


def normalize_numeric(value) -> Optional[float]:
    """
    Normalisiere numerische Werte.

    Args:
        value: Rohwert (float, str, None)

    Returns:
        Normalisierter float oder None
    """
    try:
        if pd.isna(value) or value is None:
            return None

        value = float(value)

        # Validierung (abhängig vom Kontext - wird außen durchgeführt)
        return value if value >= 0 else None

    except (ValueError, TypeError):
        return None


def validate_battery_capacity(value: Optional[float]) -> Optional[float]:
    """Validiere Battery Capacity (sollte 10-150 kWh sein)."""
    if value is None:
        return None

    if 10 <= value <= 150:
        return value
    else:
        return None  # Ungültig


def validate_charging_rate(value: Optional[float]) -> Optional[float]:
    """Validiere Charging Rate (sollte 3-350 kW sein)."""
    if value is None:
        return None

    if 3 <= value <= 350:
        return value
    else:
        return None  # Ungültig


# ============================================================================
# MAIN
# ============================================================================

def normalize_csv(input_file: str, output_file: str) -> int:
    """
    Hauptfunktion für Normalisierung.

    Args:
        input_file: Input CSV Pfad
        output_file: Output CSV Pfad

    Returns:
        Exit code
    """
    print(f"{'='*60}")
    print(f"EU EV Data - Normalisierung")
    print(f"{'='*60}\n")

    # Lade Daten
    try:
        print(f"Lade: {input_file}")
        df = pd.read_csv(input_file, low_memory=False)
        print(f"✅ {len(df)} Zeilen geladen\n")
    except Exception as e:
        print(f"ERROR: Fehler beim Laden der CSV: {e}", file=sys.stderr)
        return 1

    # Zeige Original-Spalten
    print(f"Original-Spalten: {list(df.columns)}\n")

    # ── Normalisierungsschritte ──

    print("Normalisiere Daten...\n")

    # 1. Manufacturer
    print("  1. Normalisiere Hersteller...")
    df['Manufacturer'] = df['Manufacturer'].apply(normalize_manufacturer)

    # 2. Model
    print("  2. Normalisiere Modell...")
    df['Model'] = df.apply(lambda row: normalize_model(row['Model'], row['Manufacturer']), axis=1)

    # 3. Model Year
    print("  3. Normalisiere Baujahr...")
    df['Model Year'] = df['Model Year'].apply(normalize_year)

    # 4. Battery Capacity
    print("  4. Normalisiere Batterie...")
    df['Battery Capacity kWh'] = df['Battery Capacity kWh'].apply(normalize_numeric)
    df['Battery Capacity kWh'] = df['Battery Capacity kWh'].apply(validate_battery_capacity)

    # 5. Charging Rates
    print("  5. Normalisiere Ladegeschwindigkeiten...")
    df['Charging Rate Level 2 (kW)'] = df['Charging Rate Level 2 (kW)'].apply(normalize_numeric)
    # Level 2 AC: typisch 3-22 kW
    df['Charging Rate Level 2 (kW)'] = df['Charging Rate Level 2 (kW)'].apply(
        lambda x: x if (x and 3 <= x <= 22) else None
    )

    df['Charging Rate DC Fast (kW)'] = df['Charging Rate DC Fast (kW)'].apply(normalize_numeric)
    df['Charging Rate DC Fast (kW)'] = df['Charging Rate DC Fast (kW)'].apply(validate_charging_rate)

    # ── Duplikate entfernen ──
    print("  6. Entferne Duplikate...")

    original_count = len(df)
    df = df.drop_duplicates(subset=['Manufacturer', 'Model', 'Model Year'], keep='first')
    duplicates_removed = original_count - len(df)

    if duplicates_removed > 0:
        print(f"     Duplikate entfernt: {duplicates_removed}")

    # ── Validierung & Stats ──
    print(f"\n{'='*60}")
    print(f"NORMALISIERUNG ABGESCHLOSSEN")
    print(f"{'='*60}\n")

    print(f"Zeilen: {len(df)}")
    print(f"Spalten: {list(df.columns)}\n")

    # Datenqualitäts-Stats
    print("Datenqualität:")
    print(f"  Manufacturer (100%): {(~df['Manufacturer'].isna()).sum()}/{len(df)}")
    print(f"  Model (100%): {(~df['Model'].isna()).sum()}/{len(df)}")
    print(f"  Model Year (100%): {(~df['Model Year'].isna()).sum()}/{len(df)}")
    print(f"  Battery Capacity: {(~df['Battery Capacity kWh'].isna()).sum()}/{len(df)} ({(~df['Battery Capacity kWh'].isna()).sum()/len(df)*100:.1f}%)")
    print(f"  DC Fast Charging: {(~df['Charging Rate DC Fast (kW)'].isna()).sum()}/{len(df)} ({(~df['Charging Rate DC Fast (kW)'].isna()).sum()/len(df)*100:.1f}%)\n")

    # Top Hersteller
    print("Top 10 Hersteller:")
    top_mfrs = df['Manufacturer'].value_counts().head(10)
    for mfr, count in top_mfrs.items():
        print(f"  {mfr}: {count}")

    print(f"\nTop 10 Modelle (mit Hersteller):")
    df['Full Name'] = df['Manufacturer'] + ' ' + df['Model']
    top_models = df['Full Name'].value_counts().head(10)
    for name, count in top_models.items():
        print(f"  {name}: {count}")

    df = df.drop('Full Name', axis=1)

    # ── Speichern ──
    print(f"\n{'='*60}")
    print(f"Speichern...")

    try:
        # Reordne Spalten für Klarheit
        column_order = [
            'Manufacturer', 'Model', 'Model Year',
            'Battery Capacity kWh',
            'Charging Rate Level 2 (kW)',
            'Charging Rate DC Fast (kW)'
        ]
        df = df[column_order]

        df.to_csv(output_file, index=False)
        print(f"✅ Gespeichert: {output_file}\n")

        return 0

    except Exception as e:
        print(f"ERROR: Fehler beim Speichern: {e}", file=sys.stderr)
        return 1


def parse_args() -> argparse.Namespace:
    """Parse Kommandozeilenargumente."""
    p = argparse.ArgumentParser(
        description="Normalisiere EU EV-Daten auf AFDC-Schema"
    )
    p.add_argument(
        "--input", "-i",
        default="/sessions/confident-cool-euler/mnt/Lemonflow/ev_database_raw_fixed.csv",
        help="Input CSV"
    )
    p.add_argument(
        "--output", "-o",
        default="/sessions/confident-cool-euler/mnt/Lemonflow/ev_database_normalized.csv",
        help="Output CSV"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = normalize_csv(args.input, args.output)
    raise SystemExit(exit_code)
