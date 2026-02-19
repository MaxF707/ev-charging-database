# ⚡ EV Charging Database — EU + US (2024/2025)

A comprehensive dataset of **1,326 electric vehicle models** available in Europe and the United States, with structured charging specifications for use in AI agents and interactive exploration.

---

## 📦 Contents

| File | Description |
|------|-------------|
| `ev_dashboard.html` | **Interactive dashboard** — open directly in any browser, no server needed |
| `ev_charging_prompt_block.txt` | **AI prompt block** — token-efficient text for use as LLM context |
| `ev_global_FINAL.csv` | Full dataset in CSV format (all fields, all sources) |

---

## 🚀 Quick Start — Dashboard

**Just open the file in your browser:**

```bash
# macOS
open ev_dashboard.html

# Windows
start ev_dashboard.html

# Linux
xdg-open ev_dashboard.html
```

No installation, no server, no dependencies. The entire dataset is embedded in the HTML file.

---

## 🔍 Dashboard Features

- **Search** by brand or model name
- **Filter** by Region (EU / US / both), Brand, Plug Type, Autocharge support, and whether battery data is available
- **Sort** any column by clicking the header
- **Click any row** to open a detail panel showing all fields including full source references
- Live stats bar updates as you filter

**Screenshot overview:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ⚡ EV Charging Database          EU+US 2024/25         [1326 vehicles]  │
├──────────┬────────┬────────┬───────┬──────────┬─────┬─────┬────────────┤
│ Region   │ Brand  │ Model  │  Year │ Battery  │  AC │  DC │ Autocharge │
├──────────┼────────┼────────┼───────┼──────────┼─────┼─────┼────────────┤
│ 🇪🇺 EU   │ Tesla  │Model Y │ 2024  │  75 kWh  │ 11  │ 250 │ ✅ Yes     │
│ 🇺🇸 US   │ Audi   │ Q4     │ 2024  │  82 kWh  │ 11  │ 135 │ ✅ Yes     │
│ 🌍 EU+US │ Porsche│ Taycan │ 2024  │  93 kWh  │ 22  │ 270 │ ✅ Yes     │
└──────────┴────────┴────────┴───────┴──────────┴─────┴─────┴────────────┘
```

---

## 🤖 AI Prompt Block

The file `ev_charging_prompt_block.txt` is formatted for direct use as context in LLM prompts.

**Format per entry:**
```
Region|Model|Year|Battery(kWh)|AC_kW|DC_kW|PlugType|Autocharge:Y/N/P/?|Emergency:…
```

**Example entries:**
```
EU|Model Y|2024|75kWh|AC:11kW|DC:250kW|NACS (Berlin Giga) / Type 2 mit Adapter|Autocharge:Y|Emergency:Trunk: orange cable or touchscreen service
US|Q4 40 e-tron|2024|82kWh|AC:11kW|DC:125kW|CCS1 + J1772|Autocharge:Y|Emergency:Trunk: lift floor, remove panel driver side, pull yellow loop
```

**Autocharge key:** `Y` = yes / `N` = no / `P` = partial / `?` = unknown

**Token estimate:** ~48,000 tokens (fits in a 128k context window alongside other instructions)

**Sample prompt usage:**
```
You are a charging assistant. Use the following EV database to answer questions
about charging specifications, plug compatibility, and autocharge support.

<ev_database>
[paste contents of ev_charging_prompt_block.txt here]
</ev_database>

User question: Does the Hyundai Ioniq 6 support Autocharge at Ionity stations?
```

---

## 📊 Dataset Coverage

| Field | Coverage |
|-------|----------|
| Vehicles | 1,326 models (581 EU, 745 US, 54 in both) |
| Brands | 92 manufacturers |
| Battery Capacity | ~49% |
| AC Charging Rate | ~76% (EU) / ~47% (US) |
| DC Fast Charging | ~74% (EU) / ~61% (US) |
| Plug Type | **100%** |
| Autocharge Support | **100%** |
| Emergency Cable Release | **100%** |
| Source Documentation | **100%** |

---

## 🔌 Data Fields

| Field | Description | Example |
|-------|-------------|---------|
| `Manufacturer` | Brand name | `Tesla` |
| `Model` | Model name (cleaned) | `Model Y` |
| `Model Year` | Year | `2024` |
| `Battery Capacity kWh` | Usable battery size | `75.0` |
| `Charging Rate Level 2 (kW)` | Max AC on-board charger | `11.0` |
| `Charging Rate DC Fast (kW)` | Max DC fast charging | `250.0` |
| `Plug Type` | Connector standard | `Type 2 + CCS2` / `CCS1 + J1772` / `NACS` |
| `Autocharge Support` | Plug & Charge capability | `Ja - Plug & Charge (ab MY2023)` |
| `Emergency Release Location` | Manual cable release location | `Trunk: orange cable behind left panel` |
| `Region` | Market availability | `EU` / `US` / `EU + US` |
| `*_Source` | Source references for each enriched field | URLs / standards / manuals |

---

## 🗂️ Data Sources

**Primary scraping sources:**
- [EV Database EU](https://ev-database.org) — European vehicle specifications
- [AFDC / U.S. DOE](https://afdc.energy.gov) — U.S. Alternative Fuels Data Center

**Standards referenced:**
- IEC 62196-2 (Type 2 / Mennekes)
- CCS2 / CCS1 (Combined Charging System)
- NACS (North American Charging Standard)
- CHAdeMO Association Specification

**Charging networks referenced:**
- Ionity, Electrify Europe (NewMotion), Shell Recharge
- Electrify America, EVgo, ChargePoint
- Manufacturer networks: Tesla Supercharger, BMW ChargeNow, Audi ChargeConnect

---

## 🛠️ Methodology

Data was collected and enriched in a multi-stage pipeline:

1. **Web scraping** — BeautifulSoup scraping of listing and detail pages
2. **Detail page enrichment** — Parallel fetching of 1,225+ individual vehicle pages (8 worker threads)
3. **Model-name extraction** — Regex patterns extracting battery sizes from model name strings (e.g. `"64 kWh"`)
4. **Lookup tables** — 60+ model-specific charging specifications cross-referenced with manufacturer documentation
5. **EU/US enrichment** — Region-specific plug types, autocharge support by manufacturer/year, emergency release by model/platform/brand hierarchy
6. **Source documentation** — Every enriched field linked to primary sources

---

## ⚠️ Known Limitations

- Battery and charging rate data incomplete for some models (~50%) — the website does not publish all specs publicly
- Emergency release locations for ~26% of models default to "see owner's manual" (no public documentation found)
- Model year coverage: primarily 2024; some US entries include 2018–2023 where still on market
- Autocharge support reflects MY2023+ rollout status; older model years of the same model may differ

---

*Dataset compiled February 2026 | Pipeline: Python / BeautifulSoup / pandas*
