import pandas as pd

# อ่านไฟล์
df = pd.read_csv("bangkok_traffy.csv")

# ตรวจสอบชื่อ column ว่ามี subdistrict, district จริงไหม
print(df.columns)

# นับจำนวน record ต่อ district และ subdistrict
problem_counts = df.groupby(['district', 'subdistrict']).size().reset_index(name='num_problems')

# เรียงจากมากไปน้อย
problem_counts_sorted = problem_counts.sort_values(by='num_problems', ascending=False)

# แสดง top 10
print(problem_counts_sorted.head(10))

# เซฟเป็น CSV
problem_counts_sorted.to_csv("problems_by_area.csv", index=False)
