#!/usr/bin/env python3
"""
enrich_eu_ev_data.py

Reichert EU EV-Daten mit EU-spezifischen Informationen an:
- Steckertyp (Type 2 + CCS2 für EU)
- Autocharge/Plug & Charge Support (EU Netzwerke)
- Manuelle Entriegelung des Ladekabels

Nutzt 3-stufige Lookup-Hierarchie: Modell > Plattform > Hersteller

Verwendung:
    python3 enrich_eu_ev_data.py --input ev_database_normalized.csv --output ev_eu_enriched.csv
"""

from __future__ import annotations

import argparse
import sys
import pandas as pd
from typing import Dict, Any


# ============================================================================
# EU-SPEZIFISCHE LOOKUP-TABLES
# ============================================================================

# EU Autocharge/Plug & Charge Support
EU_AUTOCHARGE_LOOKUP: Dict[str, Dict[str, Any]] = {
    # VW Group
    "Audi": {
        "default": "Ja - Plug & Charge (ab MY2023) via NewMotion",
        "networks": "NewMotion (Electrify Europe), Ionity, Shell Recharge",
        "min_year": 2023,
    },
    "Porsche": {
        "default": "Ja - Plug & Charge (ab MY2023)",
        "networks": "Porsche Charging Service, Electrify Europe, Ionity",
        "min_year": 2023,
    },
    "Volkswagen": {
        "default": "Ja - Plug & Charge (ab MY2023)",
        "networks": "Electrify Europe (NewMotion), Ionity",
        "min_year": 2023,
    },

    # BMW Group
    "BMW": {
        "default": "Ja - Plug & Charge (ab MY2023) via BMW ChargeNow",
        "networks": "BMW ChargeNow, Electrify Europe, Ionity",
        "min_year": 2023,
    },
    "Mini": {
        "default": "Nein",
        "networks": "N/A",
    },

    # Mercedes
    "Mercedes-Benz": {
        "default": "Ja - Plug & Charge (ab MY2023)",
        "networks": "Mercedes me Charge, Electrify Europe, Ionity",
        "min_year": 2023,
    },

    # Hyundai Group
    "Hyundai": {
        "default": "Ja - Plug & Charge (ab MY2023)",
        "networks": "Electrify Europe, Ionity, Shell Recharge",
        "min_year": 2023,
    },
    "Kia": {
        "default": "Ja - Plug & Charge (ab MY2023)",
        "networks": "Electrify Europe, Ionity, Shell Recharge",
        "min_year": 2023,
    },
    "Genesis": {
        "default": "Ja - Plug & Charge (ab MY2023)",
        "networks": "Electrify Europe, Ionity",
        "min_year": 2023,
    },

    # Volvo/Polestar
    "Volvo": {
        "default": "Ja - Plug & Charge (neuere Modelle)",
        "networks": "Electrify Europe, Ionity",
        "min_year": 2023,
    },
    "Polestar": {
        "default": "Ja - Plug & Charge (neuere Modelle)",
        "networks": "Electrify Europe, Ionity",
        "min_year": 2023,
    },

    # Stellantis (PSA Group)
    "Peugeot": {
        "default": "Partiell - ab MY2023",
        "networks": "Electrify Europe, Ionity (begrenzt)",
        "min_year": 2023,
    },
    "Opel": {
        "default": "Partiell - ab MY2023",
        "networks": "Electrify Europe, Ionity",
        "min_year": 2023,
    },
    "Citroën": {
        "default": "Nein",
        "networks": "N/A",
    },
    "CUPRA": {
        "default": "Nein",
        "networks": "N/A",
    },
    "Fiat": {
        "default": "Nein",
        "networks": "N/A",
    },

    # Ford
    "Ford": {
        "default": "Ja - Plug & Charge (ab MY2024)",
        "networks": "Electrify America (EU via Ionity)",
        "min_year": 2024,
    },

    # Tesla
    "Tesla": {
        "default": "Teilweise - NACS Adapter für EU Type 2",
        "networks": "Tesla Supercharger (mit Adapter)",
        "min_year": 2020,
    },

    # BYD, NIO, Xpeng, etc. (Chinesische Hersteller)
    "BYD": {
        "default": "Nein",
        "networks": "N/A",
    },
    "MG": {
        "default": "Nein",
        "networks": "N/A",
    },
    "Nissan": {
        "default": "Nein",
        "networks": "N/A (CHAdeMO)",
    },
    "Škoda": {
        "default": "Partiell - ab MY2023",
        "networks": "Electrify Europe, Ionity",
        "min_year": 2023,
    },
    "Lucid": {
        "default": "Ja - Plug & Charge",
        "networks": "Electrify Europe, Ionity",
        "min_year": 2022,
    },
    "Rivian": {
        "default": "Ja - Plug & Charge (neuere)",
        "networks": "Rivian Adventure Network (EU), Electrify Europe",
        "min_year": 2023,
    },
}


