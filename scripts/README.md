# Pipeline Scripts

The scripts are numbered in execution order. Each step produces a CSV that the next step consumes.

| # | Script | Input | Output | Description |
|---|--------|-------|--------|-------------|
| 1 | `scrape_ev_database_v4.py` | — | `ev_database_raw_v4.csv` | Scrapes ev-database.org list pages (EU BEVs) |
| 2 | `enrich_from_detail_pages_v5.py` | `ev_database_raw_v4.csv` | `ev_database_raw_v4_enriched_v5_complete.csv` | Multi-threaded detail-page enrichment (battery, AC, DC, plug) |
| 3 | `normalize_eu_data.py` | enriched CSV | `ev_eu_normalized.csv` | Deduplication, model-name cleanup, 1 225 → 831 rows |
| 4 | `enrich_eu_ev_data.py` | normalized CSV | `ev_eu_enriched.csv` | EU-specific fields: Plug & Charge, emergency release, Type 2+CCS2 plug standard |
| 5 | `fix_eu_data.py` | enriched EU CSV | same | Regex fixes for kWh/kW specs accidentally left in model names |
| 6 | `add_eu_sources.py` | enriched EU CSV | `ev_eu_enriched_v5_with_sources.csv` | Adds source columns (Plug Type Source, Autocharge Source, Emergency Release Source) |
| 7 | `Filter_afdc_list.py` | AFDC API response | `us_bev_clean.csv` | Filters AFDC US BEV endpoint response to relevant columns |
| 8 | `download_eu_plugins_discodata.py` | AFDC API (PHEV) | `eu_phev_clean.csv` | Fetches PHEV models from AFDC for EU; adds Vehicle Type column |
| 9 | `integrate_phev.py` | EU BEV CSV + `eu_phev_clean.csv` | `ev_global_FINAL.csv` | Merges EU BEVs + US BEVs + EU PHEVs into one global dataset |
| 10 | `build_lookup.py` | `ev_global_FINAL.csv` | same (enriched) | Fills missing battery/AC/DC specs using a 300+ model hardcoded lookup table |
| 11 | `deduplicate_regions.py` | `ev_global_FINAL.csv` | same (deduplicated) | Resolves EU/US duplicates caused by AFDC PHEV endpoint misclassifying BEVs |
| 12 | `gen_prompt_block.py` | `ev_global_FINAL.csv` | `ev_charging_prompt_block.txt` | Generates token-efficient pipe-separated text file for AI agent context |

The interactive dashboard (`ev_dashboard.html`) was generated separately as a single-file offline HTML with embedded JSON.

## Requirements

```
pip install requests beautifulsoup4 pandas
```
