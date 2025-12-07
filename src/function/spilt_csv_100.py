import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'dataset', 'bangkok_traffy.csv')
# print(f"Reading data from: {input_path}

OUTPUT_NAME = "bangkok_traffy_100.csv"
OUTPUT_CSV = os.path.join(project_root, 'data-insight', OUTPUT_NAME)

# อ่านไฟล์ CSV
df = pd.read_csv(input_path)

# เลือก 100 แถวแรก
df_head = df.head(100)

# เขียนไฟล์ใหม่
df_head.to_csv(OUTPUT_CSV, index=False)

print("Export เสร็จแล้ว: bangkok_traffy_100.csv")