# EU Emergency Release (Modell-spezifisch)
EU_EMERGENCY_RELEASE_BY_MODEL: Dict[tuple, str] = {
    # Audi
    ("Audi", "Q4"): "Kofferraum: Gelbe Schlaufe unter Ladeboden, links Seite",
    ("Audi", "e-tron"): "Motorhaube: Kleine Klappe direkt über Ladeanschluss",

    # BMW (siehe Phase 1 - aus US bereits vorhanden)
    ("BMW", "iX"): "Kofferraum rechte Seite: Verkleidung abnehmen, Notentriegelungshebel",
    ("BMW", "i4"): "⚠️ KEIN mechanischer Notentriegelungsmechanismus",

    # Peugeot/Opel (meist ähnlich)
    ("Peugeot", "e-208"): "Kofferraum: Gelbe Schlaufe unter Ladeboden",
    ("Opel", "Corsa"): "Kofferraum: Gelbe Schlaufe unter Ladeboden",

    # Tesla (weltweit gleich)
    ("Tesla", "Model"): "Kofferraum: Oranges Notentriegelungskabel, oder Touchscreen Service",

    # Volkswagen (MEB Plattform)
    ("Volkswagen", "ID"): "Kofferraum Beifahrerseite: Gelbe Schlaufe",

    # Ford
    ("Ford", "Mustang"): "Kofferraum: Flexibler Tab neben Ladeanschluss",

    # Volvo/Polestar (Volvo-Plattform)
    ("Volvo", "EX"): "Kofferraum links: Kappe abhebeln, Hebel darunter ziehen",
    ("Polestar", "2"): "Kofferraum links: Bodenpanel anheben, Hebel ziehen",

    # Hyundai/Kia (E-GMP Plattform)
    ("Hyundai", "Ioniq"): "Kofferraum rechts: Runde Kunststoffkappe abziehen",
    ("Kia", "EV6"): "Kofferraum rechts: Runde Kunststoffkappe abziehen",
    ("Kia", "EV9"): "Kofferraum rechts: Runde Kunststoffkappe abziehen",

    # Nissan
    ("Nissan", "LEAF"): "Druckknopf am Stecker selbst (CHAdeMO)",
    ("Nissan", "ARIYA"): "Motorhaube: Einmaliger mechanischer Mechanismus",
}


