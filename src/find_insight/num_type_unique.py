import pandas as pd

# อ่าน CSV
# df = pd.read_csv("bangkok_traffy.csv")
import os

# หาตำแหน่งปัจจุบันของไฟล์นี้ (src/find_insight/num_type_unique.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# ถอยหลัง 2 ชั้นเพื่อกลับไปที่ Project Root (find_insight -> src -> Project Root)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# สร้าง Path ไปยังไฟล์ input และ output ที่ต้องการ
# Input: อยู่ในโฟลเดอร์ dataset/
input_path = os.path.join(project_root, 'dataset', 'bangkok_traffy.csv')

# Output: อยากให้อยู่ในโฟลเดอร์ data-insight/ (ตามโครงสร้างใน README)
output_path = os.path.join(project_root, 'data-insight', 'num_type2.csv')
print(f"Reading data from: {input_path}")

# ---------------------------------------------------------
# 2. เริ่มทำงาน (Logic เดิม)
# ---------------------------------------------------------
try:
    df = pd.read_csv(input_path)

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

    # เซฟเป็น CSV ไปยังตำแหน่ง output ที่ถูกต้อง
    # ตรวจสอบว่ามีโฟลเดอร์ปลายทางไหม ถ้าไม่มีให้สร้าง
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    result_df.to_csv(output_path, index=False)

    print(f"✅ Exported successfully to: {output_path}")

except FileNotFoundError:
    print(f"❌ Error: ไม่พบไฟล์ข้อมูลที่ {input_path}")
    print("กรุณาตรวจสอบว่ามีไฟล์ 'bangkok_traffy.csv' อยู่ในโฟลเดอร์ 'dataset' ที่หน้าแรกของโปรเจคแล้ว")
