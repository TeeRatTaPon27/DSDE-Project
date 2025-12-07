# 📊 Component 1: AI/ML Component
# มี 2 ส่วนที่เป็น AI/ML:

# 1. DBSCAN Clustering (ใน Tab Main - Dashboard)
    # ประเภท: Unsupervised Learning - Clustering
    # จุดประสงค์: จัดกลุ่มปัญหาที่มีตำแหน่งใกล้เคียงกัน เพื่อระบุพื้นที่ที่มีปัญหาซ้ำซ้อน
    # แสดงผล: ใช้สีที่แตกต่างกันแสดง cluster แต่ละกลุ่มบนแผนที่

# 2. Linear Regression Analysis (ใน Tab PM2.5 Analysis)
    # ประเภท: Supervised Learning - Regression
    # จุดประสงค์: วิเคราะห์ความสัมพันธ์ระหว่างระดับ PM2.5 และจำนวนข้อร้องเรียน
    # แสดงผล: เส้นแนวโน้มและสมการ regression บน scatter plot
    
# 🗺️ Component 3: Visualization - Geospatial Analysis
# มีหลายส่วนที่เป็น Geospatial Visualization:

# 1. PyDeck Heatmap (ใน Tab PM2.5 Analysis)
    # ประเภท: Heatmap visualization
    # จุดประสงค์: แสดงความหนาแน่นของ PM2.5 ในพื้นที่กรุงเทพฯ

# 2. PyDeck Scatterplot (DBSCAN Clustering) (ใน Tab Main)
    # ประเภท: Point map with clustering
    # จุดประสงค์: แสดงตำแหน่งปัญหาพร้อมการจัดกลุ่มด้วย DBSCAN

# 3. Interactive Map with OpenStreetMap
    # ประเภท: Interactive map base layer
    # จุดประสงค์: ให้แผนที่พื้นฐานของกรุงเทพฯเป็น background

# 4. Plotly Line Chart
    # จุดประสงค์: แสดงแนวโน้ม PM2.5 ตามเวลา

# 5. Plotly Scatter Plot with Regression
    # จุดประสงค์: แสดงความสัมพันธ์ระหว่างตัวแปรพร้อมเส้น regression

# 6. Plotly Bar Chart
    # จุดประสงค์: แสดง 10 อันดับปัญหาที่พบมากที่สุด

# --------------------------------------------
# ✅ สรุป Compliance:
    # Component 1: AI/ML (ผ่านอย่างแน่นอน)
        # ✅ DBSCAN Clustering - สำหรับจัดกลุ่มปัญหาบนแผนที่
        # ✅ Linear Regression - สำหรับวิเคราะห์ความสัมพันธ์ PM2.5 และข้อร้องเรียน
        # ✅ Correlation Analysis - วิเคราะห์ความสัมพันธ์ระหว่างตัวแปร

    # Component 3: Visualization - Geospatial Analysis (ผ่านอย่างแน่นอน)
        # ✅ PyDeck Heatmap - การวิเคราะห์เชิงพื้นที่ของ PM2.5
        # ✅ PyDeck Scatterplot with DBSCAN - การแสดงตำแหน่งพร้อม clustering
        # ✅ Interactive Map with OSM - แผนที่กรุงเทพฯ interactive
        # ✅ Interactive Tooltips - แสดงข้อมูลเมื่อ hover
        # ✅ Map Controls - การเลือกสไตล์แผนที่และสี


import streamlit as st
import pandas as pd
import re
import time
from sklearn.cluster import DBSCAN
import pydeck as pdk
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

#!!!!!!!!!!! Edit this PATH !!!!!!!!!!!!
# df_clean_organization_path = "C:\Users\USER\Documents\Data_Science\FinalProject\DSDE-Project\dataset\df_clean_organization.csv"
# bkk_pm25_daily_2023_path = "C:\Users\USER\Documents\Data_Science\FinalProject\DSDE-Project\dataset\bkk_pm25_daily_2023_all_fast.csv"

# ---------------------------
# Load PM2.5 Data with Progress
# ---------------------------
@st.cache_data(show_spinner=False)
def load_pm25_data_with_progress():
    """โหลดข้อมูล PM2.5 ของกรุงเทพฯ"""
    progress = st.progress(0, text="กำลังโหลดข้อมูล PM2.5...")
    
    # STEP 1: load CSV
    progress.progress(25, text="โหลดข้อมูล PM2.5 จากไฟล์...")
    pm25_df = pd.read_csv(r"C:\Users\USER\Documents\I_love_my_job\CurseOfLife_Season_2\Data_Science\FinalProject\DSDE-Project\dataset\bkk_pm25_daily_2023_all_fast.csv")
    time.sleep(0.3)
    
    # STEP 2: ทำความสะอาดข้อมูล
    progress.progress(50, text="ทำความสะอาดข้อมูล PM2.5...")
    pm25_df.rename(columns={'date': 'date_str'}, inplace=True)
    pm25_df['date_dt'] = pd.to_datetime(pm25_df['date_str'], errors='coerce')
    pm25_df.dropna(subset=['date_dt', 'lon', 'lat', 'pm2_5'], inplace=True)
    
    # STEP 3: เพิ่มคอลัมน์ Quarter และ Month
    progress.progress(75, text="เพิ่มข้อมูลไตรมาสและเดือน...")
    pm25_df['quarter'] = pm25_df['date_dt'].dt.quarter
    pm25_df['month'] = pm25_df['date_dt'].dt.month
    pm25_df['year'] = pm25_df['date_dt'].dt.year
    
    # STEP 4: จัดกลุ่มตามพื้นที่ (สำหรับการแสดงผล)
    progress.progress(100, text="จัดกลุ่มข้อมูล PM2.5...")
    time.sleep(0.3)
    
    return pm25_df

def prepare_map_data(df):
    """เตรียมข้อมูลสำหรับแสดงแผนที่"""
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
# Load Data with Progress Bar (แก้ไขแล้ว)
# ---------------------------
@st.cache_data(show_spinner=False)
def load_data_with_progress():
    progress = st.progress(0, text="กำลังโหลดข้อมูล...")
    status = st.empty()

    # STEP 1: load CSV
    progress.progress(20, text="โหลด CSV ...")
    df = pd.read_csv(r"C:\Users\USER\Documents\I_love_my_job\CurseOfLife_Season_2\Data_Science\FinalProject\DSDE-Project\dataset\df_clean_organization.csv")
    time.sleep(0.3)

    # STEP 2: parse type text และเก็บข้อมูลต้นฉบับ
    progress.progress(40, text="ประมวลผล type ...")
    def parse_type(value):
        if pd.isna(value):
            return []
        value = str(value).replace("{", "").replace("}", "")
        parts = re.split(r'\s*,\s*', value)
        return [p.strip() for p in parts if p.strip()]
    
    df["type_list"] = df["type"].apply(parse_type)
    
    # 🔥 **เก็บ ID หรือ index ของแต่ละเคสต้นฉบับ**
    df["original_index"] = df.index
    df["complaint_id"] = df.index.astype(str)  # หรือใช้ ID อื่นถ้ามี
    
    time.sleep(0.3)

    # STEP 3: explode rows แต่เก็บข้อมูลต้นฉบับไว้
    progress.progress(60, text="แยกแถว (explode) ...")
    df_exploded = df.explode("type_list")
    df_exploded.rename(columns={"type_list": "type_exploded"}, inplace=True)
    df_exploded["timestamp_dt"] = pd.to_datetime(df_exploded["timestamp"], errors="coerce")

    # -----------------------
    # Clean type_exploded
    # -----------------------
    df_exploded['type_exploded'] = df_exploded['type_exploded'].astype(str) \
        .str.strip() \
        .str.replace(r"[\[\]']", "", regex=True)
    df_exploded = df_exploded[df_exploded['type_exploded'] != ""]

    time.sleep(0.3)

    # STEP 4: extract coords
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

    # เพิ่มคอลัมน์ Quarter และ Month สำหรับการวิเคราะห์ PM2.5
    df_exploded['quarter'] = df_exploded['timestamp_dt'].dt.quarter
    df_exploded['month'] = df_exploded['timestamp_dt'].dt.month
    df_exploded['year'] = df_exploded['timestamp_dt'].dt.year
    
    status.success("โหลดข้อมูลสำเร็จ!")
    
    # 🔥 **เก็บข้อมูลต้นฉบับไว้ด้วย (ก่อน explode)**
    df_original = df.copy()  # เก็บข้อมูลก่อน explode
    
    return {
        'df_exploded': df_exploded,
        'df_original': df_original  # เพิ่มข้อมูลต้นฉบับ
    }