# EU Emergency Release (Plattform-basiert)
EU_EMERGENCY_RELEASE_BY_PLATFORM: Dict[str, str] = {
    "Audi": "Kofferraum oder Motorhaube je nach Modell - siehe Betriebsanleitung",
    "BMW": "Modellabhängig: iX (Kofferraum rechts), i4/i5 (kein Mechanismus)",
    "Mercedes-Benz": "Kofferraum Beifahrerseite: Verkleidung abnehmen, Seil ziehen",
    "Ford": "Unterschiedlich je Modell - Owner's Manual konsultieren",
    "Volkswagen": "Kofferraum Beifahrerseite: Gelbe Notentriegelungsschlaufe",
    "Peugeot": "Kofferraum: Gelbe Schlaufe unter Ladeboden",
    "Opel": "Kofferraum: Gelbe Schlaufe unter Ladeboden",
    "Volvo": "Kofferraum links: Bodenpanel anheben",
    "Hyundai": "Kofferraum rechts (E-GMP): Kunststoffkappe abziehen",
    "Kia": "Kofferraum rechts (E-GMP): Kunststoffkappe abziehen",
    "Nissan": "LEAF: am Stecker; ARIYA: Motorhaube links hinten",
    "Tesla": "Kofferraum: Oranges Notentriegelungskabel",
    "Porsche": "Außen am Fahrzeug: schwarzer Knopf zwischen Tür und Kotflügel",
    "Škoda": "MEB-Plattform: Kofferraum Beifahrerseite, gelbe Schlaufe",
    "Polestar": "Volvo-Plattform: Kofferraum links",
    "Lucid": "Touchscreen Service-Modus oder mechanisch near charging port",
    "Rivian": "Zentral-Display > Ladeport entriegeln; mechanisch mit T-Schlüsseln",
}


# EU Emergency Release (Hersteller-Fallback)
EU_EMERGENCY_RELEASE_BY_MAKE: Dict[str, str] = {
    "Citroën": "Owner's Manual konsultieren",
    "CUPRA": "Wahrscheinlich VW MEB: Kofferraum Beifahrerseite",
    "Fiat": "500e: Kofferraum - ähnlich Peugeot",
    "MG": "Dokumentation begrenzt - Pannendienst kontaktieren",
    "BYD": "Dokumentation begrenzt - Hersteller kontaktieren",
    "Mini": "Ähnlich BMW - Owner's Manual konsultieren",
    "Suzuki": "Dokumentation begrenzt",
    "Leapmotor": "Chinesischer Hersteller - Owner's Manual konsultieren",
    "Ora": "Chinesischer Hersteller - Owner's Manual konsultieren",
    "Xpeng": "Chinesischer Hersteller - Owner's Manual konsultieren",
}


# ============================================================================
# PLUG TYPE BESTIMMUNG (EU)
# ============================================================================

def determine_plug_type_eu(row: pd.Series) -> str:
    """
    Bestimme Steckertyp für EU-Fahrzeuge.

    EU Standard: Type 2 + CCS2 für BEVs, Type 2 AC nur für PHEVs
    Ausnahmen: Tesla (NACS ab 2024 für Berlin Giga), Nissan (CHAdeMO)
    """
    manufacturer = str(row.get("Manufacturer", "")).strip()
    model = str(row.get("Model", "")).strip()
    model_year = int(row.get("Model Year", 2024))

    # Tesla: NACS ab 2024 (Berlin Gigafactory), sonst Type 2
    if "Tesla" in manufacturer:
        if model_year >= 2024:
            return "NACS (Berlin Giga) / Type 2 mit Adapter"
        else:
            return "Type 2 + CCS2"

    # Nissan LEAF (alt): CHAdeMO
    if "Nissan" in manufacturer and "LEAF" in model and model_year < 2024:
        return "CHAdeMO + Type 2"

    # Nissan ARIYA: CCS2
    if "Nissan" in manufacturer and "ARIYA" in model:
        return "Type 2 + CCS2"

    # Standard EU BEV: Type 2 + CCS2
    return "Type 2 + CCS2"


# ============================================================================
# AUTOCHARGE BESTIMMUNG
# ============================================================================

def determine_autocharge_eu(row: pd.Series) -> str:
    """Bestimme Autocharge Support für EU."""
    manufacturer = str(row.get("Manufacturer", "")).strip()
    model_year = int(row.get("Model Year", 2024))

    info = EU_AUTOCHARGE_LOOKUP.get(manufacturer, {})

    if not info:
        return "Unbekannt - Hersteller nicht in Datenbank"

    min_year = info.get("min_year", 2023)
    if model_year < min_year:
        return "Nein"

    default = info.get("default", "Unbekannt")
    networks = info.get("networks", "")

    if networks:
        return f"{default} | Netzwerke: {networks}"
    return default


