import pandas as pd

# อ่านไฟล์ CSV
df = pd.read_csv("bangkok_traffy.csv")

# เลือก 100 แถวแรก
df_head = df.head(100)

# เขียนไฟล์ใหม่
df_head.to_csv("bangkok_traffy_100.csv", index=False)

print("Export เสร็จแล้ว: bangkok_traffy_100.csv")