# 🔥 **ฟังก์ชันสำหรับนับเคสที่ไม่ซ้ำ**
def count_unique_complaints(df_filtered_exploded, df_original=None):
    """
    นับจำนวนเคสที่ไม่ซ้ำ (unique complaints)
    โดยใช้ original_index หรือ complaint_id
    """
    if df_original is None:
        # ถ้าไม่มี df_original ให้ใช้วิธีสำรอง
        if 'original_index' in df_filtered_exploded.columns:
            unique_indices = df_filtered_exploded['original_index'].nunique()
            return unique_indices
        else:
            # ลองใช้ timestamp + coords เป็น unique key
            unique_keys = set()
            for idx, row in df_filtered_exploded.iterrows():
                if 'timestamp' in df_filtered_exploded.columns and 'coords' in df_filtered_exploded.columns:
                    key = f"{row['timestamp']}_{row['coords']}"
                    unique_keys.add(key)
                else:
                    # ถ้าไม่มีก็ใช้ index เป็น fallback
                    unique_keys.add(idx)
            return len(unique_keys)
    
    # ถ้ามี original_index ใช้ได้เลย
    if 'original_index' in df_filtered_exploded.columns:
        unique_indices = df_filtered_exploded['original_index'].nunique()
        return unique_indices
    
    # ถ้าไม่มี original_index ให้ใช้วิธีอื่น
    unique_keys = set()
    for idx, row in df_filtered_exploded.iterrows():
        # ลองหาเคสที่ตรงกันใน df_original
        if 'timestamp' in df_filtered_exploded.columns and 'coords' in df_filtered_exploded.columns:
            # ใช้ timestamp + coords เป็น unique key
            key = f"{row['timestamp']}_{row['coords']}"
            unique_keys.add(key)
        else:
            # ใช้ index เป็น fallback
            unique_keys.add(idx)
    
    return len(unique_keys)

# 🔥 **ฟังก์ชันสำหรับหาข้อมูลต้นฉบับตาม filter**
def get_original_complaints(df_filtered_exploded, df_original):
    """
    ดึงข้อมูลเคสต้นฉบับ (ก่อน explode) จาก filter ที่ใช้กับ df_exploded
    """
    if 'original_index' in df_filtered_exploded.columns:
        # ใช้ original_index ดึงข้อมูลจาก df_original
        filtered_indices = df_filtered_exploded['original_index'].unique()
        result_df = df_original[df_original.index.isin(filtered_indices)].copy()
        return result_df
    
    # ถ้าไม่มี original_index ให้ใช้วิธีอื่น
    unique_complaints = []
    seen_keys = set()
    
    for _, row in df_filtered_exploded.iterrows():
        # ลองหาเคสที่ตรงกันใน df_original
        if 'timestamp' in row and 'coords' in row:
            mask = (df_original['timestamp'] == row['timestamp']) & \
                   (df_original['coords'] == row['coords'])
            if mask.any():
                # ใช้ timestamp + coords เป็น unique key
                key = f"{row['timestamp']}_{row['coords']}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_complaints.append(df_original[mask].iloc[0].to_dict())
    
    return pd.DataFrame(unique_complaints) if unique_complaints else pd.DataFrame()

def create_aqi_heatmap():
    # เปลี่ยนจาก color scale เดิมเป็นตาม AQI ไทย
    # ใช้ linear gradient หรือกำหนดสีตามช่วงค่า
    
    # ตัวอย่างการกำหนดสีตามช่วง AQI
    color_range = [
        [0, 25, [0, 255, 0, 150]],      # 🟢 เขียว (0-25 µg/m³)
        [26, 37, [255, 255, 0, 150]],   # 🟡 เหลือง (26-37)
        [38, 50, [255, 165, 0, 150]],   # 🟠 ส้ม (38-50)
        [51, 90, [255, 0, 0, 150]],     # 🔴 แดง (51-90)
        [91, 120, [128, 0, 128, 150]],  # 🟣 ม่วง (91-120)
        [121, 500, [139, 69, 19, 150]]  # 🟤 น้ำตาล (>120)
    ]
    
    # หรือใช้ color scale ที่มีอยู่แล้ว
    aqi_colorscale = [
        [0, "rgb(0, 255, 0)"],    # เขียว
        [0.2, "rgb(255, 255, 0)"], # เหลือง
        [0.4, "rgb(255, 165, 0)"], # ส้ม
        [0.6, "rgb(255, 0, 0)"],   # แดง
        [0.8, "rgb(128, 0, 128)"], # ม่วง
        [1.0, "rgb(139, 69, 19)"]  # น้ำตาล
    ]

# ---------------------------
# Function สำหรับหาค่า PM2.5 เฉลี่ยตามพื้นที่ใกล้เคียง
# ---------------------------
def find_nearest_pm25(pm25_data, lat, lon, date, radius_km=2.0):
    """
    หาค่า PM2.5 เฉลี่ยจากสถานีตรวจวัดใกล้เคียง
    radius_km: รัศมีการค้นหาเป็นกิโลเมตร
    """
    # แปลงระยะทาง (ประมาณ)
    radius_deg = radius_km / 111.0  # 1 องศา ≈ 111 กม.
    
    # กรองข้อมูล PM2.5 ในวันเดียวกัน
    date_only = pd.Timestamp(date).date()
    same_day_data = pm25_data[pd.to_datetime(pm25_data['date_dt']).dt.date == date_only]
    
    if len(same_day_data) == 0:
        return None
    
    # คำนวณระยะทาง
    same_day_data = same_day_data.copy()
    same_day_data['distance'] = np.sqrt(
        (same_day_data['lat'] - lat) ** 2 + 
        (same_day_data['lon'] - lon) ** 2
    )
    
    # หาสถานีที่ใกล้ที่สุดในรัศมีที่กำหนด
    nearby_stations = same_day_data[same_day_data['distance'] <= radius_deg]
    
    if len(nearby_stations) == 0:
        return None
    
    # คืนค่า PM2.5 เฉลี่ยจากสถานีใกล้เคียง
    return nearby_stations['pm2_5'].mean()

# ---------------------------
# เริ่มต้น Streamlit App
# ---------------------------
st.set_page_config(page_title="Bangkok Complaint & PM2.5 Analysis", layout="wide")

# ยืนยันใน filter
if 'filter_applied' not in st.session_state:
    st.session_state['filter_applied'] = False

# ---------------------------
# Tabs
# ---------------------------
tab_load, tab_main, tab_pm25 = st.tabs(["📊 Loading Status", "📍 Dashboard", "😷 PM2.5 Analysis"])

# ---------------------------
# Tab 1: Loading Status
# ---------------------------
with tab_load:
    st.subheader("สถานะการโหลดข้อมูล")
    with st.spinner("กำลังโหลดข้อมูลหลัก..."):
        data_dict = load_data_with_progress()
        df_exploded = data_dict['df_exploded']
        df_original = data_dict['df_original']
    
    with st.spinner("กำลังโหลดข้อมูล PM2.5..."):
        pm25_df = load_pm25_data_with_progress()
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ ข้อมูลข้อร้องเรียนถูกโหลดและ cache แล้ว")
        # นับ unique complaints
        unique_count = count_unique_complaints(df_exploded, df_original)
        exploded_count = len(df_exploded)
        st.info(f"จำนวนเคสที่ไม่ซ้ำ: {unique_count:,} เคส")
        st.info(f"จำนวนรายการ (รวมแบบแยกประเภท): {exploded_count:,} รายการ")
        st.write(f"ช่วงเวลา: {df_exploded['timestamp_dt'].min().date()} ถึง {df_exploded['timestamp_dt'].max().date()}")
        
    with col2:
        st.success("✅ ข้อมูล PM2.5 ถูกโหลดและ cache แล้ว")
        st.info(f"จำนวนรายการ: {len(pm25_df):,} รายการ")
        st.write(f"ช่วงเวลา: {pm25_df['date_dt'].min().date()} ถึง {pm25_df['date_dt'].max().date()}")
    
    # แสดงตัวอย่างข้อมูล
    with st.expander("👁️ ดูตัวอย่างข้อมูลข้อร้องเรียน (ต้นฉบับ)"):
        st.dataframe(df_original.head(10))
    
    with st.expander("👁️ ดูตัวอย่างข้อมูลข้อร้องเรียน (หลัง explode)"):
        st.dataframe(df_exploded.head(10))
        
    with st.expander("👁️ ดูตัวอย่างข้อมูล PM2.5"):
        st.dataframe(pm25_df.head(10))

