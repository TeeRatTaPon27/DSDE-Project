import pandas as pd

# อ่าน CSV
df = pd.read_csv("bangkok_traffy.csv")

# สร้าง dict สำหรับนับ
type_counts = {}

for row in df['type'].dropna():  # ลบค่า NaN
    # ลบ {} แล้ว split ด้วย comma
    row = row.strip('{}')
    items = [item.strip() for item in row.split(',') if item.strip()]
    
    for item in items:
        if item in type_counts:
            type_counts[item] += 1
        else:
            type_counts[item] = 1

# แปลง dict เป็น DataFrame
result_df = pd.DataFrame(list(type_counts.items()), columns=['type', 'count'])

# เซฟเป็น CSV
result_df.to_csv("num_type2.csv", index=False)

print("Exported num_type2.csv")
