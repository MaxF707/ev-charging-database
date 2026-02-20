"""
deduplicate_regions.py
======================
Fixes EU/US duplicate entries in ev_global_FINAL.csv.

Background
----------
The AFDC PHEV endpoint returned many pure BEVs (e.g. Audi e-tron GT, BMW i4,
Porsche Taycan) as PHEVs. After merging EU BEVs + US BEVs + EU PHEVs,
these models appeared twice: once as a (correct) EU/US BEV and once as a
(false) EU PHEV. This script resolves conflicts using keyword detection on
model names and collapses duplicates into EU+US entries.

Logic
-----
For each (Manufacturer, Model) key appearing in more than one region:
  - If model name contains BEV keywords → remove the EU PHEV row,
    update the real BEV entry to EU+US.
  - If model name contains PHEV keywords → keep the EU PHEV row as EU+US,
    drop the US duplicate.

Result: 463 rows dropped, 333 region updates (EU+US: 54 → 387).
"""

import re
import pandas as pd

INPUT_CSV  = "ev_global_FINAL.csv"
OUTPUT_CSV = "ev_global_FINAL.csv"   # overwrites in-place

PHEV_KW = re.compile(
    r'\b(hybrid|plug.?in|phev|prime|e.hybrid|gte|4xe|t8|p400e|'
    r'tfsi\s*e|45e|30e|50e|60e|xse|phv|phe|ephv)\b', re.I
)
BEV_KW = re.compile(
    r'\b(e.tron|ioniq\s*[5-9]|ev[3-9]|id\.\d|taycan|ix\s*xdrive|'
    r'i[457]\s|bz4x|eq[abcse]|enyaq|mach.e|r5|r4|megane\s*e|'
    r'zoe|spring|e.208|e.2008|mokka.e|corsa.e|e.up|born)\b', re.I
)


def main():
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    print(f"Loaded {len(df)} rows")

    # Find (Manufacturer, Model) pairs that appear in multiple regions
    groups = df.groupby(["Manufacturer", "Model"])
    to_drop   = []
    to_update = {}   # index → new Region value

    for (mfr, model), grp in groups:
        if grp["Region"].nunique() <= 1 and len(grp) == 1:
            continue

        regions = set(grp["Region"].unique())
        if len(regions) <= 1:
            continue   # same region repeated – not a cross-region conflict

        model_lower = model.lower()
        is_bev  = bool(BEV_KW.search(model_lower))
        is_phev = bool(PHEV_KW.search(model_lower))

        eu_phev_idx = grp[
            (grp["Region"].str.contains("EU")) &
            (grp["Vehicle Type"] == "PHEV")
        ].index.tolist()

        bev_idx = grp[grp["Vehicle Type"] == "BEV"].index.tolist()

        if is_bev and not is_phev:
            # EU PHEV entry is wrong → drop it, promote BEV to EU+US
            to_drop.extend(eu_phev_idx)
            for i in bev_idx:
                to_update[i] = "EU+US"

        elif is_phev and not is_bev:
            # PHEV is correct → mark EU PHEV as EU+US, drop US duplicate
            for i in eu_phev_idx:
                to_update[i] = "EU+US"
            us_idx = grp[grp["Region"] == "US"].index.tolist()
            to_drop.extend(us_idx)

        else:
            # Ambiguous – merge by keeping EU+US for BEV, drop PHEV duplicates
            for i in bev_idx:
                to_update[i] = "EU+US"
            to_drop.extend(eu_phev_idx)

    # Apply updates and drops
    for idx, region in to_update.items():
        df.at[idx, "Region"] = region

    df = df.drop(index=to_drop).reset_index(drop=True)

    print(f"Dropped {len(to_drop)} rows, updated {len(to_update)} region fields")
    print(f"Remaining rows: {len(df)}")
    print("Region distribution:")
    print(df["Region"].value_counts().to_string())

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