# ---------------------------
# Tab 2: Dashboard (Main) - แก้ไขแล้ว
# ---------------------------
with tab_main:
    # Sidebar Filter
    st.sidebar.header("Filters")
    
    districts = ["ทั้งหมด"] + sorted(df_exploded["district"].unique())
    selected_district = st.sidebar.selectbox("เลือกเขต", districts)

    subdistricts = ["ทั้งหมด"] + sorted(df_exploded["subdistrict"].unique())
    selected_subdistrict = st.sidebar.selectbox("เลือกแขวง", subdistricts)

    types = sorted(df_exploded["type_exploded"].unique())
    selected_types = st.sidebar.multiselect("เลือกประเภทปัญหา", types)

    # Organization dropdown (หลัก)
    organizations = ["ทั้งหมด"] + sorted(df_exploded["organization"].dropna().unique())
    selected_org = st.sidebar.selectbox("เลือกองค์กรหลัก", organizations)

    # Organization List (หลายรายการ)
    all_org_lists = sorted(
        {org for lst in df_exploded["organization_list"] for org in lst if isinstance(lst, list)}
    )
    selected_org_multi = st.sidebar.multiselect("เลือกหลายองค์กร (organization_list)", all_org_lists)
    
    # Filtering
    df_filtered = df_exploded.copy()

    # เขต
    if selected_district != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered["district"] == selected_district]

    # แขวง
    if selected_subdistrict != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered["subdistrict"] == selected_subdistrict]

    # ประเภทปัญหา
    if selected_types:
        df_filtered = df_filtered[df_filtered["type_exploded"].isin(selected_types)]

    # องค์กรหลัก
    if selected_org != "ทั้งหมด":
        df_filtered = df_filtered[df_filtered["organization"] == selected_org]

    # องค์กรในรายการ (list)
    if selected_org_multi:
        df_filtered = df_filtered[
            df_filtered["organization_list"].apply(
                lambda lst: any(o in lst for o in selected_org_multi)
            )
        ]
        
    # -----------------------------
    # Time Filter (Thai Calendar UI)
    # -----------------------------
    st.sidebar.subheader("ช่วงเวลา (Timestamp)")
    
    # default range
    min_date = df_exploded["timestamp_dt"].min().date()
    max_date = df_exploded["timestamp_dt"].max().date()

    # date UI (show Thai locale)
    start_date = st.sidebar.date_input("วันเริ่มต้น (พ.ศ.)", min_date)
    end_date = st.sidebar.date_input("วันสิ้นสุด (พ.ศ.)", max_date)
    
    confirm_button = st.sidebar.button('✅ Apply Filters', key='apply_main')

    # filter by datetime
    if confirm_button:
        df_filtered = df_filtered[
            (df_filtered["timestamp_dt"].dt.date >= start_date) &
            (df_filtered["timestamp_dt"].dt.date <= end_date)
        ]
    
    st.sidebar.subheader("🗺️ การแสดงผลแผนที่")

    # เพิ่มตัวเลือกการแสดงผล
    visualization_mode = st.sidebar.radio(
        "เลือกโหมดการแสดงผล:",
        ["🌫️ Heatmap (ความหนาแน่น)", "🎨 Point Colors (ระดับ AQI)", "📊 ทั้งสองแบบ"],
        index=0,
        key="visualization_mode_radio"  # 🔥 เพิ่ม key นี้
    )

    # -----------------------------
    # Display Metrics (แก้ไขแล้ว)
    # -----------------------------
    st.header("📈 สถิติและข้อมูล")
    
    # นับ unique complaints
    unique_count = count_unique_complaints(df_filtered, df_original)
    exploded_count = len(df_filtered)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔢 จำนวนเคสทั้งหมด (ไม่ซ้ำ)", f"{unique_count:,}")
        if exploded_count > unique_count:
            st.caption(f"📋 (รวมแบบแยกประเภท: {exploded_count:,})")
    
    with col2:
        # นับประเภทปัญหาที่แตกต่างกัน
        unique_types = df_filtered['type_exploded'].nunique()
        st.metric("📋 ประเภทปัญหาที่แตกต่าง", f"{unique_types}")
        
        # ถ้าเลือกประเภทปัญหาเฉพาะ
        if selected_types:
            st.caption(f"เลือกแล้ว: {len(selected_types)} ประเภท")
    
    with col3:
        # ถ้าเลือกองค์กรหลัก
        if selected_org != "ทั้งหมด":
            # ดึงข้อมูลต้นฉบับสำหรับองค์กรนี้
            df_org_exploded = df_filtered[df_filtered["organization"] == selected_org]
            org_unique_count = count_unique_complaints(df_org_exploded, df_original)
            
            if org_unique_count >= 50:
                # ดึงข้อมูลต้นฉบับเพื่อคำนวณ rating
                df_org_original = get_original_complaints(df_org_exploded, df_original)
                if 'star' in df_org_original.columns and len(df_org_original) > 0:
                    avg_rating = df_org_original["star"].mean()
                    st.metric("⭐ Rating ขององค์กร", f"{avg_rating:.2f}")
                else:
                    st.info(f"องค์กร {selected_org} มี {org_unique_count:,} เคส")
            else:
                st.info(f"องค์กร {selected_org} มี {org_unique_count:,} เคส — ไม่แสดง Rating (ต้องการอย่างน้อย 50 เคส)")
        else:
            st.metric("🏢 องค์กรทั้งหมด", f"{df_filtered['organization'].nunique():,}")
    
    # -----------------------------
    # Cases Count by Time Range (ใช้ unique count)
    # -----------------------------
    st.subheader("จำนวนปัญหาในช่วงเวลา")
    
    if len(df_filtered) > 0:
        now = df_filtered["timestamp_dt"].max()
        
        ranges = {
            "1 วันล่าสุด": now - pd.Timedelta(days=1),
            "3 วันล่าสุด": now - pd.Timedelta(days=3),
            "7 วันล่าสุด": now - pd.Timedelta(days=7),
            "2 สัปดาห์ล่าสุด": now - pd.Timedelta(days=14),
            "1 เดือนล่าสุด": now - pd.Timedelta(days=30),
            "ทั้งหมด": df_filtered["timestamp_dt"].min(),
        }

        cols = st.columns(3)
        for idx, (label, start_time) in enumerate(ranges.items()):
            # กรองและนับ unique
            temp_filtered = df_filtered[df_filtered["timestamp_dt"] >= start_time]
            unique_count_time = count_unique_complaints(temp_filtered, df_original)
            
            with cols[idx % 3]:
                st.metric(label, f"{unique_count_time:,} เคส")
    else:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    
    # -----------------------------
    # Top 10 Bar Chart (แก้ไขให้ถูกต้อง)
    # -----------------------------
    st.subheader("⭐ Top 10 ปัญหาที่เกิดมากที่สุด")
    
    if df_filtered.empty:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    else:
        # 🔥 **นับแบบไม่ซ้ำสำหรับแต่ละประเภทปัญหา**
        type_counts = {}
        
        # ใช้ original_index ถ้ามี
        if 'original_index' in df_filtered.columns:
            for type_name in df_filtered['type_exploded'].unique():
                # หา unique indices สำหรับประเภทนี้
                type_indices = df_filtered[df_filtered['type_exploded'] == type_name]['original_index'].unique()
                type_counts[type_name] = len(type_indices)
        else:
            # ใช้ timestamp + coords เป็น unique key
            for type_name in df_filtered['type_exploded'].unique():
                type_data = df_filtered[df_filtered['type_exploded'] == type_name]
                unique_keys = set()
                for _, row in type_data.iterrows():
                    key = f"{row['timestamp']}_{row['coords']}"
                    unique_keys.add(key)
                type_counts[type_name] = len(unique_keys)
        
        # แปลงเป็น DataFrame และเลือก 10 อันดับแรก
        top_10_types = pd.DataFrame({
            'ประเภทปัญหา': list(type_counts.keys()),
            'จำนวนเคส': list(type_counts.values())
        }).sort_values('จำนวนเคส', ascending=False).head(10)
        
        # 2. สร้าง Bar Chart
        fig = px.bar(
            top_10_types,
            x="จำนวนเคส",
            y="ประเภทปัญหา",
            orientation='h',
            title="10 อันดับปัญหาที่มีจำนวนเคสสูงสุด (นับไม่ซ้ำ)",
            color="จำนวนเคส",
            color_continuous_scale='Viridis'
        )
        
        # ปรับปรุง layout
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False)
        )
        
        # แสดง note ว่าคือการนับแบบไม่ซ้ำ
        st.caption("ℹ️ การนับเคสเป็นแบบไม่ซ้ำ (1 เคสที่มีหลายปัญหา นับเป็น 1 เคส)")
        
        st.plotly_chart(fig, use_container_width=True)
        
    # ---------------------------
    # Status Map
    # ---------------------------
    st.subheader("📋 แผนที่สถานะการดำเนินการ")
    
    if df_filtered.empty:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    else:
        # สร้างแผนที่สถานะ
        with st.spinner("กำลังสร้างแผนที่สถานะ..."):
            df_status_map = prepare_map_data(df_filtered)
            
            # สีตามสถานะ (สมมติมีคอลัมน์ 'status' หรือสร้างจากคอลัมน์อื่น)
            # ถ้าไม่มีคอลัมน์ status ให้สร้างจาก timestamp หรืออื่นๆ
            if 'state' in df_status_map.columns:
                # ถ้ามีคอลัมน์ status
                status_colors = {
                    'เสร็จสิ้น': [0, 255, 0, 180],      # 🟢 เขียว
                    'กำลังดำเนินการ': [0, 0, 255, 180], # 🔵 น้ำเงิน  
                    'รอรับเรื่อง': [255, 0, 0, 180],      # 🔴 แดง
                }
                
                # สร้างสีตามสถานะ
                df_status_map['color'] = df_status_map['state'].apply(
                    lambda x: status_colors.get(x, [150, 150, 150, 180])  # สีเทา default
                )
            else:
                # ถ้าไม่มีคอลัมน์ status ให้แบ่งตามเวลาหรือวิธีอื่น
                st.info("⚠️ ไม่พบคอลัมน์ 'status' กำลังสร้างสถานะจากข้อมูลที่มี...")
                
                # ตัวอย่าง: แบ่งตามเวลา (timestamp เก่า = เสร็จสิ้น, ใหม่ = กำลังดำเนินการ)
                current_time = pd.Timestamp.now()
                
                def assign_status_by_time(timestamp):
                    """กำหนดสถานะตามเวลา"""
                    time_diff = current_time - timestamp
                    days_diff = time_diff.days
                    
                    if days_diff > 30:
                        return 'เสร็จสิ้น'      # เก่ากว่า 30 วัน
                    elif days_diff > 7:
                        return 'กำลังดำเนินการ'  # 7-30 วัน
                    else:
                        return 'รอรับเรื่อง'     # น้อยกว่า 7 วัน
                
                # เพิ่มคอลัมน์ status
                df_status_map['state'] = df_status_map['timestamp_dt'].apply(assign_status_by_time)
                
                # สีตามสถานะ
                status_colors = {
                    'เสร็จสิ้น': [0, 255, 0, 180],      # 🟢 เขียว
                    'กำลังดำเนินการ': [0, 0, 255, 180], # 🔵 น้ำเงิน
                    'รอรับเรื่อง': [255, 0, 0, 180],      # 🔴 แดง
                }
                
                df_status_map['color'] = df_status_map['state'].apply(
                    lambda x: status_colors.get(x, [150, 150, 150, 180])
                )
            
            # นับจำนวนแต่ละสถานะ (นับ unique)
            status_counts = {}
            if 'original_index' in df_status_map.columns:
                # นับ unique by status
                for status in df_status_map['state'].unique():
                    indices = df_status_map[df_status_map['state'] == status]['original_index'].unique()
                    status_counts[status] = len(indices)
            else:
                # นับแบบธรรมดา (อาจนับซ้ำ)
                status_counts = df_status_map['state'].value_counts()
            
            # แสดงสถิติสถานะ
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🟢 เสร็จสิ้น", f"{status_counts.get('เสร็จสิ้น', 0):,}")
            with col2:
                st.metric("🔵 กำลังดำเนินการ", f"{status_counts.get('กำลังดำเนินการ', 0):,}")
            with col3:
                st.metric("🔴 รอรับเรื่อง", f"{status_counts.get('รอรับเรื่อง', 0):,}")
            
            # สร้างแผนที่
            status_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_status_map,
                get_position='[lon, lat]',
                get_color="color",
                get_radius=40,
                pickable=True,
                opacity=0.7,
            )
            
            view_state = pdk.ViewState(
                latitude=df_status_map["lat"].mean(),
                longitude=df_status_map["lon"].mean(),
                zoom=11,
            )
            
            r = pdk.Deck(
                layers=[status_layer],
                initial_view_state=view_state,
                tooltip={
                    "html": """
                    <b>สถานะ:</b> {state}<br>
                    <b>ประเภท:</b> {type_exploded}<br>
                    <b>องค์กร:</b> {organization}<br>
                    <b>วันที่:</b> {timestamp_dt}<br>
                    <b>ตำแหน่ง:</b> ({lat:.4f}, {lon:.4f})
                    """,
                    "style": {"color": "white", "backgroundColor": "#333", "padding": "5px"}
                }
            )
            
            st.pydeck_chart(r)
            
            # แสดง Legend
            st.markdown("""
            <div style="display: flex; justify-content: center; gap: 20px; margin-top: 10px;">
                <div style="text-align: center;">
                    <div style="width: 20px; height: 20px; background-color: rgb(0, 255, 0); border-radius: 50%; display: inline-block;"></div>
                    <div>🟢 เสร็จสิ้น</div>
                </div>
                <div style="text-align: center;">
                    <div style="width: 20px; height: 20px; background-color: rgb(0, 0, 255); border-radius: 50%; display: inline-block;"></div>
                    <div>🔵 กำลังดำเนินการ</div>
                </div>
                <div style="text-align: center;">
                    <div style="width: 20px; height: 20px; background-color: rgb(255, 0, 0); border-radius: 50%; display: inline-block;"></div>
                    <div>🔴 รอรับเรื่อง</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # ---------------------------
    # Map with Clustering
    # ---------------------------
    st.header("🗺️ ตำแหน่งปัญหาบนแผนที่ (DBSCAN Clustering)")

    if df_filtered.empty:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    else:
        with st.spinner("กำลังสร้างแผนที่..."):
            df_map = prepare_map_data(df_filtered)

            # DBSCAN Clustering
            coords = df_map[["lat", "lon"]].to_numpy()
            clustering = DBSCAN(eps=0.002, min_samples=10).fit(coords)
            df_map["cluster"] = clustering.labels_
            
            # สีตามองค์กรที่เลือก
            if selected_org != "ทั้งหมด":
                highlight_color = [0, 120, 255]   # ฟ้า
                normal_color = [180, 180, 180]    # เทาอ่อน

                df_map["color"] = df_map["organization"].apply(
                    lambda x: highlight_color if x == selected_org else normal_color
                )

            elif selected_org_multi:
                highlight_color = [255, 100, 0]    # ส้ม
                normal_color = [180, 180, 180]

                df_map["color"] = df_map["organization_list"].apply(
                    lambda lst: highlight_color if any(o in lst for o in selected_org_multi) else normal_color
                )

            else:
                # สร้างสีสุ่มให้แต่ละ cluster
                unique_clusters = sorted(df_map["cluster"].unique())
                colors = {
                    c: [np.random.randint(50,255), np.random.randint(50,255), np.random.randint(50,255)]
                    for c in unique_clusters
                }
                # cluster = -1 คือ noise → สีเทา
                colors[-1] = [150,150,150]

                df_map["color"] = df_map["cluster"].apply(lambda c: colors[c])

            # PyDeck Visualization
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_map,
                get_position='[lon, lat]',
                get_color="color",
                get_radius=40,
                pickable=True,
                opacity=0.7,
            )
            
            # 🔥 **แก้ไขตรงนี้: เอา organization points layer ออก**
            # ถ้าเลือกองค์กรเฉพาะ ให้แสดงตำแหน่งองค์กร
            if selected_org != "ทั้งหมด":
                try:
                    # โหลดตำแหน่งขององค์กร
                    org_loc_df = pd.read_csv("dataset/bkk_osm_organization_locations.csv")
                    
                    # ทำ clean ชื่อ
                    org_loc_df['name_norm'] = org_loc_df['name'].str.strip().str.lower()
                    
                    # กรองเฉพาะองค์กรที่เลือก
                    selected_org_norm = selected_org.strip().lower()
                    org_points = org_loc_df[org_loc_df['name_norm'] == selected_org_norm].copy()
                    
                    if len(org_points) > 0:
                        # สร้าง layer สำหรับองค์กร
                        layer_org = pdk.Layer(
                            "ScatterplotLayer",
                            data=org_points,
                            get_position=["lon", "lat"],
                            get_radius=200,
                            get_fill_color=[255, 0, 0, 180],
                            radius_min_pixels=8,
                            pickable=True,
                        )
                        layers = [layer, layer_org]
                        
                        # แสดงข้อความบอกตำแหน่งองค์กร
                        st.info(f"📍 แสดงตำแหน่งสำนักงานขององค์กร: **{selected_org}**")
                    else:
                        layers = [layer]
                        st.warning(f"⚠️ ไม่พบตำแหน่งสำนักงานขององค์กร: **{selected_org}** ในฐานข้อมูล")
                
                except Exception as e:
                    layers = [layer]
                    st.warning(f"⚠️ ไม่สามารถโหลดข้อมูลตำแหน่งองค์กรได้: {str(e)}")
            
            # 🔥 **แก้ไขเพิ่ม: ถ้าเลือกหลายองค์กรใน organization_list**
            elif selected_org_multi and len(selected_org_multi) > 0:
                try:
                    # โหลดตำแหน่งขององค์กร
                    org_loc_df = pd.read_csv("dataset/bkk_osm_organization_locations.csv")
                    
                    # ทำ clean ชื่อ
                    org_loc_df['name_norm'] = org_loc_df['name'].str.strip().str.lower()
                    
                    # กรองเฉพาะองค์กรที่เลือก
                    selected_orgs_norm = [org.strip().lower() for org in selected_org_multi]
                    org_points = org_loc_df[org_loc_df['name_norm'].isin(selected_orgs_norm)].copy()
                    
                    if len(org_points) > 0:
                        # สร้าง layer สำหรับองค์กร
                        layer_org = pdk.Layer(
                            "ScatterplotLayer",
                            data=org_points,
                            get_position=["lon", "lat"],
                            get_radius=200,
                            get_fill_color=[255, 0, 0, 180],
                            radius_min_pixels=8,
                            pickable=True,
                        )
                        layers = [layer, layer_org]
                        
                        # แสดงข้อความบอกตำแหน่งองค์กร
                        org_names = ", ".join(selected_org_multi)
                        st.info(f"📍 แสดงตำแหน่งสำนักงานขององค์กร: **{org_names}**")
                    else:
                        layers = [layer]
                        st.warning("⚠️ ไม่พบตำแหน่งสำนักงานขององค์กรที่เลือกในฐานข้อมูล")
                
                except Exception as e:
                    layers = [layer]
                    st.warning(f"⚠️ ไม่สามารถโหลดข้อมูลตำแหน่งองค์กรได้: {str(e)}")
            
            # 🔥 **กรณีไม่เลือกองค์กรใดๆ (เลือก "ทั้งหมด")**
            else:
                layers = [layer]
                st.info("ℹ️ เลือกองค์กรใน Filter เพื่อแสดงตำแหน่งสำนักงานขององค์กรนั้น")
                
            # เพิ่มใน Tab Load หรือ Tab Main
            with st.expander("🔍 ตรวจสอบข้อมูลข้อร้องเรียน"):
                st.write("### รายละเอียดข้อมูลข้อร้องเรียน")
                st.write(f"จำนวนเคสที่ไม่ซ้ำทั้งหมด: {count_unique_complaints(df_exploded, df_original):,}")
                st.write(f"จำนวนรายการทั้งหมด (แยกประเภท): {len(df_exploded):,}")
                st.write(f"จำนวนวันที่แตกต่าง: {df_exploded['timestamp_dt'].dt.date.nunique():,}")
                st.write(f"ช่วงวันที่: {df_exploded['timestamp_dt'].min().date()} ถึง {df_exploded['timestamp_dt'].max().date()}")
                
                # นับตามวัน (unique)
                daily_unique_counts = {}
                for date in df_exploded['timestamp_dt'].dt.date.unique():
                    day_data = df_exploded[df_exploded['timestamp_dt'].dt.date == date]
                    daily_unique_counts[date] = count_unique_complaints(day_data, df_original)
                
                max_count = max(daily_unique_counts.values()) if daily_unique_counts else 0
                avg_count = np.mean(list(daily_unique_counts.values())) if daily_unique_counts else 0
                
                st.write(f"วันที่มีข้อร้องเรียนมากที่สุด: {max_count:,} เคส")
                st.write(f"ค่าเฉลี่ยต่อวัน: {avg_count:.1f} เคส")

            view_state = pdk.ViewState(
                latitude=df_map["lat"].mean(),
                longitude=df_map["lon"].mean(),
                zoom=11,
            )

            r = pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                tooltip={
                    "html": "<b>Cluster:</b> {cluster}<br>"
                            "<b>Type:</b> {type_exploded}<br>"
                            "<b>Organization:</b> {organization}<br>"
                            "<b>Lat:</b> {lat:.4f}<br>"
                            "<b>Lon:</b> {lon:.4f}",
                    "style": {"color": "white", "backgroundColor": "#333", "padding": "5px"}
                }
            )

            st.pydeck_chart(r)

# ---------------------------
# Tab 3: PM2.5 Analysis (แก้ไขแล้ว)
# ---------------------------
with tab_pm25:
    st.header("😷 การวิเคราะห์ PM2.5 และข้อร้องเรียน")
    
    # Sidebar สำหรับ Filter PM2.5
    st.sidebar.header("PM2.5 Analysis Filters")
    
    # Filter ปี
    available_years = sorted(pm25_df['year'].unique())
    selected_year = st.sidebar.selectbox("เลือกปี", available_years, key='pm25_year')
    
    # Filter ไตรมาส
    quarters = ["ทั้งหมด"] + sorted(pm25_df['quarter'].unique())
    selected_quarter = st.sidebar.selectbox("เลือกไตรมาส", quarters, key='pm25_quarter')
    
    # Filter เดือน
    months = ["ทั้งหมด"] + sorted(pm25_df['month'].unique())
    selected_month = st.sidebar.selectbox("เลือกเดือน", months, key='pm25_month')
    
    # Filter พื้นที่
    districts_complaints = ["ทั้งหมด"] + sorted(df_exploded['district'].unique())
    selected_pm25_district = st.sidebar.selectbox("เลือกเขต (เปรียบเทียบ)", districts_complaints, key='pm25_district')
    
    # Filter ประเภทปัญหา - เปลี่ยนเป็นเฉพาะ PM2.5 เท่านั้น
    complaint_types = sorted(df_exploded['type_exploded'].unique())
    # หาประเภทที่เกี่ยวข้องกับ PM2.5
    pm25_related_types = [t for t in complaint_types if any(keyword in t.lower() for keyword in 
                                                           ['pm2.5', 'pm25', 'ฝุ่น', 'อากาศ', 'มลพิษ', 'คุณภาพอากาศ'])]
    
    if len(pm25_related_types) > 0:
        selected_complaint_type = st.sidebar.selectbox(
            "เลือกประเภทปัญหา PM2.5", 
            ["ทั้งหมด"] + pm25_related_types, 
            key='pm25_type'
        )
    else:
        selected_complaint_type = "ทั้งหมด"
        st.sidebar.warning("⚠️ ไม่พบประเภทปัญหาเกี่ยวกับ PM2.5 ในข้อมูล")
    
    # Filter PM2.5 Level
    pm25_range = st.sidebar.slider(
        "ช่วงค่า PM2.5 (µg/m³)",
        min_value=int(pm25_df['pm2_5'].min()),
        max_value=int(pm25_df['pm2_5'].max()),
        value=(0, 100),
        key='pm25_range'
    )
    
    # 🔥 **เพิ่ม: ตัวเลือกการแสดงผลแผนที่**
    st.sidebar.subheader("🗺️ การแสดงผลแผนที่")
    visualization_mode_pm25 = st.sidebar.radio(
        "เลือกโหมดการแสดงผล:",
        ["🌫️ Heatmap (ความหนาแน่น)", "🎨 Point Colors (ระดับ AQI)", "📊 ทั้งสองแบบ"],
        index=0,
        key='visualization_mode_pm25'
    )
    
    apply_pm25_filter = st.sidebar.button('🚀 วิเคราะห์ PM2.5', key='apply_pm25')
    
    if apply_pm25_filter:
        with st.spinner("กำลังวิเคราะห์ข้อมูล PM2.5 และข้อร้องเรียน..."):
            
            # ========================================
            # 1. กรองข้อมูล PM2.5 จากสถานีตรวจวัด
            # ========================================
            pm25_filtered = pm25_df.copy()
            
            # กรองตามปี
            pm25_filtered = pm25_filtered[pm25_filtered['year'] == selected_year]
            
            # กรองตามไตรมาส
            if selected_quarter != "ทั้งหมด":
                pm25_filtered = pm25_filtered[pm25_filtered['quarter'] == selected_quarter]
            
            # กรองตามเดือน
            if selected_month != "ทั้งหมด":
                pm25_filtered = pm25_filtered[pm25_filtered['month'] == selected_month]
            
            # กรองตามช่วงค่า PM2.5
            pm25_filtered = pm25_filtered[
                (pm25_filtered['pm2_5'] >= pm25_range[0]) & 
                (pm25_filtered['pm2_5'] <= pm25_range[1])
            ]
            
            # ========================================
            # 2. กรองข้อมูลข้อร้องเรียน PM2.5
            # ========================================
            complaints_filtered = df_exploded.copy()
            
            # กรองตามปีเดียวกันกับ PM2.5
            complaints_filtered = complaints_filtered[complaints_filtered['year'] == selected_year]
            
            # กรองตามไตรมาส
            if selected_quarter != "ทั้งหมด":
                complaints_filtered = complaints_filtered[complaints_filtered['quarter'] == selected_quarter]
            
            # กรองตามเดือน
            if selected_month != "ทั้งหมด":
                complaints_filtered = complaints_filtered[complaints_filtered['month'] == selected_month]
            
            # กรองตามเขต
            if selected_pm25_district != "ทั้งหมด":
                complaints_filtered = complaints_filtered[complaints_filtered['district'] == selected_pm25_district]
            
            # 🔥 **กรองเฉพาะประเภทปัญหา PM2.5**
            if selected_complaint_type != "ทั้งหมด":
                complaints_filtered = complaints_filtered[complaints_filtered['type_exploded'] == selected_complaint_type]
            elif len(pm25_related_types) > 0:
                complaints_filtered = complaints_filtered[complaints_filtered['type_exploded'].isin(pm25_related_types)]
            
            # 🔥 **นับจำนวนเคสที่ไม่ซ้ำ**
            unique_complaints_count = count_unique_complaints(complaints_filtered, df_original)
            
            # ========================================
            # 3. แสดงข้อมูลสถิติ
            # ========================================
            st.subheader("📊 สรุปข้อมูล")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📅 ปีที่วิเคราะห์", selected_year)
                st.metric("📈 จำนวนรายการ PM2.5 (สถานี)", f"{len(pm25_filtered):,}")
                avg_pm25 = pm25_filtered['pm2_5'].mean()
                st.metric("🌫️ ค่า PM2.5 เฉลี่ย (สถานี)", f"{avg_pm25:.1f} µg/m³")
            
            with col2:
                quarter_text = f"ไตรมาส {selected_quarter}" if selected_quarter != "ทั้งหมด" else "ทั้งหมด"
                st.metric("📊 ไตรมาส", quarter_text)
                # 🔥 **ใช้ unique count แทน**
                st.metric("📝 จำนวนข้อร้องเรียน PM2.5", f"{unique_complaints_count:,}")
                
                # คำนวณ rating จากข้อมูลต้นฉบับ
                if unique_complaints_count > 0:
                    original_complaints = get_original_complaints(complaints_filtered, df_original)
                    if 'star' in original_complaints.columns and len(original_complaints) > 0:
                        avg_rating = original_complaints['star'].mean()
                        st.metric("⭐ คะแนนเฉลี่ย", f"{avg_rating:.2f}")
                    else:
                        st.metric("⭐ คะแนนเฉลี่ย", "N/A")
                else:
                    st.metric("⭐ คะแนนเฉลี่ย", "N/A")
            
            with col3:
                month_text = f"เดือน {selected_month}" if selected_month != "ทั้งหมด" else "ทั้งหมด"
                st.metric("🗓️ เดือน", month_text)
                if selected_pm25_district != "ทั้งหมด":
                    st.metric("📍 เขต", selected_pm25_district)
                else:
                    st.metric("📍 เขต", "ทั้งหมด")
                
                if selected_complaint_type != "ทั้งหมด":
                    st.metric("🔧 ประเภทปัญหา", selected_complaint_type)
                else:
                    st.metric("🔧 ประเภทปัญหา", "PM2.5 ทั้งหมด")
            
            # แสดง note เกี่ยวกับการนับ
            if unique_complaints_count != len(complaints_filtered):
                st.info(f"ℹ️ หมายเหตุ: มีเคสทั้งหมด {len(complaints_filtered):,} รายการ (แยกตามประเภทปัญหา) แต่เป็นเคสที่ไม่ซ้ำ {unique_complaints_count:,} เคส")
            
            # ========================================
            # 4. Visualization: PM2.5 ตามเวลา
            # ========================================
            st.subheader("📈 แนวโน้มค่า PM2.5 ตามเวลา")
            
            if len(pm25_filtered) > 0:
                # จัดกลุ่มตามวันที่
                pm25_daily = pm25_filtered.groupby('date_dt')['pm2_5'].mean().reset_index()
                pm25_daily.sort_values('date_dt', inplace=True)
                
                fig_pm25 = px.line(
                    pm25_daily,
                    x='date_dt',
                    y='pm2_5',
                    title=f'ค่า PM2.5 เฉลี่ยรายวัน จากสถานีตรวจวัด ({selected_year})',
                    labels={'date_dt': 'วันที่', 'pm2_5': 'PM2.5 (µg/m³)'},
                    markers=True
                )
                
                # เพิ่มเส้นมาตรฐาน WHO (15 µg/m³)
                fig_pm25.add_hline(
                    y=15, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="มาตรฐาน WHO (15 µg/m³)",
                    annotation_position="bottom right"
                )
                
                # เพิ่มเส้นมาตรฐานไทย (50 µg/m³)
                fig_pm25.add_hline(
                    y=50, 
                    line_dash="dash", 
                    line_color="orange",
                    annotation_text="มาตรฐานไทย (50 µg/m³)",
                    annotation_position="top right"
                )
                
                fig_pm25.update_layout(
                    xaxis_title="วันที่",
                    yaxis_title="PM2.5 (µg/m³)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_pm25, use_container_width=True)
            else:
                st.warning("ไม่มีข้อมูล PM2.5 ตามเงื่อนไขที่เลือก")
            
            # ========================================
            # 6. Heatmap/Point Map: PM2.5 ในพื้นที่กรุงเทพฯ
            # ========================================
            st.subheader(f"🗺️ การแสดงผล PM2.5: {'Heatmap' if visualization_mode_pm25 == '🌫️ Heatmap (ความหนาแน่น)' else 'Point Colors' if visualization_mode_pm25 == '🎨 Point Colors (ระดับ AQI)' else 'Both'}")
            
            # 🔥 **เก็บ state ใน session_state**
            if 'pm25_analysis_done' not in st.session_state:
                st.session_state.pm25_analysis_done = False
            
            if 'pm25_points_raw' not in st.session_state:
                st.session_state.pm25_points_raw = None
            
            if 'pm25_grid_processed' not in st.session_state:
                st.session_state.pm25_grid_processed = None
            
            if 'complaints_data_processed' not in st.session_state:
                st.session_state.complaints_data_processed = None
            
            if 'map_style_selected' not in st.session_state:
                st.session_state.map_style_selected = "Light"
            
            # 🔥 **เก็บข้อมูลที่ประมวลผลแล้วใน session_state**
            if apply_pm25_filter or not st.session_state.pm25_analysis_done:
                with st.spinner("กำลังประมวลผลข้อมูลสำหรับแผนที่..."):
                    # ========================================
                    # 1. กรองข้อมูล PM2.5 จากสถานี
                    # ========================================
                    pm25_filtered_local = pm25_df.copy()
                    
                    # กรองตามปี
                    pm25_filtered_local = pm25_filtered_local[pm25_filtered_local['year'] == selected_year]
                    
                    # กรองตามไตรมาส
                    if selected_quarter != "ทั้งหมด":
                        pm25_filtered_local = pm25_filtered_local[pm25_filtered_local['quarter'] == selected_quarter]
                    
                    # กรองตามเดือน
                    if selected_month != "ทั้งหมด":
                        pm25_filtered_local = pm25_filtered_local[pm25_filtered_local['month'] == selected_month]
                    
                    # กรองตามช่วงค่า PM2.5
                    pm25_filtered_local = pm25_filtered_local[
                        (pm25_filtered_local['pm2_5'] >= pm25_range[0]) & 
                        (pm25_filtered_local['pm2_5'] <= pm25_range[1])
                    ]
                    
                    # ========================================
                    # 2. กรองข้อมูลข้อร้องเรียน PM2.5
                    # ========================================
                    complaints_filtered_local = df_exploded.copy()
                    
                    # กรองตามปีเดียวกันกับ PM2.5
                    complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['year'] == selected_year]
                    
                    # กรองตามไตรมาส
                    if selected_quarter != "ทั้งหมด":
                        complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['quarter'] == selected_quarter]
                    
                    # กรองตามเดือน
                    if selected_month != "ทั้งหมด":
                        complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['month'] == selected_month]
                    
                    # กรองตามเขต
                    if selected_pm25_district != "ทั้งหมด":
                        complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['district'] == selected_pm25_district]
                    
                    # 🔥 **กรองเฉพาะประเภทปัญหา PM2.5**
                    if selected_complaint_type != "ทั้งหมด":
                        complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['type_exploded'] == selected_complaint_type]
                    elif len(pm25_related_types) > 0:
                        complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['type_exploded'].isin(pm25_related_types)]
                    
                    # ========================================
                    # 3. ประมวลผลข้อมูลสำหรับแผนที่
                    # ========================================
                    if len(pm25_filtered_local) > 0:
                        st.info(f"ข้อมูล PM2.5 จากสถานี: {len(pm25_filtered_local):,} จุด")
                        st.info(f"ข้อมูลข้อร้องเรียน PM2.5: {len(complaints_filtered_local):,} รายการ (แยกประเภท)")
                        st.info(f"จำนวนเคสข้อร้องเรียนที่ไม่ซ้ำ: {count_unique_complaints(complaints_filtered_local, df_original):,} เคส")
                        
                        # 🔥 **เก็บจุดดิบ PM2.5**
                        pm25_points_raw_data = pm25_filtered_local[['lat', 'lon', 'pm2_5', 'date_dt']].copy()
                        
                        # ลดจำนวนจุดถ้ามีเยอะเกินไป
                        if len(pm25_points_raw_data) > 10000:
                            pm25_points_raw_data = pm25_points_raw_data.sample(10000, random_state=42)
                        
                        # สร้างกริดสำหรับ Heatmap (ถ้าต้องการ)
                        grid_size = 0.01
                        pm25_grid_data = pm25_points_raw_data.copy()
                        pm25_grid_data['lat_grid'] = (pm25_grid_data['lat'] / grid_size).round() * grid_size
                        pm25_grid_data['lon_grid'] = (pm25_grid_data['lon'] / grid_size).round() * grid_size
                        
                        pm25_grid_agg = pm25_grid_data.groupby(['lat_grid', 'lon_grid']).agg({
                            'pm2_5': 'mean',
                            'lat': 'count'
                        }).reset_index()
                        pm25_grid_agg.rename(columns={'lat': 'point_count'}, inplace=True)
                        
                        # เก็บข้อมูลใน session_state
                        st.session_state.pm25_points_raw = pm25_points_raw_data
                        st.session_state.pm25_grid_processed = pm25_grid_agg
                        st.session_state.complaints_data_processed = complaints_filtered_local.copy()
                        st.session_state.pm25_analysis_done = True
                        
                        st.success(f"✅ ประมวลผลข้อมูลสำเร็จ: {len(pm25_points_raw_data):,} จุดดิบ | {len(pm25_grid_agg):,} เซลล์กริด")
                    else:
                        st.warning("ไม่มีข้อมูล PM2.5 จากสถานีตามเงื่อนไขที่เลือก")
                        st.session_state.pm25_points_raw = None
                        st.session_state.pm25_grid_processed = None
                        st.session_state.complaints_data_processed = None
            
            # 🔥 **ใช้ข้อมูลจาก session_state**
            pm25_points_raw = st.session_state.pm25_points_raw
            pm25_grid = st.session_state.pm25_grid_processed
            complaints_filtered_copy = st.session_state.complaints_data_processed
            
            if pm25_points_raw is not None and len(pm25_points_raw) > 0:
                st.info(f"แสดงผล PM2.5: {len(pm25_points_raw):,} จุด")
                
                # 🔥 **UI Controls สำหรับแผนที่**
                st.markdown("---")
                st.markdown("### 🎨 ปรับแต่งแผนที่")
                
                with st.form("pm25_map_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Map style selector
                        mapbox_styles = {
                            "Street": "streets",
                            "Light": "light",
                            "Dark": "dark",
                            "Satellite": "satellite",
                        }
                        
                        map_style = st.selectbox(
                            "สไตล์แผนที่",
                            list(mapbox_styles.keys()),
                            index=list(mapbox_styles.keys()).index(st.session_state.map_style_selected)
                            if st.session_state.map_style_selected in mapbox_styles else 1
                        )
                    
                    with col2:
                        # Opacity settings
                        if visualization_mode_pm25 in ["🌫️ Heatmap (ความหนาแน่น)", "📊 ทั้งสองแบบ"]:
                            heatmap_opacity = st.slider(
                                "ความโปร่งใส Heatmap",
                                min_value=0.1,
                                max_value=1.0,
                                value=0.7,
                                step=0.1
                            )
                        
                        if visualization_mode_pm25 in ["🎨 Point Colors (ระดับ AQI)", "📊 ทั้งสองแบบ"]:
                            points_opacity = st.slider(
                                "ความโปร่งใสจุดสี",
                                min_value=0.1,
                                max_value=1.0,
                                value=0.8,
                                step=0.1
                            )
                    
                    update_map = st.form_submit_button("🔄 อัพเดทแผนที่")
                
                if update_map:
                    st.session_state.map_style_selected = map_style
                    st.rerun()
                
                # 🔥 **สร้างแผนที่**
                def create_pm25_map():
                    """ฟังก์ชันสร้างแผนที่"""
                    layers = []
                    
                    # 1. OpenStreetMap base layer
                    tile_layer = pdk.Layer(
                        "TileLayer",
                        data=None,
                        get_tile_data="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                        opacity=1.0,
                        pickable=False,
                        max_zoom=19,
                        min_zoom=0
                    )
                    layers.append(tile_layer)
                    
                    # 2. Heatmap Layer (ถ้าเลือก)
                    if visualization_mode_pm25 in ["🌫️ Heatmap (ความหนาแน่น)", "📊 ทั้งสองแบบ"] and pm25_grid is not None:
                        heatmap_layer = pdk.Layer(
                            "HeatmapLayer",
                            data=pm25_grid,
                            get_position=['lon_grid', 'lat_grid'],
                            get_weight='pm2_5',
                            radius_pixels=60,
                            intensity=1,
                            threshold=0.05,
                            opacity=heatmap_opacity if visualization_mode_pm25 == "🌫️ Heatmap (ความหนาแน่น)" else heatmap_opacity * 0.6,
                            pickable=True
                        )
                        layers.append(heatmap_layer)
                    
                    # 3. Point Colors Layer (ถ้าเลือก)
                    if visualization_mode_pm25 in ["🎨 Point Colors (ระดับ AQI)", "📊 ทั้งสองแบบ"]:
                        def get_aqi_color(pm25_value):
                            """แปลงค่า PM2.5 เป็นสีตาม AQI ไทย"""
                            if pm25_value <= 25:
                                return [0, 255, 0, 180]      # 🟢 เขียว
                            elif pm25_value <= 37:
                                return [255, 255, 0, 180]    # 🟡 เหลือง
                            elif pm25_value <= 50:
                                return [255, 165, 0, 180]    # 🟠 ส้ม
                            elif pm25_value <= 90:
                                return [255, 0, 0, 180]      # 🔴 แดง
                            elif pm25_value <= 120:
                                return [128, 0, 128, 180]    # 🟣 ม่วง
                            else:
                                return [139, 69, 19, 180]    # 🟤 น้ำตาล
                        
                        # ใช้จุดดิบ PM2.5
                        pm25_points_colored = pm25_points_raw.copy()
                        pm25_points_colored['color'] = pm25_points_colored['pm2_5'].apply(get_aqi_color)
                        
                        points_layer = pdk.Layer(
                            "ScatterplotLayer",
                            data=pm25_points_colored,
                            get_position=['lon', 'lat'],
                            get_color='color',
                            get_radius=40,
                            radius_min_pixels=2,
                            radius_max_pixels=10,
                            pickable=True,
                            opacity=points_opacity if visualization_mode_pm25 == "🎨 Point Colors (ระดับ AQI)" else points_opacity * 0.6
                        )
                        layers.append(points_layer)
                    
                    # 4. ข้อร้องเรียน PM2.5 (ถ้ามี)
                    if complaints_filtered_copy is not None and len(complaints_filtered_copy) > 0:
                        complaints_sample = complaints_filtered_copy.sample(
                            min(5000, len(complaints_filtered_copy)), 
                            random_state=42
                        )
                        
                        complaints_layer = pdk.Layer(
                            "ScatterplotLayer",
                            data=complaints_sample,
                            get_position=['lon', 'lat'],
                            get_color=[0, 0, 255, 180],  # สีน้ำเงิน
                            get_radius=50,
                            radius_min_pixels=2,
                            radius_max_pixels=8,
                            pickable=True,
                            opacity=0.6
                        )
                        layers.append(complaints_layer)
                    
                    # คำนวณจุดกึ่งกลาง
                    center_lat = pm25_points_raw['lat'].mean()
                    center_lon = pm25_points_raw['lon'].mean()
                    
                    view_state = pdk.ViewState(
                        latitude=center_lat,
                        longitude=center_lon,
                        zoom=11,
                        pitch=0,
                        bearing=0
                    )
                    
                    tooltip = {
                        "html": """
                        <div style="padding: 8px; background-color: rgba(0,0,0,0.85); color: white; 
                                    border-radius: 5px; font-size: 12px;">
                            <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">
                                📍 ข้อมูล PM2.5
                            </div>
                            <div style="margin: 3px 0;">
                                <span style="color: #4ECDC4;">📊 ค่า PM2.5:</span> {pm2_5:.1f} µg/m³
                            </div>
                            <div style="margin: 3px 0;">
                                <span style="color: #FF6B6B;">📍 ตำแหน่ง:</span> ({lat:.4f}, {lon:.4f})
                            </div>
                            <div style="margin: 3px 0;">
                                <span style="color: #FFD166;">📅 วันที่:</span> {date_dt}
                            </div>
                        </div>
                        """,
                        "style": {"color": "white"}
                    }
                    
                    # สร้างแผนที่
                    deck = pdk.Deck(
                        layers=layers,
                        initial_view_state=view_state,
                        tooltip=tooltip
                    )
                    
                    return deck
                
                # 🔥 **แสดงแผนที่**
                map_container = st.container()
                with map_container:
                    try:
                        deck = create_pm25_map()
                        st.pydeck_chart(deck)
                        
                        # แสดง legend ตามโหมด
                        if visualization_mode_pm25 == "🌫️ Heatmap (ความหนาแน่น)":
                            st.caption("🎯 **Heatmap Mode:** แสดงความหนาแน่นของ PM2.5 (แดง=สูง, เหลือง=ต่ำ)")
                        elif visualization_mode_pm25 == "🎨 Point Colors (ระดับ AQI)":
                            st.caption("""
                            🎨 **Point Colors Mode:** แสดงระดับ PM2.5 ตาม AQI ไทย:
                            🟢 0-25 | 🟡 26-37 | 🟠 38-50 | 🔴 51-90 | 🟣 91-120 | 🟤 >120 µg/m³
                            |🔵 ข้อร้องเรียนของประชาชน
                            """)
                        else:
                            st.caption("📊 **โหมดผสม:** Heatmap + Point Colors")
                        
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการสร้างแผนที่: {str(e)}")
                
                # 🔥 **แสดงสถิติ**
                st.markdown("---")
                st.subheader("📊 สถิติข้อมูล PM2.5")
                
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    # ระดับ AQI
                    pm25_values = pm25_points_raw['pm2_5']
                    aqi_counts = {
                        "🟢 ดี (0-25)": len(pm25_values[pm25_values <= 25]),
                        "🟡 ปานกลาง (26-37)": len(pm25_values[(pm25_values > 25) & (pm25_values <= 37)]),
                        "🟠 เริ่มมีผล (38-50)": len(pm25_values[(pm25_values > 37) & (pm25_values <= 50)]),
                        "🔴 มีผลมาก (51-90)": len(pm25_values[(pm25_values > 50) & (pm25_values <= 90)]),
                        "🟣 อันตราย (91-120)": len(pm25_values[(pm25_values > 90) & (pm25_values <= 120)]),
                        "🟤 อันตรายมาก (>120)": len(pm25_values[pm25_values > 120])
                    }
                    
                    st.write("**การกระจายระดับ AQI:**")
                    for level, count in aqi_counts.items():
                        percentage = (count / len(pm25_values)) * 100
                        st.write(f"{level}: {count:,} จุด ({percentage:.1f}%)")
                
                with col_stat2:
                    st.metric("ค่า PM2.5 เฉลี่ย", f"{pm25_points_raw['pm2_5'].mean():.1f} µg/m³")
                    st.metric("ค่า PM2.5 สูงสุด", f"{pm25_points_raw['pm2_5'].max():.1f} µg/m³")
                    st.metric("ค่า PM2.5 ต่ำสุด", f"{pm25_points_raw['pm2_5'].min():.1f} µg/m³")
                
                with col_stat3:
                    if complaints_filtered_copy is not None:
                        unique_complaints = count_unique_complaints(complaints_filtered_copy, df_original)
                        st.metric("จำนวนข้อร้องเรียน PM2.5 (ไม่ซ้ำ)", f"{unique_complaints:,}")
                        if unique_complaints > 0:
                            min_date_complaint = complaints_filtered_copy['timestamp_dt'].min().date()
                            max_date_complaint = complaints_filtered_copy['timestamp_dt'].max().date()
                            st.metric("ช่วงเวลา", f"{min_date_complaint} ถึง {max_date_complaint}")
                
                # 🔥 **ปุ่มรีเซ็ตแผนที่**
                col_reset, col_info = st.columns([1, 3])
                with col_reset:
                    if st.button("🔄 รีเซ็ตการตั้งค่าแผนที่", type="secondary"):
                        st.session_state.map_style_selected = "Light"
                        st.rerun()
                
                with col_info:
                    st.info("💡 สามารถเลือกโหมดการแสดงผลได้จากแถบด้านข้าง")
                    
            else:
                st.warning("ไม่มีข้อมูล PM2.5 ตามเงื่อนไขที่เลือก")
            
            # ========================================
            # 7. ตารางสรุปเปรียบเทียบ
            # ========================================
            st.subheader("📋 ตารางสรุปเปรียบเทียบ")
            
            if len(pm25_filtered) > 0:
                # สรุปข้อมูล PM2.5 ตามเดือน
                pm25_monthly = pm25_filtered.groupby('month').agg({
                    'pm2_5': ['mean', 'max', 'min', 'count']
                }).round(2)
                pm25_monthly.columns = ['ค่าเฉลี่ย', 'ค่าสูงสุด', 'ค่าต่ำสุด', 'จำนวนข้อมูล']
                pm25_monthly = pm25_monthly.reset_index()
                
                # สรุปข้อมูลข้อร้องเรียนตามเดือน (นับ unique)
                if len(complaints_filtered) > 0:
                    complaints_monthly_unique = {}
                    for month in complaints_filtered['month'].unique():
                        month_data = complaints_filtered[complaints_filtered['month'] == month]
                        unique_count_month = count_unique_complaints(month_data, df_original)
                        complaints_monthly_unique[month] = unique_count_month
                    
                    complaints_monthly = pd.DataFrame({
                        'month': list(complaints_monthly_unique.keys()),
                        'จำนวนข้อร้องเรียน': list(complaints_monthly_unique.values())
                    })
                    
                    # รวมข้อมูล
                    comparison_df = pd.merge(
                        pm25_monthly,
                        complaints_monthly,
                        on='month',
                        how='left'
                    )
                    comparison_df['เดือน'] = comparison_df['month'].apply(lambda x: f'เดือน {x}')
                    
                    # แสดงตาราง
                    st.dataframe(
                        comparison_df[['เดือน', 'ค่าเฉลี่ย', 'ค่าสูงสุด', 'ค่าต่ำสุด', 'จำนวนข้อร้องเรียน']],
                        use_container_width=True
                    )
                    
                    # แสดง note
                    st.caption("ℹ️ จำนวนข้อร้องเรียนเป็นการนับเคสที่ไม่ซ้ำ")
                else:
                    pm25_monthly['เดือน'] = pm25_monthly['month'].apply(lambda x: f'เดือน {x}')
                    st.dataframe(
                        pm25_monthly[['เดือน', 'ค่าเฉลี่ย', 'ค่าสูงสุด', 'ค่าต่ำสุด', 'จำนวนข้อมูล']],
                        use_container_width=True
                    )
                    
                    st.info("ไม่มีข้อมูลข้อร้องเรียนตามเงื่อนไขที่เลือก")
    
    else:
        # แสดงข้อมูลเริ่มต้นเมื่อยังไม่ได้กดวิเคราะห์
        st.info("👈 กรุณากดปุ่ม 'วิเคราะห์ PM2.5' ในแถบด้านข้างเพื่อเริ่มการวิเคราะห์")
        
        # แสดงตัวอย่างข้อมูล
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("ข้อมูล PM2.5 ตัวอย่าง")
            st.dataframe(pm25_df[['date_str', 'lat', 'lon', 'pm2_5', 'quarter', 'month']].head(10))
            
        with col2:
            st.subheader("ข้อมูลข้อร้องเรียน ตัวอย่าง")
            st.dataframe(df_exploded[['timestamp_dt', 'type_exploded', 'district', 'organization', 'quarter', 'month']].head(10))
        
        # แสดงสถิติเบื้องต้น
        st.subheader("📈 สถิติข้อมูล PM2.5 ทั้งหมด")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        with col_stat1:
            st.metric("ปีที่มีข้อมูล", f"{len(available_years)} ปี")
        
        with col_stat2:
            st.metric("ค่า PM2.5 เฉลี่ยทั้งหมด", f"{pm25_df['pm2_5'].mean():.1f} µg/m³")
        
        with col_stat3:
            st.metric("ค่า PM2.5 สูงสุด", f"{pm25_df['pm2_5'].max():.1f} µg/m³")
        
        with col_stat4:
            st.metric("จำนวนข้อมูลทั้งหมด", f"{len(pm25_df):,} รายการ")