# import streamlit as st
# import pandas as pd
# import re

# # ---------------------------
# # Load Data
# # ---------------------------
# @st.cache_data
# def load_data():
#     df = pd.read_csv("dataset/df_clean.csv")

#     # Parse type {..}
#     def parse_type(value):
#         if pd.isna(value):
#             return []
#         value = str(value).replace("{", "").replace("}", "")
#         parts = re.split(r'\s*,\s*', value)
#         return [p.strip() for p in parts if p.strip()]

#     df["type_list"] = df["type"].apply(parse_type)
#     df_exploded = df.explode("type_list")
#     df_exploded.rename(columns={"type_list": "type_exploded"}, inplace=True)

#     # Extract lat/lon from coords "(13.77, 100.55)"
#     df_exploded[['lat', 'lon']] = (
#         df_exploded['coords']
#         .str.extract(r'\(?\s*([0-9\.\-]+)\s*,\s*([0-9\.\-]+)\s*\)?')
#         .astype(float)
#     )

#     df_exploded = df_exploded.dropna(
#         subset=["lat", "lon", "district", "subdistrict", "type_exploded"]
#     )

#     return df_exploded


# df = load_data()

# # ---------------------------
# # Sidebar Filter
# # ---------------------------
# st.sidebar.header("Filters")

# districts = ["ทั้งหมด"] + sorted(df["district"].unique())
# selected_district = st.sidebar.selectbox("เลือกเขต", districts)

# subdistricts = ["ทั้งหมด"] + sorted(df["subdistrict"].unique())
# selected_subdistrict = st.sidebar.selectbox("เลือกแขวง", subdistricts)

# types = sorted(df["type_exploded"].unique())
# selected_types = st.sidebar.multiselect("เลือกประเภทปัญหา", types)

# # ---------------------------
# # Filtering
# # ---------------------------
# df_filtered = df.copy()

# if selected_district != "ทั้งหมด":
#     df_filtered = df_filtered[df_filtered["district"] == selected_district]

# if selected_subdistrict != "ทั้งหมด":
#     df_filtered = df_filtered[df_filtered["subdistrict"] == selected_subdistrict]

# if selected_types:
#     df_filtered = df_filtered[df_filtered["type_exploded"].isin(selected_types)]

# # ---------------------------
# # Show Map
# # ---------------------------
# st.header("ตำแหน่งปัญหาบนแผนที่")

# if df_filtered.empty:
#     st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
# else:
#     st.map(df_filtered[["lat", "lon"]])


# # ---------------------------
# # Show Summary
# # ---------------------------
# st.header("จำนวนปัญหาจำแนกตามประเภท")

# st.bar_chart(df_filtered["type_exploded"].value_counts())
import streamlit as st
import pandas as pd
import re
import time

def prepare_map_data(df):
    progress = st.progress(0, text="กำลังเตรียมข้อมูลสำหรับแผนที่...")
    step = 0

    total_step = 5

    # 1) ตรวจคอลัมน์ lat/lon
    step += 1
    progress.progress(int(100 * step/total_step),
                      text=f"ตรวจสอบตำแหน่ง ... ({step}/{total_step})")
    time.sleep(0.1)

    # 2) ลบค่า NaN
    step += 1
    df = df.dropna(subset=["lat", "lon"])
    progress.progress(int(100 * step/total_step),
                      text=f"ล้างข้อมูล ... ({step}/{total_step})")
    time.sleep(0.1)

    # 3) Convert type
    step += 1
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    progress.progress(int(100 * step/total_step),
                      text=f"จัดรูปแบบ lat/lon ... ({step}/{total_step})")
    time.sleep(0.05)

    # 4) Limit number of points (optional) → ป้องกัน map ช้า
    step += 1
    if len(df) > 30000:  
        df = df.sample(30000)  # จำกัด 30k จุด
    progress.progress(int(100 * step/total_step),
                      text=f"ลดจำนวนจุดเพื่อประสิทธิภาพ ... ({step}/{total_step})")
    time.sleep(0.1)

    # 5) เสร็จสิ้น
    step += 1
    progress.progress(100, text="พร้อมแสดงแผนที่ ✓")
    time.sleep(0.1)

    return df

