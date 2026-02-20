#!/usr/bin/env python3
"""
fix_eu_data.py

Korrigiert die rohen EV-Daten: Splittet Hersteller/Modell-Strings korrekt.
"""

import pandas as pd
import re

df = pd.read_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_database_raw.csv')

print(f"Original: {len(df)} Zeilen")
print(f"Spalten: {list(df.columns)}")

# Korrekte Hersteller-Liste (basierend auf top Herstellern)
MANUFACTURERS = [
    'Tesla', 'Porsche', 'Mercedes-Benz', 'Ford', 'Škoda',
    'Hyundai', 'Audi', 'Volkswagen', 'Polestar', 'BMW',
    'Kia', 'BYD', 'Volvo', 'CUPRA', 'Fiat', 'Mini',
    'Nissan', 'Peugeot', 'Renault', 'Chevrolet', 'Cadillac',
    'Genesis', 'Maxus', 'MG', 'Ora', 'GAC', 'Xpeng',
    'Hongqi', 'Dacia', 'Citroën', 'Opel', 'Toyota',
    'Lexus', 'Subaru', 'Mazda', 'Mitsubishi', 'Jeep',
    'Dodge', 'GMC', 'Honda', 'Acura', 'Lincoln',
    'Chrysler', 'Ram', 'Rivian', 'Lucid', 'Alfa Romeo',
    'Jaguar', 'Land Rover', 'Bentley', 'Rolls-Royce',
    'Maserati', 'Ferrari', 'Lamborghini', 'Bugatti'
]

def split_manufacturer_model(text):
    """Splittet "ManufacturerModel" in ("Manufacturer", "Model")"""

    if not isinstance(text, str) or not text:
        return "Unknown", "Unknown"

    text = text.strip()

    # Versuche zu matchken bekannte Hersteller vom Anfang
    for mfr in sorted(MANUFACTURERS, key=lambda x: -len(x)):  # Längste zuerst
        if text.startswith(mfr):
            model = text[len(mfr):].strip()

            # Entferne Hersteller auch vom Ende des Models (z.B. "iX3BMW" → "iX3")
            for mfr2 in sorted(MANUFACTURERS, key=lambda x: -len(x)):
                if model.endswith(mfr2) and mfr2 != mfr:
                    model = model[:-len(mfr2)].strip()
                    break

            if model:
                return mfr, model

    # Fallback: Split nach erstem Großbuchstaben nach Position 2
    for i in range(2, min(len(text), 10)):
        if text[i].isupper() and text[i-1].islower():
            return text[:i], text[i:]

    # Letzter Fallback
    parts = text.split()
    if len(parts) > 1:
        return parts[0], ' '.join(parts[1:])

    return text, "Unknown"

# Anwende Korrektur
df['Manufacturer_Fixed'] = df['Manufacturer'].apply(lambda x: split_manufacturer_model(x)[0])
df['Model_Fixed'] = df['Manufacturer'].apply(lambda x: split_manufacturer_model(x)[1])

# Ersetze Spalten
df['Manufacturer'] = df['Manufacturer_Fixed']
df['Model'] = df['Model_Fixed'].fillna(df['Model'])  # Nutze Model_Fixed, fallback zu Model

# Entferne temporäre Spalten
df = df.drop(['Manufacturer_Fixed', 'Model_Fixed'], axis=1)

# Speichere
df.to_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_database_raw_fixed.csv', index=False)

print(f"\n✅ Korrigiert: {len(df)} Zeilen")
print(f"\nBeispiele:")
print(df[['Manufacturer', 'Model', 'Battery Capacity kWh', 'Charging Rate DC Fast (kW)']].head(15).to_string())
print(f"\nTop Hersteller:")
print(df['Manufacturer'].value_counts().head(15))
