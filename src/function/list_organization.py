import pandas as pd
import os

# ชื่อไฟล์ผลลัพธ์
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'dataset', 'df_clean_organization.csv')
# print(f"Reading data from: {input_path}

OUTPUT_NAME = "bkk_organization_unique.csv"
OUTPUT_CSV = os.path.join(project_root, 'dataset', OUTPUT_NAME)

df = pd.read_csv(input_path)

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
org_only.to_csv(OUTPUT_CSV, index=False)

print("✔ Saved to dataset/bkk_organization_unique.csv")
