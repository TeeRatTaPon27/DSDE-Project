# -*- coding: utf-8 -*-
"""
ดึงจุด "organization locations" จริง ๆ ในกรุงเทพฯ จาก OpenStreetMap
ผ่าน Overpass API (ไม่ต้องใช้ API key)

ได้ข้อมูลจริง เช่น:
 - โรงเรียน
 - โรงพยาบาล
 - คลินิก
 - สถานีตำรวจ
 - สถานีดับเพลิง
 - ธนาคาร
 - สำนักงานเขต
 - ศูนย์ราชการ ฯลฯ

แล้วเซฟเป็น CSV:
  org_id, name, name_en, org_type, province, district, subdistrict,
  lat, lon, addr_full, source
"""

import uuid
import requests
import pandas as pd
import os

# -----------------------------
# 1) CONFIG
# -----------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# bounding box คร่าว ๆ รอบกรุงเทพ (ใต้,ซ้าย,เหนือ,ขวา)
#   (min_lat, min_lon, max_lat, max_lon)
BKK_BBOX = (13.5, 100.3, 13.95, 100.95)

# ประเภท amenity ที่อยากดึง (เลือกได้)
AMENITY_FILTER = [
    "school",
    "university",
    "college",
    "kindergarten",
    "hospital",
    "clinic",
    "doctors",
    "dentist",
    "pharmacy",
    "police",
    "fire_station",
    "bank",
    "atm",
    "library",
    "embassy",
    "townhall",
    "courthouse",
    "community_centre",
    "arts_centre",
    "theatre",
    "place_of_worship",
    "public_building",
    "social_facility",
    "bureau_de_change",
]

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

OUTPUT_NAME = "bkk_osm_organization_locations.csv"
OUTPUT_CSV = os.path.join(project_root, 'dataset', OUTPUT_NAME)

# -----------------------------
# 2) สร้าง Overpass Query
# -----------------------------

def build_overpass_query():
    min_lat, min_lon, max_lat, max_lon = BKK_BBOX

    # สร้าง filter ของ amenity เป็น OR
    amenity_part = "".join(
        f'  node["amenity"="{a}"]({min_lat},{min_lon},{max_lat},{max_lon});\n'
        for a in AMENITY_FILTER
    ) + "".join(
        f'  way["amenity"="{a}"]({min_lat},{min_lon},{max_lat},{max_lon});\n'
        for a in AMENITY_FILTER
    ) + "".join(
        f'  relation["amenity"="{a}"]({min_lat},{min_lon},{max_lat},{max_lon});\n'
        for a in AMENITY_FILTER
    )

    # out center; สำหรับ way / relation จะให้จุดกลาง (lat/lon) มา
    query = f"""
[out:json][timeout:90];
(
{amenity_part}
);
out center;
"""
    return query.strip()


# -----------------------------
# 3) เรียก Overpass API
# -----------------------------

def fetch_osm():
    query = build_overpass_query()
    print("📡 กำลังยิง Overpass API ...")

    r = requests.post(OVERPASS_URL, data={"data": query}, timeout=120)
    r.raise_for_status()
    js = r.json()

    elements = js.get("elements", [])
    print(f"✅ ได้ element ทั้งหมด: {len(elements)} จุด/โพลิกอน")
    return elements


# -----------------------------
# 4) แปลง OSM element -> row ในตาราง
# -----------------------------

def element_to_row(el):
    """
    el: dict หนึ่งตัวจาก 'elements' ของ OSM
    คืน dict หนึ่งแถวพร้อมข้อมูล lat/lon, name, address ฯลฯ
    """

    tags = el.get("tags", {}) or {}

    # 1) ชื่อ
    name = tags.get("name")
    name_en = tags.get("name:en")

    # 2) ประเภทองค์กร (ใช้ amenity เป็นหลัก)
    org_type = tags.get("amenity")

    # 3) lat/lon
    if el["type"] == "node":
        lat = el.get("lat")
        lon = el.get("lon")
    else:
        # way / relation -> ใช้ center.lat / center.lon
        center = el.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")

    # 4) address คร่าว ๆ (ถ้ามี)
    province = tags.get("addr:province") or "กรุงเทพมหานคร"
    district = tags.get("addr:district") or tags.get("addr:city")
    subdistrict = tags.get("addr:subdistrict")

    house = tags.get("addr:housenumber") or ""
    street = tags.get("addr:street") or ""
    postcode = tags.get("addr:postcode") or ""

    addr_parts = [house, street, subdistrict or "", district or "", province or "", postcode]
    addr_full = " ".join(p for p in addr_parts if p)

    return {
        "org_id": str(uuid.uuid4()),
        "name": name,
        "name_en": name_en,
        "org_type": org_type,
        "province": province,
        "district": district,
        "subdistrict": subdistrict,
        "lat": lat,
        "lon": lon,
        "addr_full": addr_full or None,
        "osm_id": el.get("id"),
        "osm_type": el.get("type"),
        "source": "OpenStreetMap+Overpass",
    }


# -----------------------------
# 5) main
# -----------------------------

def main():
    elements = fetch_osm()

    rows = []
    for el in elements:
        row = element_to_row(el)

        # ถ้าไม่มี lat/lon ข้ามไป
        if row["lat"] is None or row["lon"] is None:
            continue

        rows.append(row)

    df = pd.DataFrame(rows)
    print("\n📊 จำนวน record ที่ใช้งานได้ (มี lat/lon):", len(df))

    # อาจจะมีชื่อว่างบ้าง (บาง POI ไม่มี name ใน OSM) — แล้วแต่จะฟิลเตอร์ต่อ
    print("\nตัวอย่าง 5 แถวแรก:")
    print(df.head())

    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n💾 บันทึกไฟล์ {OUTPUT_CSV} เรียบร้อย!")


if __name__ == "__main__":
    main()