# ---------------------------
# Load Data with Progress Bar
# ---------------------------
@st.cache_data(show_spinner=False)
def load_data_with_progress():
    progress = st.progress(0, text="กำลังโหลดข้อมูล...")
    status = st.empty()

    # STEP 1: load CSV
    progress.progress(20, text="โหลด CSV ...")
    df = pd.read_csv("dataset/df_clean.csv")
    time.sleep(0.3)

    # STEP 2: parse type text
    progress.progress(40, text="ประมวลผล type ...")
    def parse_type(value):
        if pd.isna(value):
            return []
        value = str(value).replace("{", "").replace("}", "")
        parts = re.split(r'\s*,\s*', value)
        return [p.strip() for p in parts if p.strip()]
    df["type_list"] = df["type"].apply(parse_type)
    time.sleep(0.3)

    # STEP 3: explode rows
    progress.progress(60, text="แยกแถว (explode) ...")
    df_exploded = df.explode("type_list")
    df_exploded.rename(columns={"type_list": "type_exploded"}, inplace=True)

    # -----------------------
    # Clean type_exploded
    # -----------------------
    df_exploded['type_exploded'] = df_exploded['type_exploded'].astype(str) \
        .str.strip() \
        .str.replace(r"[\[\]']", "", regex=True)
    df_exploded = df_exploded[df_exploded['type_exploded'] != ""]

    time.sleep(0.3)

    # STEP 4: extract coords (แก้ลำดับให้ตรงจริง: lon, lat)
    progress.progress(80, text="ดึง lat/lon จาก coords ...")
    df_exploded['coords'] = df_exploded['coords'].astype(str)
    df_exploded[['lon', 'lat']] = df_exploded['coords'].str.extract(
        r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'
    ).astype(float)
    time.sleep(0.3)

    # STEP 5: drop missing
    progress.progress(100, text="ล้างข้อมูล ...")
    df_exploded = df_exploded.dropna(
        subset=["lat", "lon", "district", "subdistrict", "type_exploded"]
    )
    time.sleep(0.3)

    status.success("โหลดข้อมูลสำเร็จ!")

    return df_exploded


# ---------------------------
# Tabs
# ---------------------------
tab_load, tab_main = st.tabs(["📊 Loading Status", "📍 Dashboard"])

with tab_load:
    st.subheader("สถานะการโหลดข้อมูล")
    df = load_data_with_progress()
    st.success("ข้อมูลถูกโหลดและ cache แล้ว ✓")


# ---------------------------
# Dashboard (Main)
# ---------------------------
with tab_main:
    # Sidebar Filter
    st.sidebar.header("Filters")

    districts = ["ทั้งหมด"] + sorted(df["district"].unique())
    selected_district = st.sidebar.selectbox("เลือกเขต", districts)

    subdistricts = ["ทั้งหมด"] + sorted(df["subdistrict"].unique())
    selected_subdistrict = st.sidebar.selectbox("เลือกแขวง", subdistricts)

    types = sorted(df["type_exploded"].unique())
    selected_types = st.sidebar.multiselect("เลือกประเภทปัญหา", types)

    # Filtering
    df_filtered = df.copy()

    if selected_district != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered["district"] == selected_district]

    if selected_subdistrict != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered["subdistrict"] == selected_subdistrict]

    if selected_types:
        df_filtered = df_filtered[df_filtered["type_exploded"].isin(selected_types)]

    # Map
    st.header("ตำแหน่งปัญหาบนแผนที่")
    if df_filtered.empty:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    else:
        with st.spinner("กำลังสร้างแผนที่..."):
            df_map = prepare_map_data(df_filtered)
            st.write(df_map.head())
            st.write(df_map.describe())
            st.map(df_map[["lat","lon"]])

    # Bar Chart
    st.header("จำนวนปัญหาจำแนกตามประเภท")
    st.bar_chart(df_filtered["type_exploded"].value_counts())
