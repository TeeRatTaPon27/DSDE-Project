import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'dataset', 'bangkok_traffy.csv')
# print(f"Reading data from: {input_path}

OUTPUT_NAME = "num_type.csv"
OUTPUT_CSV = os.path.join(project_root, 'data-insight', OUTPUT_NAME)

# อ่าน CSV
df = pd.read_csv(input_path)

# ตรวจว่ามี column 'type' หรือเปล่า
if 'type' not in df.columns:
    raise ValueError("ไม่มี column 'type' ในไฟล์ CSV")

# ลบค่า NaN ก่อนนับ
df['type'] = df['type'].dropna()

# นับจำนวน unique ของแต่ละ type
unique_counts = df['type'].value_counts().reset_index()
unique_counts.columns = ['type', 'count']

# เซฟเป็น CSV
unique_counts.to_csv(OUTPUT_CSV, index=False)

print("Exported num_type.csv")