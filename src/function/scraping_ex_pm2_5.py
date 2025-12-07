# -*- coding: utf-8 -*-
"""
ดึงข้อมูล PM2.5 จาก Open-Meteo Air Quality API
สำหรับ "ทุกแขวง" ใน BKK_CENTROIDS แล้วสรุปเป็น "รายวัน"
ตั้งแต่ 2023-01-01 ถึงวันนี้

เร่งความเร็วด้วย:
 - ใช้เฉพาะตัวแปร pm2_5 อย่างเดียว
 - ใช้ ThreadPoolExecutor เพื่อดึงหลายแขวงพร้อมกัน (ขนาน)
"""

import uuid
from datetime import date, timedelta
import concurrent.futures as futures

import requests
import pandas as pd
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
input_path = os.path.join(project_root, 'src', 'find_insight')
print(f"Reading data from: {input_path}")

sys.path.append(input_path)

from bkk_centroids import BKK_CENTROIDS

# -------------------------------------------------
# 1) CONFIG
# -------------------------------------------------

# ใช้ทุกแขวงที่มี lat/lon
ALL_POINTS = list(BKK_CENTROIDS)

# ช่วงวันที่: ตั้งแต่ 2023-01-01 ถึงวันนี้
START_DATE = date(2023, 1, 1)
END_DATE = date.today()

# ตัดช่วงวันที่เป็น block ละกี่วัน เวลาเรียก API
CHUNK_DAYS = 30

# จำนวน worker (thread) ที่จะเรียก API พร้อมกัน
# ถ้าเน็ต+API รับไหว ลอง 5–8 ได้ แต่ไม่ควรมากเกินไป
MAX_WORKERS = 5

# ชื่อไฟล์ผลลัพธ์
OUTPUT_NAME = "bkk_pm25_daily_2023_all_fast.csv"
OUTPUT_CSV = os.path.join(project_root, 'data-insight', OUTPUT_NAME)

# -------------------------------------------------
# 2) helper ตัดช่วงวันที่เป็น block เล็ก ๆ
# -------------------------------------------------

def iter_date_chunks(start_date: date, end_date: date, chunk_days: int = 30):
    """
    คืน (chunk_start, chunk_end) ทีละก้อน ก้อนละ chunk_days วัน
    เช่น 2023-01-01 → 2023-01-30, 2023-01-31 → ...
    """
    cur = start_date
    while cur <= end_date:
        c_end = min(cur + timedelta(days=chunk_days - 1), end_date)
        yield cur, c_end
        cur = c_end + timedelta(days=1)


# -------------------------------------------------
# 3) ฟังก์ชันเรียก Open-Meteo (เฉพาะ pm2_5, รายชั่วโมง)
# -------------------------------------------------

def fetch_pm25_hourly(lat, lon, sdate_str: str, edate_str: str):
    """
    เรียก Open-Meteo air-quality API คืน dict hourly:
        {
          "time": [...],
          "pm2_5": [...],
        }
    """
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": sdate_str,
        "end_date": edate_str,
        "timezone": "Asia/Bangkok",
        "hourly": ["pm2_5"],   # เอาแค่ PM2.5 ให้ payload เล็กลง
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json().get("hourly", {})


# -------------------------------------------------
# 4) worker: ดึงข้อมูลของ "แขวงเดียว" ทั้งช่วงเวลา
# -------------------------------------------------

