import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tqdm import tqdm # ใช้สำหรับแสดง Progress Bar ระหว่าง Geocoding
import time
import os

# เปิดใช้งาน tqdm สำหรับ Pandas
tqdm.pandas() 

# ----------------------------------------------------
# 1. โหลดข้อมูล
# ----------------------------------------------------
# ชื่อไฟล์ CSV ของคุณ

# ชื่อไฟล์ผลลัพธ์
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_filename = os.path.join(project_root, 'dataset', 'bkk_organization_unique.csv')
# print(f"Reading data from: {input_path}

OUTPUT_NAME = "bkk_organization_with_coords.csv"
OUTPUT_CSV = os.path.join(project_root, 'data-insight', OUTPUT_NAME)

try:
    df = pd.read_csv(input_filename)
    print(f"✅ โหลดไฟล์ '{input_filename}' สำเร็จ. จำนวนองค์กร: {len(df):,}")
except FileNotFoundError:
    print(f"❌ Error: ไม่พบไฟล์ชื่อ '{input_filename}'")
    exit()


# ----------------------------------------------------
# 2. เตรียม Geocoder และ Rate Limiter
# ----------------------------------------------------
# Nominatim Usage Policy แนะนำให้หน่วงเวลาอย่างน้อย 1.5 วินาที ต่อการเรียกใช้
DELAY_SECONDS = 1.5 
USER_AGENT = "TeeRatTaPon27" # ตั้งชื่อ User Agent ที่ไม่ซ้ำใคร

geolocator = Nominatim(user_agent=USER_AGENT)

# กำหนด Rate Limiter เพื่อหน่วงเวลาการเรียกใช้ API อัตโนมัติ
geocode = RateLimiter(geolocator.geocode, 
                      min_delay_seconds=DELAY_SECONDS, 
                      error_wait_seconds=5) # หากเกิด Error ให้รอ 5 วินาทีแล้วลองใหม่

# ----------------------------------------------------
# 3. ฟังก์ชัน Geocoding
# ----------------------------------------------------
def get_lat_lon(organization_name):
    """
    ค้นหาพิกัด Lat/Lon จากชื่อองค์กร โดยจำกัดขอบเขตในกรุงเทพฯ
    """
    if pd.isna(organization_name) or organization_name == "":
        return None, None
    
    # เพิ่มขอบเขตการค้นหาเพื่อให้แม่นยำขึ้นในพื้นที่กรุงเทพฯ (Scoping)
    query = f"{organization_name}, Bangkok, Thailand"
    
    try:
        location = geocode(query)
        if location:
            # คืนค่า Latitude และ Longitude
            return location.latitude, location.longitude
        else:
            # คืนค่า None หากหาไม่พบ
            return None, None
    except Exception as e:
        # จัดการข้อผิดพลาดที่อาจเกิดขึ้น เช่น Connection Error หรือ Timeout
        print(f"\n⚠️ Error Geocoding '{organization_name}': {e}. Skipping...")
        return None, None

# ----------------------------------------------------
# 4. ประมวลผล Geocoding
# ----------------------------------------------------
print(f"\n⏳ เริ่มต้น Geocoding ({DELAY_SECONDS} วินาที/องค์กร). โปรดรอ...")

# ใช้ .progress_apply() เพื่อแสดงแถบความคืบหน้า
# .apply(lambda x: pd.Series(get_lat_lon(x))) คือการคืนค่าเป็น Series เพื่อใส่ใน 2 คอลัมน์พร้อมกัน
df[['lat', 'lon']] = df['organization'].progress_apply(
    lambda x: pd.Series(get_lat_lon(x))
)

# ----------------------------------------------------
# 5. บันทึกผลลัพธ์
# ----------------------------------------------------
# ตรวจสอบจำนวนพิกัดที่หาเจอ
valid_coords = df['lat'].notna().sum()

print("\n------------------------------------")
print("สรุปผลลัพธ์:")
print(f"จำนวนองค์กรทั้งหมด: {len(df):,}")
print(f"จำนวนพิกัดที่ค้นหาพบ: {valid_coords:,}")
print(f"จำนวนองค์กรที่หาพิกัดไม่พบ: {len(df) - valid_coords:,}")
print("------------------------------------")

df.to_csv(output_filename, index=False)
print(f"✅ บันทึกไฟล์ที่มีพิกัดแล้ว: '{output_filename}'")