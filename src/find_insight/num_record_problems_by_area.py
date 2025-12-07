import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'dataset', 'bangkok_traffy.csv')
# print(f"Reading data from: {input_path}

OUTPUT_NAME = "problems_by_area.csv"
OUTPUT_CSV = os.path.join(project_root, 'data-insight', OUTPUT_NAME)

# อ่านไฟล์
df = pd.read_csv(input_path)

# ตรวจสอบชื่อ column ว่ามี subdistrict, district จริงไหม
print(df.columns)

# นับจำนวน record ต่อ district และ subdistrict
problem_counts = df.groupby(['district', 'subdistrict']).size().reset_index(name='num_problems')

# เรียงจากมากไปน้อย
problem_counts_sorted = problem_counts.sort_values(by='num_problems', ascending=False)

# แสดง top 10
print(problem_counts_sorted.head(10))

# เซฟเป็น CSV
problem_counts_sorted.to_csv(OUTPUT_CSV, index=False)
