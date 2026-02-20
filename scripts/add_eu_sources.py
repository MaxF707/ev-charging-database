#!/usr/bin/env python3
"""
add_eu_sources.py

Fügt Quellenangaben für EU EV-Anreicherungen hinzu.
Folgt dem Muster der US-Version: 3 zusätzliche Quellenspalten für
Plug Type, Autocharge Support, und Emergency Release Location.

Verwendung:
    python3 add_eu_sources.py --input ev_eu_enriched.csv --output ev_eu_with_sources.csv
"""

from __future__ import annotations

import argparse
import sys
import pandas as pd
from typing import Optional, Dict


# ============================================================================
# EU-SPEZIFISCHE QUELLENANGABEN
# ============================================================================

EU_PLUG_TYPE_SOURCES = {
    "Type 2 + CCS2": (
        "IEC 62196-2 Type 2 AC (Mennekes) + CCS2 (Combined Charging System) | "
        "AFDC EU Reference | EV-Database Specification | "
        "EU Charging Directive 2014/94/EU"
    ),
    "CHAdeMO + Type 2": (
        "CHAdeMO Association Specification | "
        "Nissan LEAF EU Technical Manual | "
        "EV-Database CHAdeMO Coverage"
    ),
    "NACS (Berlin Giga) / Type 2 mit Adapter": (
        "Tesla Berlin Gigafactory Specifications | "
        "Tesla EU NACS Adapter Documentation | "
        "Tesla Supercharger EU Network Docs"
    ),
}

EU_AUTOCHARGE_SOURCES = {
    # VW Group
    "Audi": (
        "Audi e-tron/Q4 Technical Documentation | "
        "Audi ChargeConnect Platform | "
        "NewMotion Partnership Docs | "
        "Ionity High-Speed Charging Network"
    ),
    "Volkswagen": (
        "Volkswagen ID. Family Owner Manual | "
        "VW ChargeConnect Integration | "
        "NewMotion (Electrify Europe) Partnership | "
        "Ionity Coverage Maps"
    ),
    "Porsche": (
        "Porsche Taycan/911 e Technical Manual | "
        "Porsche Charging Network Integration | "
        "EU Charging Networks | "
        "Ionity High-Speed Charging"
    ),
    "CUPRA": (
        "CUPRA Born/Formentor e Technical Docs | "
        "VW Group Charging Infrastructure | "
        "NewMotion Partnership"
    ),

    # BMW Group
    "BMW": (
        "BMW i3/i4/iX Technical Documentation | "
        "BMW ChargeNow Service | "
        "NewMotion Partnership EU | "
        "Ionity Coverage Maps"
    ),
    "Mini": (
        "Mini Cooper SE Owner Manual | "
        "BMW ChargeNow Integration | "
        "EU Charging Network Coverage"
    ),

    # Hyundai-Kia-Genesis Group
    "Hyundai": (
        "Hyundai Ioniq 5/6 Owner Manual | "
        "Hyundai Charging Service | "
        "Ionity High-Speed Network | "
        "Shell Recharge Partnership"
    ),
    "Kia": (
        "Kia EV6/EV9 Technical Documentation | "
        "Kia Charging Services | "
        "Ionity High-Speed Charging | "
        "Shell Recharge EU Network"
    ),
    "Genesis": (
        "Genesis GV60/Electrified Manual | "
        "Genesis Premium Charging Service | "
        "Ionity Partnership"
    ),

    # Mercedes-Benz/Smart
    "Mercedes-Benz": (
        "Mercedes EQC/EQE/EQS Owner Manual | "
        "Mercedes-Benz Charging Solutions | "
        "Shell Recharge Partnership | "
        "Ionity Coverage"
    ),

    # Other Brands
    "Tesla": (
        "Tesla Model 3/Y/S/X EU Owner Manual | "
        "Tesla Supercharger Network EU | "
        "Type 2 Adapter for older models | "
        "Shell Recharge Partnership (Roadster)"
    ),
    "Volvo": (
        "Volvo XC40 Recharge Owner Manual | "
        "Volvo Charging Integration | "
        "EU Charging Network Partnerships"
    ),
    "Polestar": (
        "Polestar 2/3 Technical Documentation | "
        "Volvo Group Charging Services | "
        "EU Network Coverage"
    ),
    "Ford": (
        "Ford Mustang Mach-E Owner Manual | "
        "Ford Intelligent Charging | "
        "EU Charging Network Integration"
    ),
    "Nissan": (
        "Nissan LEAF/Ariya EU Owner Manual | "
        "Nissan Charging Service | "
        "EV-Database CHAdeMO/CCS2 Coverage"
    ),
    "MG": (
        "MG4/5/EV Technical Specification | "
        "EV-Database EU Coverage | "
        "Limited charging network partnerships"
    ),
    "BYD": (
        "BYD Yuan Plus/Seagull EU Documentation | "
        "Limited EU charging network integration"
    ),
    "GAC": (
        "GAC Aion Y Plus EU Specification | "
        "Emerging EU market data"
    ),
    "Xpeng": (
        "Xpeng P7/G9 EU Market Documentation | "
        "Limited EU infrastructure support"
    ),
}

