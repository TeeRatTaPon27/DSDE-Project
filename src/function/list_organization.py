import pandas as pd

df = pd.read_csv("dataset/df_clean_organization.csv")

# เอาเฉพาะคอลัมน์ organization
df['organization'] = df['organization'].fillna("ไม่ระบุ")

# ดึง unique + sorted
org_only = (
    df['organization']
    .dropna()
    .drop_duplicates()
    .sort_values()
    .reset_index(drop=True)
    .to_frame()
)

# export
org_only.to_csv("dataset/bkk_organization_unique.csv", index=False)

print("✔ Saved to dataset/bkk_organization_unique.csv")
