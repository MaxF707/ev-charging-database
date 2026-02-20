import pandas as pd
import re

df = pd.read_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_global_FINAL.csv')
df = df.sort_values(['Manufacturer','Region','Model Year'], ascending=[True,True,False])

def fmt_num(val):
    if pd.isna(val) or str(val).strip() in ('', '-', 'nan', 'None'):
        return '-'
    s = str(val).strip()
    m = re.match(r'(\d+(?:\.\d+)?)', s)
    if not m:
        return '-'
    f = float(m.group(1))
    return str(int(f)) if f == int(f) else f'{f:.1f}'

def fmt_autocharge(val):
    if pd.isna(val) or str(val).strip() in ('', '-', 'nan', 'None', 'Unbekannt'):
        return '?'
    s = str(val).lower()
    if s.startswith('ja'): return 'Y'
    if s.startswith('nein'): return 'N'
    if 'partial' in s or 'partiell' in s or 'teilweise' in s: return 'P'
    return '?'

lines = [
    '# EV CHARGING DATABASE — EU+US 2024/2025',
    '# Format: Region|Type|Model|Year|Battery(kWh)|AC_kW|DC_kW|Plug|Autocharge:Y/N/P/?|Emergency:…',
    "# Autocharge: Y=yes N=no P=partial ?=unknown | Type: BEV=Battery Electric PHEV=Plug-in Hybrid | '-'=data unavailable",
    ''
]

current_mfr = None
for _, row in df.iterrows():
    mfr = str(row['Manufacturer']).strip()
    if mfr != current_mfr:
        lines.append(f'## {mfr.upper()}')
        current_mfr = mfr
    
    region = str(row['Region']).strip()
    vtype  = str(row.get('Vehicle Type', 'BEV')).strip()
    model  = str(row['Model']).strip()
    year   = str(int(row['Model Year'])) if pd.notna(row['Model Year']) else '?'
    bat    = fmt_num(row['Battery Capacity kWh'])
    ac     = fmt_num(row['Charging Rate Level 2 (kW)'])
    dc     = fmt_num(row['Charging Rate DC Fast (kW)'])
    plug   = str(row['Plug Type']).strip() if pd.notna(row['Plug Type']) else '-'
    auto   = fmt_autocharge(row['Autocharge Support'])
    emerg  = str(row['Emergency Release Location']).strip() if pd.notna(row['Emergency Release Location']) else '-'

    bat_s = f'{bat}kWh' if bat != '-' else '-'
    ac_s  = f'AC:{ac}kW' if ac != '-' else 'AC:-'
    dc_s  = f'DC:{dc}kW' if dc != '-' else 'DC:-'

    lines.append(f'{region}|{vtype}|{model}|{year}|{bat_s}|{ac_s}|{dc_s}|{plug}|Autocharge:{auto}|Emergency:{emerg}')

content = '\n'.join(lines)
out = '/sessions/confident-cool-euler/mnt/Lemonflow/ev_charging_prompt_block.txt'
with open(out, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Lines: {len(lines)}')
print(f'Size: {len(content):,} chars (~{len(content)//4:,} tokens)')
