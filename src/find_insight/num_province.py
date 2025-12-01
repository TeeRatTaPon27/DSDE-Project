import pandas as pd

# อ่านไฟล์ CSV
df = pd.read_csv("bangkok_traffy.csv")

# นับจำนวน unique record ต่อ province
province_counts = df.groupby('province').size().reset_index(name='count')

# เซฟเป็น CSV
province_counts.to_csv("num_province.csv", index=False)

print(province_counts.head())