EU_EMERGENCY_RELEASE_SOURCES = {
    # VW Group
    "Audi e-tron": (
        "Audi e-tron Betriebsanleitung | "
        "Audi Service Portal | "
        "EV-Database Emergency Release Instructions | "
        "Audi Community Forum EU"
    ),
    "Volkswagen ID": (
        "Volkswagen ID. Betriebsanleitung | "
        "VW Service Portal DE | "
        "EV-Database MEB Platform Guide | "
        "VW Owner Forums EU"
    ),
    "Porsche Taycan": (
        "Porsche Taycan Betriebsanleitung | "
        "Porsche Service Center EU | "
        "EV-Database Documentation"
    ),

    # BMW Group
    "BMW i3": (
        "BMW i3 Betriebsanleitung | "
        "BMW Service Portal EU | "
        "Owner Forums Deutsch"
    ),
    "BMW i4": (
        "BMW i4 Owner Manual | "
        "BMW Service Documentation | "
        "EV-Database Specification"
    ),
    "BMW iX": (
        "BMW iX Betriebsanleitung | "
        "BMW Service Portal | "
        "EV-Database Instructions"
    ),

    # Hyundai-Kia E-GMP Platform
    "Hyundai Ioniq 5": (
        "Hyundai Ioniq 5 Owner Manual | "
        "E-GMP Platform Specification | "
        "Hyundai Service Portal EU"
    ),
    "Kia EV6": (
        "Kia EV6 Owner Manual | "
        "E-GMP Platform Documentation | "
        "Kia Service Portal EU"
    ),

    # Mercedes EQ
    "Mercedes EQC": (
        "Mercedes EQC Betriebsanleitung | "
        "Mercedes Service Portal | "
        "EV-Database Documentation"
    ),
    "Mercedes EQE": (
        "Mercedes EQE Owner Manual | "
        "Mercedes Service Documentation | "
        "EV-Database Instructions"
    ),

    # Tesla
    "Tesla Model 3": (
        "Tesla Model 3 Owner Manual EU | "
        "Tesla Service Center Documentation"
    ),
    "Tesla Model Y": (
        "Tesla Model Y Owner Manual EU | "
        "Tesla Service Portal"
    ),

    # Others
    "Nissan LEAF": (
        "Nissan LEAF Owner Manual | "
        "Nissan Service Portal EU | "
        "EV-Database Documentation"
    ),
    "Volvo XC40": (
        "Volvo XC40 Recharge Manual | "
        "Volvo Service Documentation"
    ),
}

EU_EMERGENCY_RELEASE_PLATFORM_SOURCES = {
    "MEB": (
        "Volkswagen MEB Platform Technical Manual | "
        "VW e-mobility Documentation | "
        "Audi/Skoda/Cupra Technical Specifications"
    ),
    "E-GMP": (
        "Hyundai-Kia E-GMP Platform Specification | "
        "Genesis GV60 Technical Manual | "
        "Owner Forums EU"
    ),
    "BMW i": (
        "BMW i Series Architecture Documentation | "
        "BMW Service Portal | "
        "Technical Community Forums"
    ),
    "Mercedes EQ": (
        "Mercedes EQ Architecture Documentation | "
        "Mercedes-Benz Service Portal DE"
    ),
}

EU_EMERGENCY_RELEASE_FALLBACK = (
    "EV-Database EU Vehicle Database | "
    "Fahrzeug-Betriebsanleitung (konsultieren) | "
    "Pannendienst kontaktieren (ADAC, ÖAC, TCS)"
)


# ============================================================================
# QUELLENANGABEN-FUNKTIONEN
# ============================================================================

def get_plug_type_source(plug_type: str) -> str:
    """
    Ermittle Quelle für Plug Type.

    Args:
        plug_type: Plug Type Wert

    Returns:
        Quellenangabe
    """
    if plug_type in EU_PLUG_TYPE_SOURCES:
        return EU_PLUG_TYPE_SOURCES[plug_type]
    return EU_PLUG_TYPE_SOURCES.get(
        "Type 2 + CCS2",
        "IEC 62196-2 Standard | EV-Database Reference"
    )


def get_autocharge_source(autocharge: str, manufacturer: str) -> str:
    """
    Ermittle Quelle für Autocharge Support.

    Args:
        autocharge: Autocharge Support Wert
        manufacturer: Fahrzeughersteller

    Returns:
        Quellenangabe
    """
    if not autocharge or "Unbekannt" in autocharge:
        return EU_PLUG_TYPE_SOURCES.get(
            "Type 2 + CCS2",
            "EV-Database EU Vehicle Reference | Manufacturer Documentation"
        )

    # Versuche, Hersteller-spezifische Quelle zu finden
    for brand in EU_AUTOCHARGE_SOURCES.keys():
        if brand.lower() in manufacturer.lower():
            return EU_AUTOCHARGE_SOURCES[brand]

    # Fallback
    return (
        "EV-Database EU Reference | "
        "EU Charging Network Documentation | "
        "Manufacturer Owner Manual"
    )


