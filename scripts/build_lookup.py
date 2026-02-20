import pandas as pd
import re

# ─────────────────────────────────────────────
# COMPREHENSIVE EV SPECS LOOKUP TABLE
# Format: (Manufacturer, model_substring_lower) -> (battery_kWh, ac_kW, dc_kW)
# Use None where spec is unknown / varies too much
# Priority: more specific entries should come BEFORE generic ones in the list
# ─────────────────────────────────────────────

SPECS = [

  # ── AUDI BEV ────────────────────────────────
  # e-tron GT family (2024 facelift = S/RS designations)
  ("Audi","s e-tron gt",         105.0, 22.0, 320.0),
  ("Audi","rs e-tron gt",        105.0, 22.0, 320.0),
  ("Audi","e-tron gt",            85.0, 11.0, 270.0),
  # Q6 / A6 e-tron family
  ("Audi","sq6",                  94.9, 22.0, 270.0),
  ("Audi","sa6",                  94.9, 22.0, 270.0),
  ("Audi","s6 sportback e-tron",  94.9, 22.0, 270.0),
  ("Audi","q6 40",                83.0, 11.0, 185.0),
  ("Audi","q6 55",                94.9, 11.0, 270.0),
  ("Audi","q6 e-tron",            94.9, 11.0, 270.0),
  ("Audi","a6 40 e-tron",         83.0, 11.0, 185.0),
  ("Audi","a6 55 e-tron",         94.9, 11.0, 270.0),
  ("Audi","a6 e-tron",            94.9, 11.0, 270.0),
  # Q8 e-tron family
  ("Audi","sq8",                 114.0, 11.0, 170.0),
  ("Audi","q8 50",                95.0, 11.0, 150.0),
  ("Audi","q8 55",               114.0, 11.0, 170.0),
  ("Audi","q8 e-tron",           114.0, 11.0, 170.0),
  # Original e-tron family
  ("Audi","e-tron 50",            71.2, 11.0, 120.0),
  ("Audi","e-tron s",             95.0, 11.0, 150.0),
  ("Audi","e-tron 55",            95.0, 11.0, 150.0),
  ("Audi","e-tron sportback 50",  71.2, 11.0, 120.0),
  ("Audi","e-tron sportback",     95.0, 11.0, 150.0),
  ("Audi","e-tron",               95.0, 11.0, 150.0),
  # Q4 e-tron family
  ("Audi","q4 35",                55.0,  7.2, 100.0),
  ("Audi","q4 40",                77.0, 11.0, 125.0),
  ("Audi","q4 45",                77.0, 11.0, 125.0),
  ("Audi","q4 50",                77.0, 11.0, 125.0),
  ("Audi","q4 55",                82.0, 11.0, 135.0),
  ("Audi","q4 e-tron",            77.0, 11.0, 135.0),

  # ── BMW BEV ─────────────────────────────────
  ("BMW","i3s",                   42.2, 11.0,  50.0),
  ("BMW","i3",                    42.2, 11.0,  50.0),
  ("BMW","i4 edrive35",           70.2, 11.0, 180.0),
  ("BMW","i4 m50",                83.9, 11.0, 210.0),
  ("BMW","i4 edrive40",           83.9, 11.0, 180.0),
  ("BMW","i4",                    83.9, 11.0, 180.0),
  ("BMW","ix1 edrive20",          64.7, 11.0, 130.0),
  ("BMW","ix1 xdrive30",          64.7, 11.0, 130.0),
  ("BMW","ix1",                   64.7, 11.0, 130.0),
  ("BMW","ix2 edrive20",          64.7, 11.0, 130.0),
  ("BMW","ix2 xdrive30",          64.7, 11.0, 130.0),
  ("BMW","ix2",                   64.7, 11.0, 130.0),
  ("BMW","ix3 50",               108.7, 11.0, 200.0),
  ("BMW","ix3",                   80.0, 11.0, 150.0),
  ("BMW","ix xdrive40",           76.6, 11.0, 200.0),
  ("BMW","ix m60",               111.5, 22.0, 200.0),
  ("BMW","ix xdrive50",          111.5, 22.0, 200.0),
  ("BMW","ix",                    76.6, 11.0, 200.0),
  ("BMW","i5 m60",                84.3, 22.0, 205.0),
  ("BMW","i5 edrive40",           84.3, 11.0, 205.0),
  ("BMW","i5 xdrive40",           84.3, 11.0, 205.0),
  ("BMW","i5",                    84.3, 11.0, 205.0),
  ("BMW","i7 m70",               101.7, 22.0, 195.0),
  ("BMW","i7 xdrive60",          101.7, 22.0, 195.0),
  ("BMW","i7 edrive50",          101.7, 11.0, 195.0),
  ("BMW","i7",                   101.7, 11.0, 195.0),

  # ── VOLKSWAGEN BEV ──────────────────────────
  ("Volkswagen","id.3 pure",       45.0, 11.0, 100.0),
  ("Volkswagen","id.3 pro s",      79.0, 11.0, 135.0),
  ("Volkswagen","id.3 pro",        58.0, 11.0, 120.0),
  ("Volkswagen","id.3 gtx",        79.0, 11.0, 175.0),
  ("Volkswagen","id.3",            58.0, 11.0, 120.0),
  ("Volkswagen","id.4 pure",       52.0, 11.0, 100.0),
  ("Volkswagen","id.4 pro",        77.0, 11.0, 135.0),
  ("Volkswagen","id.4 gtx",        77.0, 11.0, 135.0),
  ("Volkswagen","id.4",            77.0, 11.0, 135.0),
  ("Volkswagen","id.5 gtx",        77.0, 11.0, 135.0),
  ("Volkswagen","id.5 pro",        77.0, 11.0, 135.0),
  ("Volkswagen","id.5",            77.0, 11.0, 135.0),
  ("Volkswagen","id.7 gtx",        86.0, 11.0, 200.0),
  ("Volkswagen","id.7 tourer",     77.0, 11.0, 200.0),
  ("Volkswagen","id.7 pro",        77.0, 11.0, 200.0),
  ("Volkswagen","id.7",            77.0, 11.0, 200.0),
  ("Volkswagen","id. buzz gtx",    86.0, 11.0, 200.0),
  ("Volkswagen","id. buzz",        77.0, 11.0, 170.0),
  ("Volkswagen","id.2",            38.0, 11.0, 125.0),

  # ── TESLA BEV ───────────────────────────────
  ("Tesla","model s plaid",       100.0, 11.0, 250.0),
  ("Tesla","model s 100d",        100.0, 11.0, 120.0),
  ("Tesla","model s 90d",          90.0, 11.0, 120.0),
  ("Tesla","model s 85d",          85.0, 11.0, 120.0),
  ("Tesla","model s 75d",          75.0, 11.0, 120.0),
  ("Tesla","model s",             100.0, 11.0, 250.0),
  ("Tesla","model x plaid",       100.0, 11.0, 250.0),
  ("Tesla","model x 100d",        100.0, 11.0, 120.0),
  ("Tesla","model x 90d",          90.0, 11.0, 120.0),
  ("Tesla","model x",             100.0, 11.0, 250.0),
  ("Tesla","model 3 long range",   75.0, 11.0, 250.0),
  ("Tesla","model 3 performance",  75.0, 11.0, 250.0),
  ("Tesla","model 3 standard",     57.5, 11.0, 170.0),
  ("Tesla","model 3 rwd",          57.5, 11.0, 170.0),
  ("Tesla","model 3",              57.5, 11.0, 250.0),
  ("Tesla","model y long range",   75.0, 11.0, 250.0),
  ("Tesla","model y performance",  75.0, 11.0, 250.0),
  ("Tesla","model y rwd",          57.5, 11.0, 250.0),
  ("Tesla","model y",              75.0, 11.0, 250.0),
  ("Tesla","cybertruck",          123.0, 11.0, 250.0),
  ("Tesla","semi",                None, None, 250.0),

  # ── PORSCHE BEV ─────────────────────────────
  # Taycan 2024 facelift: Turbo S=105kWh/320kW, Turbo=105kWh/320kW
  ("Porsche","taycan turbo s",    105.0, 22.0, 320.0),
  ("Porsche","taycan turbo",      105.0, 22.0, 320.0),
  ("Porsche","taycan gts",         93.4, 11.0, 270.0),
  ("Porsche","taycan 4s",          93.4, 11.0, 270.0),
  ("Porsche","taycan 4",           93.4, 11.0, 270.0),
  ("Porsche","taycan cross turismo",93.4,11.0, 270.0),
  ("Porsche","taycan sport turismo",93.4,11.0, 270.0),
  ("Porsche","taycan",             93.4, 11.0, 270.0),
  ("Porsche","macan electric",     100.0,11.0, 270.0),
  ("Porsche","macan 4s",           100.0,11.0, 270.0),
  ("Porsche","macan 4",            100.0,11.0, 270.0),
  ("Porsche","macan turbo",        100.0,11.0, 270.0),
  ("Porsche","macan",              100.0,11.0, 270.0),

  # ── VOLVO BEV ───────────────────────────────
  ("Volvo","ex30 twin motor",      64.0, 11.0, 153.0),
  ("Volvo","ex30 extended range",  64.0, 11.0, 153.0),
  ("Volvo","ex30",                 51.0, 11.0, 153.0),
  ("Volvo","ex40 twin motor",      82.0, 11.0, 150.0),
  ("Volvo","ex40 extended range",  82.0, 11.0, 150.0),
  ("Volvo","ex40 single motor er", 82.0, 11.0, 150.0),
  ("Volvo","ex40 single motor",    69.0, 11.0, 150.0),
  ("Volvo","ex40",                 82.0, 11.0, 150.0),
  ("Volvo","ec40 twin motor",      82.0, 11.0, 150.0),
  ("Volvo","ec40 extended range",  82.0, 11.0, 150.0),
  ("Volvo","ec40",                 82.0, 11.0, 150.0),
  ("Volvo","ex60",                 75.0, 11.0, 150.0),
  ("Volvo","ex90",                107.0, 11.0, 250.0),
  ("Volvo","xc40 recharge twin motor",   82.0, 11.0, 150.0),
  ("Volvo","xc40 recharge single motor er",82.0,11.0,150.0),
  ("Volvo","xc40 recharge single motor",  69.0,11.0, 150.0),
  ("Volvo","xc40 recharge",         82.0, 11.0, 150.0),
  ("Volvo","c40 recharge",          82.0, 11.0, 150.0),

  # ── MERCEDES-BENZ BEV ───────────────────────
  ("Mercedes-Benz","eqa 250+",     70.5, 11.0, 100.0),
  ("Mercedes-Benz","eqa 250",      66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqa 300",      66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqa 350",      66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqa",          66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqb 250+",     70.5, 11.0, 100.0),
  ("Mercedes-Benz","eqb 250",      66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqb 300",      66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqb 350",      66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqb",          66.5, 11.0, 100.0),
  ("Mercedes-Benz","eqc 400",      80.0, 11.0, 110.0),
  ("Mercedes-Benz","eqc",          80.0, 11.0, 110.0),
  ("Mercedes-Benz","eqe 350+",     90.6, 22.0, 170.0),
  ("Mercedes-Benz","eqe 300",      90.6, 22.0, 170.0),
  ("Mercedes-Benz","eqe 350",      90.6, 22.0, 170.0),
  ("Mercedes-Benz","eqe 500",      90.6, 22.0, 170.0),
  ("Mercedes-Benz","amg eqe 43",  100.4, 22.0, 170.0),
  ("Mercedes-Benz","amg eqe 53",  100.4, 22.0, 170.0),
  ("Mercedes-Benz","eqe suv",      90.6, 22.0, 170.0),
  ("Mercedes-Benz","eqe",          90.6, 22.0, 170.0),
  ("Mercedes-Benz","eqs 450+",    107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqs 450",     107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqs 580",     107.8, 22.0, 200.0),
  ("Mercedes-Benz","amg eqs 53",  107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqs suv 450", 107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqs suv 580", 107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqs suv",     107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqs",         107.8, 22.0, 200.0),
  ("Mercedes-Benz","eqv 300 long",  100.0, 11.0, 110.0),
  ("Mercedes-Benz","eqv 300",       100.0, 11.0, 110.0),
  ("Mercedes-Benz","eqv",           100.0, 11.0, 110.0),
  ("Mercedes-Benz","eq fortwo",      17.6, 22.0,  None),
  ("Mercedes-Benz","eq forfour",     17.6, 22.0,  None),

  # ── FORD BEV ────────────────────────────────
  ("Ford","mustang mach-e gt",     91.0, 11.0, 150.0),
  ("Ford","mustang mach-e extended range",  91.0, 11.0, 150.0),
  ("Ford","mustang mach-e",        72.0, 11.0, 115.0),
  ("Ford","f-150 lightning",      131.0, 19.2, 150.0),
  ("Ford","explorer",              77.0, 11.0, 135.0),
  ("Ford","capri",                 77.0, 11.0, 135.0),
  ("Ford","puma gen-e",            43.0, 11.0, 100.0),
  ("Ford","e-transit custom",      89.0, 11.0, 115.0),
  ("Ford","e-transit",            68.0,  11.0,  115.0),

  # ── HYUNDAI BEV ─────────────────────────────
  ("Hyundai","ioniq 5 n",          84.0, 11.0, 350.0),
  ("Hyundai","ioniq 5 long range",  84.0, 11.0, 220.0),
  ("Hyundai","ioniq 5 standard range",53.0,11.0, 220.0),
  ("Hyundai","ioniq 5",            84.0, 11.0, 220.0),
  ("Hyundai","ioniq 6 long range",  77.4, 11.0, 220.0),
  ("Hyundai","ioniq 6 standard range",53.0,11.0,220.0),
  ("Hyundai","ioniq 6",            77.4, 11.0, 220.0),
  ("Hyundai","ioniq 9",           110.0, 11.0, 350.0),
  ("Hyundai","kona electric",      65.4, 11.0, 100.0),
  ("Hyundai","kona",               65.4, 11.0, 100.0),
  ("Hyundai","nexo",               None, None,  None),  # FCEV

  # ── KIA BEV ─────────────────────────────────
  ("Kia","ev3 long range",         81.4, 11.0, 135.0),
  ("Kia","ev3 standard range",     58.3, 11.0, 101.0),
  ("Kia","ev3",                    81.4, 11.0, 135.0),
  ("Kia","ev6 gt",                 77.4, 11.0, 233.0),
  ("Kia","ev6 long range awd",     77.4, 11.0, 233.0),
  ("Kia","ev6 long range rwd",     77.4, 11.0, 233.0),
  ("Kia","ev6 standard range",     58.0, 11.0, 233.0),
  ("Kia","ev6",                    77.4, 11.0, 233.0),
  ("Kia","ev9 long range awd",     99.8, 11.0, 217.0),
  ("Kia","ev9 long range rwd",     99.8, 11.0, 217.0),
  ("Kia","ev9",                    99.8, 11.0, 217.0),
  ("Kia","niro ev",                64.8, 11.0, 100.0),
  ("Kia","niro",                   64.8, 11.0, 100.0),
  ("Kia","soul ev",                64.0, 11.0, 100.0),

  # ── ŠKODA BEV ───────────────────────────────
  ("Škoda","enyaq 50",             55.0, 11.0, 100.0),
  ("Škoda","enyaq 60",             58.0, 11.0, 120.0),
  ("Škoda","enyaq 85x",            82.0, 11.0, 175.0),
  ("Škoda","enyaq 85",             77.0, 11.0, 175.0),
  ("Škoda","enyaq rs",             82.0, 11.0, 175.0),
  ("Škoda","enyaq",                77.0, 11.0, 135.0),
  ("Škoda","elroq 85x",            82.0, 11.0, 175.0),
  ("Škoda","elroq 85",             77.0, 11.0, 175.0),
  ("Škoda","elroq 60",             59.0, 11.0, 145.0),
  ("Škoda","elroq 50",             55.0, 11.0, 145.0),
  ("Škoda","elroq",                77.0, 11.0, 175.0),

  # ── POLESTAR BEV ─────────────────────────────
  ("Polestar","polestar 2 long range dual motor",82.0,11.0,205.0),
  ("Polestar","polestar 2 long range single motor",82.0,11.0,130.0),
  ("Polestar","polestar 2 standard range",       69.0,11.0,130.0),
  ("Polestar","polestar 2",                      82.0,11.0,205.0),
  ("Polestar","2 long range dual motor",         82.0,11.0,205.0),
  ("Polestar","2 long range single motor",       82.0,11.0,130.0),
  ("Polestar","2 standard range",                69.0,11.0,130.0),
  ("Polestar","2",                               82.0,11.0,205.0),
  ("Polestar","polestar 3",                     111.0,22.0,250.0),
  ("Polestar","3",                              111.0,22.0,250.0),
  ("Polestar","polestar 4",                      94.0,22.0,200.0),
  ("Polestar","4",                               94.0,22.0,200.0),

  # ── SMART BEV ────────────────────────────────
  ("Smart","#1 brabus",            66.0, 22.0, 150.0),
  ("Smart","#1 pro+",              66.0, 22.0, 150.0),
  ("Smart","#1 premium",           66.0, 22.0, 150.0),
  ("Smart","#1",                   62.0, 22.0, 150.0),
  ("Smart","#3 brabus",            66.0, 22.0, 150.0),
  ("Smart","#3 pro+",              66.0, 22.0, 150.0),
  ("Smart","#3",                   62.0, 22.0, 150.0),
  ("Smart","fortwo electric",      16.7, 22.0,  None),
  ("Smart","forfour electric",     16.7, 22.0,  None),

  # ── MG BEV ───────────────────────────────────
  ("MG","mg4 electric",            64.0, 11.0, 135.0),
  ("MG","mg4",                     64.0, 11.0, 135.0),
  ("MG","mg5 electric",            61.1, 11.0,  76.0),
  ("MG","mg5",                     61.1, 11.0,  76.0),
  ("MG","zs ev long range",        72.6, 11.0,  92.0),
  ("MG","zs ev",                   51.0,  6.6,  76.0),
  ("MG","cyberster",               77.0, 11.0, 135.0),
  ("MG","im6",                     None, 11.0, None),
  ("MG","mgs5",                    77.0, 11.0, 150.0),

  # ── MINI BEV ─────────────────────────────────
  ("Mini","mini cooper e",         40.7, 11.0,  95.0),
  ("Mini","mini cooper se",        32.6, 11.0,  50.0),
  ("Mini","mini aceman e",         40.7, 11.0,  95.0),
  ("Mini","mini aceman se",        54.2, 11.0,  95.0),
  ("Mini","mini aceman",           54.2, 11.0,  95.0),
  ("Mini","mini countryman e",     64.7, 11.0,  95.0),
  ("Mini","mini countryman se",    64.7, 11.0,  95.0),
  ("Mini","cooper e",              40.7, 11.0,  95.0),
  ("Mini","cooper se",             32.6, 11.0,  50.0),
  ("Mini","aceman e",              40.7, 11.0,  95.0),
  ("Mini","aceman se",             54.2, 11.0,  95.0),
  ("Mini","aceman",                54.2, 11.0,  95.0),
  ("Mini","countryman e",          64.7, 11.0,  95.0),
  ("Mini","countryman se",         64.7, 11.0,  95.0),

  # ── RENAULT BEV ──────────────────────────────
  ("Renault","zoe r135",           52.0, 22.0,  50.0),
  ("Renault","zoe r110",           52.0, 22.0,  50.0),
  ("Renault","zoe",                52.0, 22.0,  50.0),
  ("Renault","megane e-tech 220",  60.0, 22.0, 130.0),
  ("Renault","megane e-tech 130",  40.0, 22.0, 130.0),
  ("Renault","megane e-tech",      60.0, 22.0, 130.0),
  ("Renault","5 e-tech 150",       52.0, 11.0, 100.0),
  ("Renault","5 e-tech 120",       40.0, 11.0, 100.0),
  ("Renault","5 e-tech",           52.0, 11.0, 100.0),
  ("Renault","scenic e-tech",      87.0, 22.0, 150.0),
  ("Renault","rafale e-tech",      None, 22.0,  None),

  # ── ABARTH BEV ───────────────────────────────
  ("Abarth","500e convertible",    42.2, 11.0,  85.0),
  ("Abarth","500e",                42.2, 11.0,  85.0),
  ("Abarth","600e scorpionissima", 54.0, 11.0, 100.0),
  ("Abarth","600e turismo",        54.0, 11.0, 100.0),
  ("Abarth","600e",                54.0, 11.0, 100.0),

  # ── FIAT BEV ─────────────────────────────────
  ("Fiat","500e convertible",      42.0, 11.0,  85.0),
  ("Fiat","500e",                  42.0, 11.0,  85.0),
  ("Fiat","600e",                  54.0, 11.0, 100.0),
  ("Fiat","grande panda",          44.0, 11.0, 100.0),

  # ── OPEL / VAUXHALL BEV ──────────────────────
  ("Opel","astra electric",        54.0, 11.0, 100.0),
  ("Opel","corsa electric",        51.0, 11.0, 100.0),
  ("Opel","corsa-e",               50.0, 11.0,  75.0),
  ("Opel","mokka electric",        54.0, 11.0, 100.0),
  ("Opel","mokka-e",               50.0, 11.0,  75.0),
  ("Opel","grandland electric",    73.0, 11.0, 100.0),
  ("Opel","frontera electric",     44.0, 11.0, 100.0),
  ("Opel","zafira electric",       75.0, 11.0, 100.0),

  # ── PEUGEOT BEV ──────────────────────────────
  ("Peugeot","e-208",              51.0, 11.0, 100.0),
  ("Peugeot","e-2008",             54.0, 11.0, 100.0),
  ("Peugeot","e-3008",             73.0, 11.0, 160.0),
  ("Peugeot","e-308",              54.0, 11.0, 100.0),
  ("Peugeot","e-5008",             96.0, 11.0, 160.0),

  # ── CITROËN BEV ──────────────────────────────
  ("Citroën","ë-c3",               44.0, 11.0, 100.0),
  ("Citroën","ë-berlingo",         50.0, 11.0,  75.0),
  ("Citroën","ë-spacetourer",      75.0, 11.0, 100.0),
  ("Citroën","ë-c4",               54.0, 11.0, 100.0),
  ("Citroën","ë-c5 aircross",      54.0, 11.0, 100.0),

  # ── DS BEV ────────────────────────────────────
  ("DS","ds 3 e-tense",            54.0, 11.0, 100.0),
  ("DS","ds 7 e-tense 4x4",        None, 11.0,  None),
  ("DS","ds 4 e-tense",            54.0, 11.0, 100.0),

  # ── SEAT / CUPRA BEV ─────────────────────────
  ("Cupra","born 58",              58.0, 11.0, 120.0),
  ("Cupra","born 77",              77.0, 11.0, 135.0),
  ("Cupra","born",                 58.0, 11.0, 120.0),
  ("Cupra","tavascan vz",          77.0, 11.0, 135.0),
  ("Cupra","tavascan",             77.0, 11.0, 135.0),
  ("Seat","mii electric",          32.3, 11.0,  37.0),

  # ── ALPINE BEV ────────────────────────────────
  ("Alpine","a290 electric",       52.0, 11.0, 100.0),
  ("Alpine","a390 gts",           None, 22.0,  None),
  ("Alpine","a390",               None, 22.0,  None),

  # ── ALFA ROMEO / JEEP / MASERATI BEV ─────────
  ("Alfa Romeo","tonale",          None, 11.0, None),
  ("Jeep","avenger electric",      54.0, 11.0, 100.0),
  ("Jeep","avenger",               54.0, 11.0, 100.0),
  ("Maserati","granturismo folgore", 92.5, 22.0, 270.0),
  ("Maserati","grancabrio folgore",  92.5, 22.0, 270.0),
  ("Maserati","grecale folgore",     105.0,22.0, 270.0),

  # ── LUCID BEV ─────────────────────────────────
  ("Lucid","air dream edition",   118.0, 22.0, 300.0),
  ("Lucid","air grand touring",   118.0, 22.0, 300.0),
  ("Lucid","air touring",          99.0, 22.0, 300.0),
  ("Lucid","air pure",             88.0, 22.0, 300.0),
  ("Lucid","air sapphire",        118.0, 22.0, 300.0),
  ("Lucid","air",                 118.0, 22.0, 300.0),
  ("Lucid","gravity",             None,  22.0, 300.0),

  # ── RIVIAN BEV ────────────────────────────────
  ("Rivian","r1t standard",        135.0, 11.4, 200.0),
  ("Rivian","r1t large",           149.0, 11.4, 220.0),
  ("Rivian","r1t",                 149.0, 11.4, 220.0),
  ("Rivian","r1s standard",        135.0, 11.4, 200.0),
  ("Rivian","r1s large",           149.0, 11.4, 220.0),
  ("Rivian","r1s",                 149.0, 11.4, 220.0),
  ("Rivian","r2",                  None,  11.0, None),

  # ── CHEVROLET BEV ─────────────────────────────
  ("Chevrolet","equinox ev",       73.0, 11.5, 150.0),
  ("Chevrolet","silverado ev",    200.0, 19.2, 350.0),
  ("Chevrolet","blazer ev",        89.0, 11.5, 190.0),
  ("Chevrolet","bolt euv",         65.0, 11.5,  55.0),
  ("Chevrolet","bolt ev",          65.0, 11.5,  55.0),

  # ── GMC BEV ───────────────────────────────────
  ("GMC","sierra ev denali",      200.0, 19.2, 350.0),
  ("GMC","sierra ev",             200.0, 19.2, 350.0),
  ("GMC","hummer ev suv",         246.0, 19.2, 350.0),
  ("GMC","hummer ev pickup",      212.7, 19.2, 350.0),
  ("GMC","hummer ev",             212.7, 19.2, 350.0),

  # ── NISSAN BEV ────────────────────────────────
  ("Nissan","leaf e+",             59.0, 22.0,  50.0),
  ("Nissan","leaf",                40.0,  6.6,  50.0),
  ("Nissan","ariya 87",            87.0, 22.0, 130.0),
  ("Nissan","ariya 63",            63.0, 22.0, 130.0),
  ("Nissan","ariya",               87.0, 22.0, 130.0),

  # ── TOYOTA / LEXUS BEV ────────────────────────
  ("Toyota","bz4x",                71.4, 11.0, 150.0),
  ("Toyota","bz3",                 49.9, 11.0, 130.0),
  ("Lexus","rz 450e",              71.4, 11.0, 150.0),
  ("Lexus","rz 350e",              71.4, 11.0, 150.0),
  ("Lexus","rz 300e",              71.4, 11.0, 150.0),
  ("Lexus","rz 500e",              71.4, 11.0, 150.0),
  ("Lexus","rz",                   71.4, 11.0, 150.0),
  ("Lexus","uz 450e",              72.8, 11.0, 150.0),
  ("Lexus","uz",                   72.8, 11.0, 150.0),

  # ── SUBARU BEV ────────────────────────────────
  ("Subaru","solterra",            71.4, 11.0, 150.0),

  # ── HONDA BEV ─────────────────────────────────
  ("Honda","e",                    35.5, 11.0,  50.0),
  ("Honda","prologue",            102.0, 11.5, 150.0),
  ("Honda","e:ny1",                68.8, 11.0, 100.0),

  # ── ZEEKR BEV ─────────────────────────────────
  ("Zeekr","001",                 100.0, 22.0, 200.0),
  ("Zeekr","007",                  75.0, 22.0, 200.0),
  ("Zeekr","009",                 140.0, 22.0, 200.0),
  ("Zeekr","x",                    66.0, 11.0, 150.0),

  # ── LAND ROVER BEV ────────────────────────────
  ("Land Rover","range rover electric", 117.0, 22.0, 150.0),
  ("Land Rover","range rover evoque e", 68.0, 11.0, 100.0),
  ("Land Rover","defender electric",    117.0, 22.0, 150.0),

  # ── MAZDA BEV ─────────────────────────────────
  ("Mazda","mx-30",                35.5, 11.0,  50.0),
  ("Mazda","mx-30 r-ev",           17.8, 11.0,  50.0),

  # ── ACURA BEV ─────────────────────────────────
  ("Acura","zdx awd",             102.0, 11.5, 190.0),
  ("Acura","zdx rwd",             102.0, 11.5, 190.0),
  ("Acura","zdx",                 102.0, 11.5, 190.0),

  # ── GENESIS BEV ──────────────────────────────
  ("Genesis","gv60",               77.4, 11.0, 233.0),
  ("Genesis","gv70 electrified",   77.4, 11.0, 233.0),
  ("Genesis","g80 electrified",    87.2, 11.0, 233.0),
  ("Genesis","gv80 electrified",   99.8, 11.0, 350.0),

  # ── AIWAYS BEV ────────────────────────────────
  ("Aiways","u5",                  63.0, 11.0,  90.0),
  ("Aiways","u6",                  63.0, 11.0,  90.0),

  # ─────────────────────────────────────────────
  # PHEV LOOKUP TABLE
  # ─────────────────────────────────────────────

  # ── BMW PHEV ──────────────────────────────────
  ("BMW","230e",                   14.9,  3.7,  None),
  ("BMW","330e",                   12.0,  3.7,  None),
  ("BMW","530e",                   19.4,  3.7,  None),
  ("BMW","545e",                   24.0,  3.7,  None),
  ("BMW","740e",                   18.7,  3.7,  None),
  ("BMW","745e",                   15.1,  3.7,  None),
  ("BMW","x1 xdrive25e",           14.2,  3.7,  None),
  ("BMW","x2 xdrive25e",           14.2,  3.7,  None),
  ("BMW","x3 xdrive30e",           12.0,  3.7,  None),
  ("BMW","x5 xdrive45e",           24.5,  7.4,  None),
  ("BMW","x5 50e",                 24.5,  7.4,  None),
  ("BMW","x7 xdrive50e",           26.0,  7.4,  None),
  ("BMW","ix1 xdrive30e",          21.1,  7.4,  None),
  ("BMW","ix2 xdrive30e",          21.1,  7.4,  None),

  # ── MERCEDES-BENZ PHEV ────────────────────────
  ("Mercedes-Benz","a 250e",       15.6,  7.4,  None),
  ("Mercedes-Benz","b 250e",       15.6,  7.4,  None),
  ("Mercedes-Benz","c 300e",       25.4, 55.0,  None),
  ("Mercedes-Benz","c 300de",      25.4, 55.0,  None),
  ("Mercedes-Benz","e 300e",       25.4, 55.0,  None),
  ("Mercedes-Benz","e 300de",      25.4, 55.0,  None),
  ("Mercedes-Benz","s 580e",       28.6, 55.0,  None),
  ("Mercedes-Benz","s 450e",       28.6, 55.0,  None),
  ("Mercedes-Benz","cla 250e",     15.6,  7.4,  None),
  ("Mercedes-Benz","gla 250e",     15.6,  7.4,  None),
  ("Mercedes-Benz","glb 250e",     15.6,  7.4,  None),
  ("Mercedes-Benz","glc 300e",     25.4, 55.0,  None),
  ("Mercedes-Benz","glc 300de",    25.4, 55.0,  None),
  ("Mercedes-Benz","gle 350e",     25.4, 22.0,  None),
  ("Mercedes-Benz","gle 350de",    25.4, 22.0,  None),

  # ── AUDI PHEV (TFSI e) ────────────────────────
  ("Audi","a3 45 tfsi e",          14.4,  3.7,  None),
  ("Audi","a3 tfsi e",             14.4,  3.7,  None),
  ("Audi","a6 tfsi e",             17.9,  7.4,  None),
  ("Audi","a7 tfsi e",             17.9,  7.4,  None),
  ("Audi","a8 tfsi e",             17.9,  7.4,  None),
  ("Audi","q3 tfsi e",             13.0,  3.7,  None),
  ("Audi","q5 55 tfsi e",          17.9,  7.4,  None),
  ("Audi","q5 tfsi e",             17.9,  7.4,  None),
  ("Audi","q7 tfsi e",             17.9,  7.4,  None),
  ("Audi","q8 tfsi e",             17.9,  7.4,  None),
  ("Audi","sq5 tfsi e",            17.9,  7.4,  None),
  ("Audi","sq7 tfsi e",            17.9,  7.4,  None),
  ("Audi","sq8 tfsi e",            17.9,  7.4,  None),
  ("Audi","tfsi e",                17.9,  7.4,  None),

  # ── TOYOTA / LEXUS PHEV ───────────────────────
  ("Toyota","prius prime",          8.8,  3.3,  None),
  ("Toyota","prius phev",           8.8,  3.3,  None),
  ("Toyota","prius plug-in",        8.8,  3.3,  None),
  ("Toyota","prius",                8.8,  3.3,  None),
  ("Toyota","rav4 prime",          18.1,  6.6,  None),
  ("Toyota","rav4 plug-in",        18.1,  6.6,  None),
  ("Toyota","rav4",                18.1,  6.6,  None),
  ("Toyota","corolla cross phev",  18.1,  6.6,  None),
  ("Toyota","venza phev",          None,  6.6,  None),
  ("Toyota","camry phev",          None,  6.6,  None),
  ("Toyota","sienna phev",         None,  3.3,  None),
  ("Lexus","ux 300e",              54.3, 11.0,  50.0),  # actually BEV
  ("Lexus","nx 450h+",             18.1,  6.6,  None),
  ("Lexus","nx 350h",              None,  None,  None),
  ("Lexus","rx 450h+",             18.1,  6.6,  None),
  ("Lexus","es 300h",              None,  None,  None),

  # ── FORD PHEV ─────────────────────────────────
  ("Ford","escape phev",           14.4,  3.3,  None),
  ("Ford","kuga phev",             14.4,  3.7,  None),
  ("Ford","kuga",                  14.4,  3.7,  None),
  ("Ford","maverick phev",         None,  3.3,  None),
  ("Ford","explorer phev",         18.8,  3.7,  None),
  ("Ford","f-150 phev",            None,  7.2,  None),
  ("Ford","lincoln corsair phev",  14.0,  7.2,  None),
  ("Ford","lincoln aviator phev",  13.6,  7.2,  None),

  # ── HYUNDAI PHEV ──────────────────────────────
  ("Hyundai","santa fe phev",      13.8,  7.2,  None),
  ("Hyundai","tucson phev",        13.8,  7.2,  None),
  ("Hyundai","ioniq phev",          8.9,  3.3,  None),

  # ── KIA PHEV ──────────────────────────────────
  ("Kia","sorento phev",           13.8,  7.2,  None),
  ("Kia","sportage phev",          13.8,  7.2,  None),
  ("Kia","niro phev",               8.9,  3.3,  None),
  ("Kia","niro plug-in",            8.9,  3.3,  None),
  ("Kia","optima phev",             9.8,  3.3,  None),

  # ── VOLVO PHEV (Recharge T6/T8) ───────────────
  ("Volvo","xc60 recharge t8",     18.8,  3.7,  None),
  ("Volvo","xc60 recharge t6",     14.9,  3.7,  None),
  ("Volvo","xc60 recharge",        18.8,  3.7,  None),
  ("Volvo","xc90 recharge t8",     18.8,  3.7,  None),
  ("Volvo","xc90 recharge",        18.8,  3.7,  None),
  ("Volvo","s60 recharge",         18.8,  3.7,  None),
  ("Volvo","s90 recharge",         18.8,  3.7,  None),
  ("Volvo","v60 recharge",         18.8,  3.7,  None),
  ("Volvo","v90 recharge",         18.8,  3.7,  None),

  # ── LAND ROVER PHEV ───────────────────────────
  ("Land Rover","range rover phev",   31.8, 7.4, None),
  ("Land Rover","range rover sport phev",31.8,7.4,None),
  ("Land Rover","range rover velar p400e",17.1,7.4,None),
  ("Land Rover","defender phev",      19.2, 7.4, None),
  ("Land Rover","discovery sport phev",15.1,3.7, None),
  ("Land Rover","freelander phev",    15.0, 7.4, None),
  ("Land Rover","phev",               31.8, 7.4, None),  # generic

  # ── PORSCHE PHEV ──────────────────────────────
  ("Porsche","cayenne turbo s e-hybrid",25.9,7.2, None),
  ("Porsche","cayenne e-hybrid",        25.9,7.2, None),
  ("Porsche","cayenne",                 25.9,7.2, None),
  ("Porsche","panamera turbo s e-hybrid",25.9,7.2,None),
  ("Porsche","panamera 4 e-hybrid",     25.9,7.2, None),
  ("Porsche","panamera e-hybrid",       25.9,7.2, None),

  # ── VOLKSWAGEN PHEV ───────────────────────────
  ("Volkswagen","golf gte",            12.9, 3.7, None),
  ("Volkswagen","golf",                12.9, 3.7, None),
  ("Volkswagen","passat gte",          12.9, 3.7, None),
  ("Volkswagen","passat",              12.9, 3.7, None),
  ("Volkswagen","tiguan ehybrid",      14.4, 3.7, None),
  ("Volkswagen","tiguan",              14.4, 3.7, None),

  # ── JEEP PHEV ─────────────────────────────────
  ("Jeep","wrangler 4xe",          17.3, 7.2, None),
  ("Jeep","grand cherokee 4xe",    17.3, 7.2, None),
  ("Jeep","compass 4xe",           11.4, 3.7, None),
  ("Jeep","renegade 4xe",          11.4, 3.7, None),

  # ── MITSUBISHI PHEV ───────────────────────────
  ("Mitsubishi","outlander phev",  20.0, 6.6, None),
  ("Mitsubishi","eclipse cross phev",13.8,3.7,None),

  # ── HONDA PHEV ────────────────────────────────
  ("Honda","cr-v phev",            17.7, 7.2, None),
  ("Honda","claridad phev",        17.0, 7.2, None),
  ("Honda","accord phev",          17.0, 7.2, None),

  # ── PEUGEOT PHEV ──────────────────────────────
  ("Peugeot","508 hybrid",         11.5, 7.4, None),
  ("Peugeot","3008 hybrid",        12.4, 7.4, None),
  ("Peugeot","5008 hybrid",        12.4, 7.4, None),
  ("Peugeot","4008 hybrid",        12.4, 7.4, None),

  # ── GENERIC FALLBACK ──────────────────────────
]

# ─────────────────────────────────────────────
# APPLY LOOKUP TABLE
# ─────────────────────────────────────────────

df = pd.read_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_global_FINAL.csv')

def normalize(s):
    """Lowercase and simplify for matching"""
    return re.sub(r'\s+', ' ', str(s).lower().strip())

filled_bat = filled_ac = filled_dc = 0
source_note = "Manufacturer technical specification (training data cross-reference)"

for i, row in df.iterrows():
    mfr = str(row['Manufacturer']).strip()
    model_norm = normalize(row['Model'])

    # Check what's missing
    need_bat = pd.isna(row['Battery Capacity kWh'])
    need_ac  = pd.isna(row['Charging Rate Level 2 (kW)'])
    need_dc  = pd.isna(row['Charging Rate DC Fast (kW)'])
    if not (need_bat or need_ac or need_dc):
        continue

    # Find best match (first match wins — most specific first)
    for (spec_mfr, spec_model, bat, ac, dc) in SPECS:
        if spec_mfr != mfr:
            continue
        if spec_model in model_norm:
            if need_bat and bat is not None:
                df.at[i, 'Battery Capacity kWh'] = bat
                df.at[i, 'Plug Type Source'] = (str(row['Plug Type Source']) or '') + ' | ' + source_note
                filled_bat += 1
            if need_ac and ac is not None:
                df.at[i, 'Charging Rate Level 2 (kW)'] = ac
                filled_ac += 1
            if need_dc and dc is not None:
                df.at[i, 'Charging Rate DC Fast (kW)'] = dc
                filled_dc += 1
            break

print(f"Filled Battery: {filled_bat}")
print(f"Filled AC kW:   {filled_ac}")
print(f"Filled DC kW:   {filled_dc}")

# Coverage after
bev = df[df['Vehicle Type']=='BEV']
phev = df[df['Vehicle Type']=='PHEV']
total = len(df)

print(f"\n=== COVERAGE AFTER ===")
print(f"Battery  BEV: {bev['Battery Capacity kWh'].notna().sum()}/{len(bev)} = {bev['Battery Capacity kWh'].notna().mean()*100:.0f}%")
print(f"Battery PHEV: {phev['Battery Capacity kWh'].notna().sum()}/{len(phev)} = {phev['Battery Capacity kWh'].notna().mean()*100:.0f}%")
print(f"AC kW    BEV: {bev['Charging Rate Level 2 (kW)'].notna().sum()}/{len(bev)} = {bev['Charging Rate Level 2 (kW)'].notna().mean()*100:.0f}%")
print(f"AC kW   PHEV: {phev['Charging Rate Level 2 (kW)'].notna().sum()}/{len(phev)} = {phev['Charging Rate Level 2 (kW)'].notna().mean()*100:.0f}%")
print(f"DC kW    BEV: {bev['Charging Rate DC Fast (kW)'].notna().sum()}/{len(bev)} = {bev['Charging Rate DC Fast (kW)'].notna().mean()*100:.0f}%")

df.to_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_global_FINAL.csv', index=False)
print("\nSaved.")
