import pandas as pd

# Load both datasets
global_df = pd.read_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_global_FINAL.csv')
phev_df = pd.read_csv('/sessions/confident-cool-euler/mnt/Lemonflow/eu_phev_clean.csv')

print(f"Global (existing): {len(global_df)} vehicles")
print(f"EU PHEVs: {len(phev_df)} vehicles")
print(f"Global columns: {list(global_df.columns)}")
print(f"PHEV columns: {list(phev_df.columns)}")

# Add Vehicle Type column to existing global dataset
global_df['Vehicle Type'] = 'BEV'

# Ensure phev_df has all same columns
# phev_df already has Vehicle Type = 'PHEV'
# Make sure column order matches
cols = list(global_df.columns)
print(f"Final columns: {cols}")

# Add any missing columns to phev_df
for col in cols:
    if col not in phev_df.columns:
        phev_df[col] = ''
        
# Reorder phev_df to match column order
phev_df = phev_df[cols]

# Concatenate
combined = pd.concat([global_df, phev_df], ignore_index=True)
print(f"Combined total: {len(combined)} vehicles")
print(f"Region breakdown:\n{combined['Region'].value_counts()}")
print(f"Vehicle Type breakdown:\n{combined['Vehicle Type'].value_counts()}")

# Save
combined.to_csv('/sessions/confident-cool-euler/mnt/Lemonflow/ev_global_FINAL.csv', index=False)
print("Saved ev_global_FINAL.csv")