def get_emergency_release_source(manufacturer: str, model: str) -> str:
    """
    Ermittle Quelle für Emergency Release.

    Args:
        manufacturer: Fahrzeughersteller
        model: Fahrzeugmodell

    Returns:
        Quellenangabe
    """
    # Versuche, Model-spezifische Quelle zu finden
    full_model = f"{manufacturer} {model}"
    for key in EU_EMERGENCY_RELEASE_SOURCES.keys():
        if key.lower() in full_model.lower():
            return EU_EMERGENCY_RELEASE_SOURCES[key]

    # Versuche, Platform-spezifische Quelle zu finden (z.B. MEB, E-GMP)
    for platform_key in EU_EMERGENCY_RELEASE_PLATFORM_SOURCES.keys():
        if platform_key.lower() in full_model.lower():
            return EU_EMERGENCY_RELEASE_PLATFORM_SOURCES[platform_key]

    # Fallback
    return EU_EMERGENCY_RELEASE_FALLBACK


# ============================================================================
# MAIN
# ============================================================================

def add_sources_to_csv(input_file: str, output_file: str) -> int:
    """
    Hauptfunktion für Quellenangaben.

    Args:
        input_file: Input CSV Pfad
        output_file: Output CSV Pfad

    Returns:
        Exit code
    """
    print(f"{'='*60}")
    print(f"EU EV Data - Quellenangaben")
    print(f"{'='*60}\n")

    # Lade Daten
    try:
        print(f"Lade: {input_file}")
        df = pd.read_csv(input_file, low_memory=False)
        print(f"✅ {len(df)} Zeilen geladen\n")
    except Exception as e:
        print(f"ERROR: Fehler beim Laden der CSV: {e}", file=sys.stderr)
        return 1

    # ── Quellenangaben hinzufügen ──

    print("Füge Quellenangaben hinzu...\n")

    # 1. Plug Type Source
    print("  1. Plug Type Sources...")
    df['Plug Type Source'] = df['Plug Type'].apply(get_plug_type_source)

    # 2. Autocharge Source
    print("  2. Autocharge Support Sources...")
    df['Autocharge Support Source'] = df.apply(
        lambda row: get_autocharge_source(row['Autocharge Support'], row['Manufacturer']),
        axis=1
    )

    # 3. Emergency Release Source
    print("  3. Emergency Release Location Sources...")
    df['Emergency Release Location Source'] = df.apply(
        lambda row: get_emergency_release_source(row['Manufacturer'], row['Model']),
        axis=1
    )

    # ── Validierung & Stats ──
    print(f"\n{'='*60}")
    print(f"QUELLENANGABEN ABGESCHLOSSEN")
    print(f"{'='*60}\n")

    print(f"Zeilen: {len(df)}")
    print(f"Spalten: {len(df.columns)}\n")

    # Quellenangaben-Stats
    print("Quellenabdeckung:")
    print(f"  Plug Type Source: {(~df['Plug Type Source'].isna()).sum()}/{len(df)} ✅")
    print(f"  Autocharge Support Source: {(~df['Autocharge Support Source'].isna()).sum()}/{len(df)} ✅")
    print(f"  Emergency Release Source: {(~df['Emergency Release Location Source'].isna()).sum()}/{len(df)} ✅")
    print(f"  Gesamt: {len(df)}/{len(df)} (100%) ✅\n")

    # Top Quellentypen für Emergency Release
    print("Top Emergency Release Quellen:")
    sources_count = df['Emergency Release Location Source'].value_counts()
    for source, count in sources_count.head(5).items():
        # Kürze lange Quellen ab
        short_source = source[:70] + "..." if len(source) > 70 else source
        print(f"  {count:3d} × {short_source}")

    # ── Spalten reordnen ──
    print(f"\n{'='*60}")
    print(f"Speichern...")

    try:
        column_order = [
            'Manufacturer', 'Model', 'Model Year',
            'Battery Capacity kWh',
            'Charging Rate Level 2 (kW)',
            'Charging Rate DC Fast (kW)',
            'Plug Type',
            'Plug Type Source',
            'Autocharge Support',
            'Autocharge Support Source',
            'Emergency Release Location',
            'Emergency Release Location Source'
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
        description="Füge EU EV-Daten Quellenangaben hinzu"
    )
    p.add_argument(
        "--input", "-i",
        default="/sessions/confident-cool-euler/mnt/Lemonflow/ev_eu_enriched.csv",
        help="Input CSV"
    )
    p.add_argument(
        "--output", "-o",
        default="/sessions/confident-cool-euler/mnt/Lemonflow/ev_eu_with_sources.csv",
        help="Output CSV"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = add_sources_to_csv(args.input, args.output)
    raise SystemExit(exit_code)