def fetch_point_all_period(prov, dist, subdist, lat, lon):
    """
    ดึง PM2.5 รายชั่วโมงของแขวงเดียว (ทุกช่วง date block)
    แล้วคืน list ของ row (dict) ที่ยังเป็นรายชั่วโมง
    """
    if lat is None or lon is None:
        print(f"⚠ ข้ามแขวง{subdist} เขต{dist} เพราะ lat/lon เป็น None")
        return []

    print(f"\n📍 เริ่ม: แขวง{subdist} เขต{dist} ({lat}, {lon})")

    rows = []

    for c_start, c_end in iter_date_chunks(START_DATE, END_DATE, CHUNK_DAYS):
        sdate_str = c_start.strftime("%Y-%m-%d")
        edate_str = c_end.strftime("%Y-%m-%d")
        print(f"   - {subdist}: ดึงช่วง {sdate_str} → {edate_str}")

        try:
            hourly = fetch_pm25_hourly(lat, lon, sdate_str, edate_str)
        except Exception as e:
            print(f"   ❌ ERROR เรียก API ที่ช่วง {sdate_str}–{edate_str}: {e}")
            continue

        times = hourly.get("time", [])
        pm25 = hourly.get("pm2_5", [])

        for i in range(len(times)):
            rows.append({
                "province": prov,
                "district": dist,
                "subdistrict": subdist,
                "lat": lat,
                "lon": lon,
                "datetime": times[i],   # "YYYY-MM-DDTHH:00"
                "date": times[i][:10],  # "YYYY-MM-DD"
                "pm2_5": pm25[i],
            })

    print(f"   ✔ จบแขวง{subdist} ได้ {len(rows)} แถว (รายชั่วโมง)")
    return rows


# -------------------------------------------------
# 5) main: ใช้ ThreadPoolExecutor + รวม + สรุปรายวัน
# -------------------------------------------------

def main():
    print("===== BKK PM2.5 Daily (All Subdistricts, Fast) =====")
    print(f"ช่วงวันที่: {START_DATE} → {END_DATE}")
    print(f"จำนวนแขวงจาก BKK_CENTROIDS: {len(ALL_POINTS)} จุด\n")

    # กรองแขวงที่ lat/lon มีจริง
    valid_points = [
        (prov, dist, sub, lat, lon)
        for (prov, dist, sub, lat, lon) in ALL_POINTS
        if lat is not None and lon is not None
    ]
    print(f"ใช้แขวงที่มีพิกัดจริง: {len(valid_points)} จุด\n")

    all_hourly_rows = []

    # ใช้ thread pool ดึงหลายแขวงพร้อมกัน
    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_point = {}
        for p in valid_points:
            prov, dist, sub, lat, lon = p
            fut = executor.submit(fetch_point_all_period, prov, dist, sub, lat, lon)
            future_to_point[fut] = (prov, dist, sub)

        # รวมผลลัพธ์ทีละ future
        for fut in futures.as_completed(future_to_point):
            prov, dist, sub = future_to_point[fut]
            try:
                rows = fut.result()
                all_hourly_rows.extend(rows)
            except Exception as e:
                print(f"❌ ERROR ที่แขวง{sub} เขต{dist}: {e}")

    # ---------- แปลงเป็น DataFrame ----------
    df_hourly = pd.DataFrame(all_hourly_rows)
    print("\n📊 จำนวนแถวแบบรายชั่วโมงทั้งหมด:", len(df_hourly))

    if df_hourly.empty:
        print("❌ ไม่มีข้อมูลเลย ตรวจสอบการเรียก API / พิกัด อีกครั้ง")
        return

    # ---------- สรุปเป็น "รายวัน" ----------
    group_cols = ["province", "district", "subdistrict", "lat", "lon", "date"]

    df_daily = (
        df_hourly
        .groupby(group_cols, as_index=False)
        .agg({
            "pm2_5": "mean",
        })
    )

    # เพิ่ม aq_id (1 จุด+1วัน = 1 แถว)
    df_daily.insert(0, "aq_id", [str(uuid.uuid4()) for _ in range(len(df_daily))])

    print("📌 จำนวนแถวแบบ 'รายวัน':", len(df_daily))

    # ---------- เซฟ CSV ----------
    df_daily.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n💾 บันทึกไฟล์ {OUTPUT_CSV} เรียบร้อย!")


if __name__ == "__main__":
    main()