# ============================================================================
# EMERGENCY RELEASE BESTIMMUNG
# ============================================================================

def determine_emergency_release_eu(row: pd.Series) -> str:
    """
    Bestimme Notentriegelung in 3 Stufen.
    Ähnlich wie US-Version aber mit EU-spezifischen Daten.
    """
    manufacturer = str(row.get("Manufacturer", "")).strip()
    model = str(row.get("Model", "")).strip()

    # Stufe 1: Modell-spezifisch
    for (mfr_key, model_key), description in EU_EMERGENCY_RELEASE_BY_MODEL.items():
        if mfr_key.lower() in manufacturer.lower() and model_key.lower() in model.lower():
            return description

    # Stufe 2: Plattform/Hersteller
    for mfr_key, description in EU_EMERGENCY_RELEASE_BY_PLATFORM.items():
        if mfr_key.lower() in manufacturer.lower():
            return description

    # Stufe 3: Hersteller-Fallback
    for mfr_key, description in EU_EMERGENCY_RELEASE_BY_MAKE.items():
        if mfr_key.lower() in manufacturer.lower():
            return description

    return "Nicht dokumentiert – Owner's Manual des Fahrzeugs konsultieren"


# ============================================================================
# MAIN
# ============================================================================

def enrich_csv(input_file: str, output_file: str) -> int:
    """
    Hauptfunktion für Anreicherung.

    Args:
        input_file: Input CSV Pfad (normalisiert)
        output_file: Output CSV Pfad (angereichert)

    Returns:
        Exit code
    """
    print(f"{'='*60}")
    print(f"EU EV Data - Anreicherung")
    print(f"{'='*60}\n")

    # Lade Daten
    try:
        print(f"Lade: {input_file}")
        df = pd.read_csv(input_file, low_memory=False)
        print(f"✅ {len(df)} Zeilen geladen\n")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Anreicherung
    print("Reichere Daten an...\n")

    print("  1. Füge Plug Type hinzu...")
    df["Plug Type"] = df.apply(determine_plug_type_eu, axis=1)

    print("  2. Füge Autocharge Support hinzu...")
    df["Autocharge Support"] = df.apply(determine_autocharge_eu, axis=1)

    print("  3. Füge Emergency Release Location hinzu...")
    df["Emergency Release Location"] = df.apply(determine_emergency_release_eu, axis=1)

    # Stats
    print(f"\n{'='*60}")
    print(f"ANREICHERUNG ABGESCHLOSSEN")
    print(f"{'='*60}\n")

    print(f"Zeilen: {len(df)}")
    print(f"Neue Spalten: Plug Type, Autocharge Support, Emergency Release Location\n")

    print("Plug Type Verteilung:")
    print(df["Plug Type"].value_counts().head(5).to_string())

    print("\n\nAutocharge Support (Top 5):")
    print(df["Autocharge Support"].value_counts().head(5).to_string())

    print("\n\nEmergency Release (Top 5):")
    top_release = df["Emergency Release Location"].value_counts().head(5)
    for desc, count in top_release.items():
        print(f"  {desc[:60]}...: {count}")

    # Speichern
    print(f"\n{'='*60}")
    print(f"Speichern...")

    try:
        df.to_csv(output_file, index=False)
        print(f"✅ Gespeichert: {output_file}\n")
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def parse_args() -> argparse.Namespace:
    """Parse Kommandozeilenargumente."""
    p = argparse.ArgumentParser(
        description="Reichert EU EV-Daten mit Plug Type, Autocharge, Emergency Release an"
    )
    p.add_argument(
        "--input", "-i",
        default="/sessions/confident-cool-euler/mnt/Lemonflow/ev_database_normalized.csv",
        help="Input CSV"
    )
    p.add_argument(
        "--output", "-o",
        default="/sessions/confident-cool-euler/mnt/Lemonflow/ev_eu_enriched.csv",
        help="Output CSV"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = enrich_csv(args.input, args.output)
    raise SystemExit(exit_code)
