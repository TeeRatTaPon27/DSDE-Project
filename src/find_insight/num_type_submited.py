import pandas as pd

# อ่าน CSV
df = pd.read_csv("bangkok_traffy.csv")

# ตรวจว่ามี column 'type' หรือเปล่า
if 'type' not in df.columns:
    raise ValueError("ไม่มี column 'type' ในไฟล์ CSV")

# ลบค่า NaN ก่อนนับ
df['type'] = df['type'].dropna()

# นับจำนวน unique ของแต่ละ type
unique_counts = df['type'].value_counts().reset_index()
unique_counts.columns = ['type', 'count']

# เซฟเป็น CSV
unique_counts.to_csv("num_type.csv", index=False)

print("Exported num_type.csv")