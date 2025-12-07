import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'dataset', 'bangkok_traffy.csv')
# print(f"Reading data from: {input_path}

OUTPUT_NAME = "num_province.csv"
OUTPUT_CSV = os.path.join(project_root, 'data-insight', OUTPUT_NAME)

# อ่านไฟล์ CSV
df = pd.read_csv(input_path)

# นับจำนวน unique record ต่อ province
province_counts = df.groupby('province').size().reset_index(name='count')

# เซฟเป็น CSV
province_counts.to_csv(OUTPUT_CSV, index=False)

print(province_counts.head())