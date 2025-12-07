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

# ---------------------------
# Load PM2.5 Data with Progress
# ---------------------------
@st.cache_data(show_spinner=False)
def load_pm25_data_with_progress():
    """โหลดข้อมูล PM2.5 ของกรุงเทพฯ"""
    progress = st.progress(0, text="กำลังโหลดข้อมูล PM2.5...")
    
    # STEP 1: load CSV
    progress.progress(25, text="โหลดข้อมูล PM2.5 จากไฟล์...")
    pm25_df = pd.read_csv("dataset/bkk_pm25_daily_2023_all_fast.csv")
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
# Load Data with Progress Bar
# ---------------------------
@st.cache_data(show_spinner=False)
def load_data_with_progress():
    progress = st.progress(0, text="กำลังโหลดข้อมูล...")
    status = st.empty()

    # STEP 1: load CSV
    progress.progress(20, text="โหลด CSV ...")
    df = pd.read_csv("dataset/df_clean_organization.csv")
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
    df_exploded["timestamp_dt"] = pd.to_datetime(df_exploded["timestamp"], errors="coerce")

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

    # เพิ่มคอลัมน์ Quarter และ Month สำหรับการวิเคราะห์ PM2.5
    df_exploded['quarter'] = df_exploded['timestamp_dt'].dt.quarter
    df_exploded['month'] = df_exploded['timestamp_dt'].dt.month
    df_exploded['year'] = df_exploded['timestamp_dt'].dt.year
    
    status.success("โหลดข้อมูลสำเร็จ!")

    return df_exploded

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
        df = load_data_with_progress()
    
    with st.spinner("กำลังโหลดข้อมูล PM2.5..."):
        pm25_df = load_pm25_data_with_progress()
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ ข้อมูลข้อร้องเรียนถูกโหลดและ cache แล้ว")
        st.info(f"จำนวนรายการ: {len(df):,} รายการ")
        st.write(f"ช่วงเวลา: {df['timestamp_dt'].min().date()} ถึง {df['timestamp_dt'].max().date()}")
        
    with col2:
        st.success("✅ ข้อมูล PM2.5 ถูกโหลดและ cache แล้ว")
        st.info(f"จำนวนรายการ: {len(pm25_df):,} รายการ")
        st.write(f"ช่วงเวลา: {pm25_df['date_dt'].min().date()} ถึง {pm25_df['date_dt'].max().date()}")
    
    # แสดงตัวอย่างข้อมูล
    with st.expander("👁️ ดูตัวอย่างข้อมูล PM2.5"):
        st.dataframe(pm25_df.head(10))

# ---------------------------
# Tab 2: Dashboard (Main)
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

    # Organization dropdown (หลัก)
    organizations = ["ทั้งหมด"] + sorted(df["organization"].dropna().unique())
    selected_org = st.sidebar.selectbox("เลือกองค์กรหลัก", organizations)

    # Organization List (หลายรายการ)
    all_org_lists = sorted(
        {org for lst in df["organization_list"] for org in lst if isinstance(lst, list)}
    )
    selected_org_multi = st.sidebar.multiselect("เลือกหลายองค์กร (organization_list)", all_org_lists)
    
    # Filtering
    df_filtered = df.copy()

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
    min_date = df["timestamp_dt"].min().date()
    max_date = df["timestamp_dt"].max().date()

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
    
    # -----------------------------
    # Display Metrics
    # -----------------------------
    st.header("📈 สถิติและข้อมูล")
    
    # ถ้าเลือกองค์กรหลัก
    if selected_org != "ทั้งหมด":
        df_org = df_filtered[df_filtered["organization"] == selected_org]
        count_cases = len(df_org)

        if count_cases >= 50:
            avg_rating = df_org["star"].mean()
            st.metric("⭐ Rating ขององค์กร", f"{avg_rating:.2f}")
        else:
            st.info(f"องค์กร {selected_org} มีจำนวนปัญหา {count_cases} เคส — ไม่แสดง Rating (ต้องการอย่างน้อย 50 เคส)")
    
    # -----------------------------
    # Cases Count by Time Range
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
            count = df_filtered[df_filtered["timestamp_dt"] >= start_time].shape[0]
            with cols[idx % 3]:
                st.metric(label, f"{count:,} เคส")
    else:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    
    # -----------------------------
    # Top 10 Bar Chart
    # -----------------------------
    st.subheader("⭐ Top 10 ปัญหาที่เกิดมากที่สุด")

    if df_filtered.empty:
        st.warning("ไม่พบข้อมูลตามเงื่อนไขที่เลือก")
    else:
        # 1. Groupby และนับจำนวนเคส (Value Counts)
        top_10_types = df_filtered["type_exploded"].value_counts().nlargest(10).reset_index()
        top_10_types.columns = ["ประเภทปัญหา", "จำนวนเคส"]

        # 2. สร้าง Bar Chart
        fig = px.bar(
            top_10_types,
            x="จำนวนเคส",
            y="ประเภทปัญหา",
            orientation='h',
            title="10 อันดับปัญหาที่มีจำนวนเคสสูงสุด",
            color="จำนวนเคส",
            color_continuous_scale='Viridis'
        )
        
        # ปรับปรุง layout
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False)
        )

        st.plotly_chart(fig, use_container_width=True)
    
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
            
            # โหลดตำแหน่งขององค์กร (ถ้ามี)
            try:
                org_loc_df = pd.read_csv("dataset/bkk_osm_organization_locations.csv")
                org_loc_df['name_norm'] = org_loc_df['name'].str.strip().str.lower()
                df_map['organization_norm'] = df_map['organization'].fillna("").str.strip().str.lower()
                filtered_orgs = df_map['organization_norm'].unique()
                org_points = org_loc_df[org_loc_df['name_norm'].isin(filtered_orgs)].copy()
                
                if len(org_points) > 0:
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
                else:
                    layers = [layer]
            except:
                layers = [layer]

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
# Tab 3: PM2.5 Analysis
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
    districts_complaints = ["ทั้งหมด"] + sorted(df['district'].unique())
    selected_pm25_district = st.sidebar.selectbox("เลือกเขต (เปรียบเทียบ)", districts_complaints, key='pm25_district')
    
    # Filter ประเภทปัญหา
    complaint_types = ["ทั้งหมด"] + sorted(df['type_exploded'].unique())
    selected_complaint_type = st.sidebar.selectbox("เลือกประเภทปัญหา (เปรียบเทียบ)", complaint_types, key='pm25_type')
    
    # Filter PM2.5 Level
    pm25_range = st.sidebar.slider(
        "ช่วงค่า PM2.5 (µg/m³)",
        min_value=int(pm25_df['pm2_5'].min()),
        max_value=int(pm25_df['pm2_5'].max()),
        value=(0, 100),
        key='pm25_range'
    )
    
    apply_pm25_filter = st.sidebar.button('🚀 วิเคราะห์ PM2.5', key='apply_pm25')
    
    if apply_pm25_filter:
        with st.spinner("กำลังวิเคราะห์ข้อมูล PM2.5 และข้อร้องเรียน..."):
            
            # ========================================
            # 1. กรองข้อมูล PM2.5
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
            # 2. กรองข้อมูลข้อร้องเรียน
            # ========================================
            complaints_filtered = df.copy()
            
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
            
            # กรองตามประเภทปัญหา
            if selected_complaint_type != "ทั้งหมด":
                complaints_filtered = complaints_filtered[complaints_filtered['type_exploded'] == selected_complaint_type]
            
            # ========================================
            # 3. แสดงข้อมูลสถิติ
            # ========================================
            st.subheader("📊 สรุปข้อมูล")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📅 ปีที่วิเคราะห์", selected_year)
                st.metric("📈 จำนวนรายการ PM2.5", f"{len(pm25_filtered):,}")
                avg_pm25 = pm25_filtered['pm2_5'].mean()
                st.metric("🌫️ ค่า PM2.5 เฉลี่ย", f"{avg_pm25:.1f} µg/m³")
            
            with col2:
                quarter_text = f"ไตรมาส {selected_quarter}" if selected_quarter != "ทั้งหมด" else "ทั้งหมด"
                st.metric("📊 ไตรมาส", quarter_text)
                st.metric("📝 จำนวนข้อร้องเรียน", f"{len(complaints_filtered):,}")
                if len(complaints_filtered) > 0:
                    avg_rating = complaints_filtered['star'].mean()
                    st.metric("⭐ คะแนนเฉลี่ย", f"{avg_rating:.2f}")
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
                    st.metric("🔧 ประเภทปัญหา", "ทั้งหมด")
            
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
                    title=f'ค่า PM2.5 เฉลี่ยรายวัน ({selected_year})',
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
            # 5. Visualization: เปรียบเทียบข้อร้องเรียนกับ PM2.5
            # ========================================
            st.subheader("📊 เปรียบเทียบข้อร้องเรียนกับระดับ PM2.5")
            
            if len(complaints_filtered) > 0 and len(pm25_filtered) > 0:
                # จัดกลุ่มข้อร้องเรียนตามวันที่
                complaints_daily = complaints_filtered.groupby(
                    complaints_filtered['timestamp_dt'].dt.date
                ).size().reset_index(name='complaint_count')
                complaints_daily['timestamp_dt'] = pd.to_datetime(complaints_daily['timestamp_dt'])
                
                # จัดกลุ่ม PM2.5 ตามวันที่
                pm25_daily_avg = pm25_filtered.groupby('date_dt')['pm2_5'].mean().reset_index()
                
                # รวมข้อมูล
                merged_data = pd.merge(
                    complaints_daily,
                    pm25_daily_avg,
                    left_on='timestamp_dt',
                    right_on='date_dt',
                    how='inner'
                )
                
                if len(merged_data) > 0:
                    # คำนวณ correlation ก่อน
                    correlation = merged_data['pm2_5'].corr(merged_data['complaint_count'])
                    
                    # สร้าง scatter plot (ไม่ใช้ trendline='ols')
                    fig_scatter = px.scatter(
                        merged_data,
                        x='pm2_5',
                        y='complaint_count',
                        title=f'ความสัมพันธ์ระหว่างระดับ PM2.5 และจำนวนข้อร้องเรียน (Correlation: {correlation:.3f})',
                        labels={'pm2_5': 'PM2.5 (µg/m³)', 'complaint_count': 'จำนวนข้อร้องเรียน'},
                        hover_data=['timestamp_dt'],
                        trendline=None  # ไม่ใช้ trendline จาก statsmodels
                    )
                    
                    # เพิ่มเส้น regression ด้วย numpy (ถ้า correlation สูงพอ)
                    if abs(correlation) > 0.2:
                        try:
                            # คำนวณเส้น regression อย่างง่าย
                            x = merged_data['pm2_5'].values
                            y = merged_data['complaint_count'].values
                            
                            # ใช้ numpy สำหรับ linear regression
                            coeff = np.polyfit(x, y, 1)
                            poly = np.poly1d(coeff)
                            
                            # สร้างจุดสำหรับเส้น regression
                            x_line = np.linspace(x.min(), x.max(), 100)
                            y_line = poly(x_line)
                            
                            # เพิ่มเส้นลงในกราฟ
                            fig_scatter.add_trace(
                                go.Scatter(
                                    x=x_line,
                                    y=y_line,
                                    mode='lines',
                                    name='แนวโน้ม',
                                    line=dict(color='red', dash='dash'),
                                    showlegend=True
                                )
                            )
                            
                            # เพิ่มสมการ regression
                            equation = f'y = {coeff[0]:.3f}x + {coeff[1]:.3f}'
                            fig_scatter.update_layout(
                                annotations=[
                                    dict(
                                        x=0.05, y=0.95,
                                        xref="paper", yref="paper",
                                        text=f"Correlation: {correlation:.3f}<br>Regression: {equation}",
                                        showarrow=False,
                                        bgcolor="white",
                                        bordercolor="black",
                                        borderwidth=1
                                    )
                                ]
                            )
                        except:
                            # ถ้าคำนวณ regression ไม่ได้
                            fig_scatter.update_layout(
                                annotations=[
                                    dict(
                                        x=0.05, y=0.95,
                                        xref="paper", yref="paper",
                                        text=f"Correlation: {correlation:.3f}",
                                        showarrow=False,
                                        bgcolor="white",
                                        bordercolor="black",
                                        borderwidth=1
                                    )
                                ]
                            )
                    
                    fig_scatter.update_layout(
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)
                    
                    # แสดงผลลัพธ์ความสัมพันธ์
                    st.subheader("📈 การวิเคราะห์ความสัมพันธ์")
                    
                    col_corr1, col_corr2 = st.columns(2)
                    
                    with col_corr1:
                        st.metric("ค่าสหสัมพันธ์ (Correlation)", f"{correlation:.3f}")
                        
                        # ตีความ correlation
                        if correlation > 0.7:
                            st.success("🔴 **ความสัมพันธ์ทางบวกที่แข็งแกร่งมาก**")
                            st.write("PM2.5 สูงมีความสัมพันธ์อย่างชัดเจนกับการเพิ่มขึ้นของข้อร้องเรียน")
                        elif correlation > 0.5:
                            st.success("🟠 **ความสัมพันธ์ทางบวกระดับปานกลาง**")
                            st.write("PM2.5 สูงมีความสัมพันธ์กับการเพิ่มขึ้นของข้อร้องเรียน")
                        elif correlation > 0.3:
                            st.info("🟡 **ความสัมพันธ์ทางบวกระดับอ่อน**")
                            st.write("PM2.5 สูงอาจเกี่ยวข้องกับการเพิ่มขึ้นของข้อร้องเรียน")
                        elif correlation > -0.3:
                            st.warning("⚪ **ไม่มีความสัมพันธ์ที่ชัดเจน**")
                            st.write("ระดับ PM2.5 และจำนวนข้อร้องเรียนไม่มีความสัมพันธ์กัน")
                        elif correlation > -0.5:
                            st.info("🟢 **ความสัมพันธ์ทางลบระดับอ่อน**")
                            st.write("PM2.5 สูงอาจเกี่ยวข้องกับการลดลงของข้อร้องเรียน")
                        elif correlation > -0.7:
                            st.success("🔵 **ความสัมพันธ์ทางลบระดับปานกลาง**")
                            st.write("PM2.5 สูงมีความสัมพันธ์กับการลดลงของข้อร้องเรียน")
                        else:
                            st.success("🟣 **ความสัมพันธ์ทางลบที่แข็งแกร่งมาก**")
                            st.write("PM2.5 สูงมีความสัมพันธ์อย่างชัดเจนกับการลดลงของข้อร้องเรียน")
                    
                    with col_corr2:
                        # สรุปข้อมูลสถิติ
                        st.metric("ช่วงค่า PM2.5", f"{merged_data['pm2_5'].min():.1f} - {merged_data['pm2_5'].max():.1f} µg/m³")
                        st.metric("ช่วงข้อร้องเรียน", f"{merged_data['complaint_count'].min()} - {merged_data['complaint_count'].max()} ครั้ง/วัน")
                        
                        # คำนวณวันที่ที่มี PM2.5 สูงสุดและต่ำสุด
                        max_pm25_day = merged_data.loc[merged_data['pm2_5'].idxmax()]
                        min_pm25_day = merged_data.loc[merged_data['pm2_5'].idxmin()]
                        
                        st.write("**วันที่ PM2.5 สูงสุด:**")
                        st.write(f"- วันที่: {max_pm25_day['timestamp_dt'].date()}")
                        st.write(f"- ค่า PM2.5: {max_pm25_day['pm2_5']:.1f} µg/m³")
                        st.write(f"- ข้อร้องเรียน: {max_pm25_day['complaint_count']} ครั้ง")
                        
                        st.write("**วันที่ PM2.5 ต่ำสุด:**")
                        st.write(f"- วันที่: {min_pm25_day['timestamp_dt'].date()}")
                        st.write(f"- ค่า PM2.5: {min_pm25_day['pm2_5']:.1f} µg/m³")
                        st.write(f"- ข้อร้องเรียน: {min_pm25_day['complaint_count']} ครั้ง")
                    
                    # แสดงตารางข้อมูล
                    with st.expander("📋 ดูข้อมูลเปรียบเทียบรายวัน"):
                        st.dataframe(
                            merged_data[['timestamp_dt', 'pm2_5', 'complaint_count']].sort_values('pm2_5', ascending=False),
                            use_container_width=True
                        )
                        
                else:
                    st.warning("ไม่มีข้อมูลที่ตรงกันระหว่างวันที่ของข้อร้องเรียนและข้อมูล PM2.5")
                    
                    # แสดงเหตุผลที่เป็นไปได้
                    st.info("**สาเหตุที่เป็นไปได้:**")
                    st.write("1. ข้อมูลข้อร้องเรียนและข้อมูล PM2.5 ไม่มีวันเดียวกัน")
                    st.write("2. ข้อมูลมีช่วงเวลาที่ไม่ตรงกัน")
                    st.write("3. ตัวกรองที่เลือกจำกัดข้อมูลมากเกินไป")
                    
                    # แสดงช่วงเวลาของข้อมูลแต่ละส่วน
                    if len(complaints_daily) > 0:
                        st.write(f"📅 ข้อร้องเรียนมีข้อมูลวันที่: {complaints_daily['timestamp_dt'].min().date()} ถึง {complaints_daily['timestamp_dt'].max().date()}")
                    if len(pm25_daily_avg) > 0:
                        st.write(f"🌫️ PM2.5 มีข้อมูลวันที่: {pm25_daily_avg['date_dt'].min().date()} ถึง {pm25_daily_avg['date_dt'].max().date()}")
            else:
                st.warning("ไม่มีข้อมูลข้อร้องเรียนหรือ PM2.5 ตามเงื่อนไขที่เลือก")
                
                # ให้คำแนะนำ
                if len(complaints_filtered) == 0:
                    st.write("❌ **ไม่มีข้อมูลข้อร้องเรียน** - ลองปรับเงื่อนไข:")
                    st.write("- เลือกปีที่ต่างออกไป")
                    st.write("- เลือกประเภทปัญหาอื่น")
                    st.write("- เลือกเขตอื่นหรือไม่เลือกเขต")
                    
                if len(pm25_filtered) == 0:
                    st.write("❌ **ไม่มีข้อมูล PM2.5** - ลองปรับเงื่อนไข:")
                    st.write("- เลือกปีที่ต่างออกไป")
                    st.write("- ขยายช่วงค่า PM2.5")
                    st.write("- เลือกไตรมาส/เดือนอื่น")
            
                        # ========================================
            # 6. Heatmap: PM2.5 ในพื้นที่กรุงเทพฯ (Optimized)
            # ========================================
            st.subheader("🗺️ Heatmap ค่า PM2.5 ในกรุงเทพฯ")
            
            # 🔥 **แก้ไข: เก็บ state ใน session_state**
            if 'pm25_analysis_done' not in st.session_state:
                st.session_state.pm25_analysis_done = False
            
            if 'pm25_data_processed' not in st.session_state:
                st.session_state.pm25_data_processed = None
            
            if 'complaints_data_processed' not in st.session_state:
                st.session_state.complaints_data_processed = None
            
            if 'map_style_selected' not in st.session_state:
                st.session_state.map_style_selected = "Light"
            
            if 'complaint_color_selected' not in st.session_state:
                st.session_state.complaint_color_selected = [255, 0, 0]  # แดง
            
            # 🔥 **เก็บข้อมูลที่ประมวลผลแล้วใน session_state**
            # ถ้ายังไม่ได้วิเคราะห์ หรือกดปุ่มวิเคราะห์ใหม่
            if apply_pm25_filter or not st.session_state.pm25_analysis_done:
                with st.spinner("กำลังประมวลผลข้อมูลสำหรับ Heatmap..."):
                    # ========================================
                    # 1. กรองข้อมูล PM2.5
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
                    # 2. กรองข้อมูลข้อร้องเรียน
                    # ========================================
                    complaints_filtered_local = df.copy()
                    
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
                    
                    # กรองตามประเภทปัญหา
                    if selected_complaint_type != "ทั้งหมด":
                        complaints_filtered_local = complaints_filtered_local[complaints_filtered_local['type_exploded'] == selected_complaint_type]
                    
                    # ========================================
                    # 3. ประมวลผลข้อมูลสำหรับ Heatmap
                    # ========================================
                    if len(pm25_filtered_local) > 0:
                        # แสดงจำนวนข้อมูล
                        st.info(f"พบข้อมูล PM2.5 ทั้งหมด {len(pm25_filtered_local):,} จุด")
                        
                        # ลดจำนวนจุดข้อมูลถ้าจำนวนมากเกินไป
                        if len(pm25_filtered_local) > 50000:
                            st.warning("⚠️ ข้อมูลมีจำนวนมาก กำลังลดความละเอียดเพื่อประสิทธิภาพ...")
                            pm25_sampled = pm25_filtered_local.sample(30000, random_state=42)
                        else:
                            pm25_sampled = pm25_filtered_local
                        
                        # สร้างกริดละติจูด/ลองจิจูด
                        grid_size = 0.01  # ประมาณ 1.1 กม.
                        
                        # เพิ่มคอลัมน์กริด
                        pm25_sampled['lat_grid'] = (pm25_sampled['lat'] / grid_size).round() * grid_size
                        pm25_sampled['lon_grid'] = (pm25_sampled['lon'] / grid_size).round() * grid_size
                        
                        # รวมข้อมูลในแต่ละเซลล์กริด
                        pm25_grid_local = pm25_sampled.groupby(['lat_grid', 'lon_grid']).agg({
                            'pm2_5': 'mean',
                            'lat': 'count'
                        }).reset_index()
                        pm25_grid_local.rename(columns={'lat': 'point_count'}, inplace=True)
                        
                        # เก็บข้อมูลใน session_state
                        st.session_state.pm25_data_processed = pm25_grid_local
                        st.session_state.complaints_data_processed = complaints_filtered_local.copy()
                        st.session_state.pm25_analysis_done = True
                        
                        st.success(f"✅ ประมวลผลข้อมูลสำเร็จ: {len(pm25_grid_local):,} เซลล์กริด")
                    else:
                        st.warning("ไม่มีข้อมูล PM2.5 ตามเงื่อนไขที่เลือก")
                        st.session_state.pm25_data_processed = None
                        st.session_state.complaints_data_processed = None
            
            # 🔥 **ใช้ข้อมูลจาก session_state**
            pm25_grid = st.session_state.pm25_data_processed
            
            if pm25_grid is not None and len(pm25_grid) > 0:
                complaints_filtered_copy = st.session_state.complaints_data_processed
                
                st.info(f"ข้อมูล PM2.5: {len(pm25_grid):,} เซลล์กริด")
                
                # 🔥 **UI Controls ที่ไม่ทำให้รีหน้า**
                st.markdown("---")
                st.markdown("### 🎨 ปรับแต่งแผนที่")
                
                # ใช้ form เพื่อรวมการควบคุม
                with st.form("map_settings_form"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Map style selector
                        mapbox_styles = {
                            "Street": "streets",
                            "Light": "light",
                            "Dark": "dark",
                            "Satellite": "satellite",
                            "Outdoors": "outdoors"
                        }
                        
                        map_style = st.selectbox(
                            "สไตล์แผนที่",
                            list(mapbox_styles.keys()),
                            index=list(mapbox_styles.keys()).index(st.session_state.map_style_selected)
                            if st.session_state.map_style_selected in mapbox_styles else 1
                        )
                    
                    with col2:
                        # Color picker สำหรับจุดข้อร้องเรียน
                        color_options = {
                            "🔴 แดง": [255, 0, 0],
                            "🔵 น้ำเงิน": [0, 0, 255],
                            "🟢 เขียว": [0, 255, 0],
                            "🟡 เหลือง": [255, 255, 0],
                            "🟣 ม่วง": [128, 0, 128],
                            "🟠 ส้ม": [255, 165, 0],
                            "⚫ ดำ": [0, 0, 0],
                            "⚪ ขาว": [255, 255, 255]
                        }
                        
                        # หาค่าเริ่มต้นจาก session_state
                        default_color_name = "🔴 แดง"
                        for name, color in color_options.items():
                            if color == st.session_state.complaint_color_selected:
                                default_color_name = name
                                break
                        
                        complaint_color_name = st.selectbox(
                            "สีจุดข้อร้องเรียน",
                            list(color_options.keys()),
                            index=list(color_options.keys()).index(default_color_name)
                        )
                        complaint_color = color_options[complaint_color_name]
                    
                    with col3:
                        # Heatmap settings
                        heatmap_opacity = st.slider(
                            "ความโปร่งใส Heatmap",
                            min_value=0.1,
                            max_value=1.0,
                            value=0.7,
                            step=0.1
                        )
                        
                        point_size = st.slider(
                            "ขนาดจุดข้อร้องเรียน",
                            min_value=50,
                            max_value=200,
                            value=100,
                            step=10
                        )
                    
                    # ปุ่มอัพเดทแผนที่
                    update_map = st.form_submit_button("🔄 อัพเดทแผนที่")
                
                # 🔥 **เมื่อกดอัพเดท แค่เปลี่ยนค่าใน session_state**
                if update_map:
                    st.session_state.map_style_selected = map_style
                    st.session_state.complaint_color_selected = complaint_color
                    st.rerun()  # รีเฉพาะส่วนที่จำเป็น
                
                # 🔥 **สร้างแผนที่โดยใช้ค่าจาก session_state**
                def create_pm25_map():
                    """ฟังก์ชันสร้างแผนที่แยกออกมา"""
                    # Heatmap Layer
                    heatmap_layer = pdk.Layer(
                        "HeatmapLayer",
                        data=pm25_grid,
                        get_position=['lon_grid', 'lat_grid'],
                        get_weight='pm2_5',
                        radius_pixels=50,
                        intensity=1,
                        threshold=0.05,
                        opacity=heatmap_opacity,
                        pickable=True
                    )
                    
                    layers = [heatmap_layer]
                    
                    # ถ้ามีข้อร้องเรียน
                    if complaints_filtered_copy is not None and len(complaints_filtered_copy) > 0:
                        # ลดจำนวนเพื่อ performance
                        complaints_sample = complaints_filtered_copy.sample(
                            min(5000, len(complaints_filtered_copy)), 
                            random_state=42
                        )
                        
                        complaints_layer = pdk.Layer(
                            "ScatterplotLayer",
                            data=complaints_sample,
                            get_position=['lon', 'lat'],
                            get_color=st.session_state.complaint_color_selected + [180],
                            get_radius=point_size,
                            radius_min_pixels=2,
                            radius_max_pixels=8,
                            pickable=True,
                            opacity=0.6
                        )
                        layers.append(complaints_layer)
                    
                    # 🔥 **ใช้ OpenStreetMap เป็นพื้นหลัง**
                    tile_layer = pdk.Layer(
                        "TileLayer",
                        data=None,
                        get_tile_data="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                        opacity=1.0,
                        pickable=False,
                        max_zoom=19,
                        min_zoom=0
                    )
                    
                    # ใส่ tile layer เป็น layer แรก
                    layers = [tile_layer] + layers
                    
                    # คำนวณจุดกึ่งกลาง
                    center_lat = pm25_grid['lat_grid'].mean()
                    center_lon = pm25_grid['lon_grid'].mean()
                    
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
                                <span style="color: #4ECDC4;">📊 ค่าเฉลี่ย:</span> {pm2_5:.1f} µg/m³
                            </div>
                            <div style="margin: 3px 0;">
                                <span style="color: #FF6B6B;">📍 ตำแหน่ง:</span> ({lat_grid:.4f}, {lon_grid:.4f})
                            </div>
                            <div style="margin: 3px 0;">
                                <span style="color: #FFD166;">🔢 จำนวนจุด:</span> {point_count}
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
                
                # 🔥 **แสดงแผนที่ใน container แยก**
                map_container = st.container()
                with map_container:
                    current_color_name = next(
                        (name for name, color in color_options.items() 
                         if color == st.session_state.complaint_color_selected), 
                        "🔴 แดง"
                    )
                    
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>🗺️ แผนที่ปัจจุบัน:</strong> {st.session_state.map_style_selected} | 
                        <strong>🎨 สีข้อร้องเรียน:</strong> {current_color_name} | 
                        <strong>📊 เซลล์ข้อมูล:</strong> {len(pm25_grid):,}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    try:
                        deck = create_pm25_map()
                        st.pydeck_chart(deck)
                        
                        # 🔥 **แสดง legend**
                        current_color = st.session_state.complaint_color_selected
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; margin-top: 10px; flex-wrap: wrap;">
                            <div style="text-align: center; margin: 5px;">
                                <div style="width: 20px; height: 20px; background: linear-gradient(to right, #006837, #fee08b, #d73027); display: inline-block;"></div>
                                <div style="font-size: 12px;">PM2.5 Heatmap</div>
                            </div>
                            <div style="text-align: center; margin: 5px;">
                                <div style="width: 20px; height: 20px; background-color: rgb({current_color[0]},{current_color[1]},{current_color[2]}); border-radius: 50%; display: inline-block;"></div>
                                <div style="font-size: 12px;">จุดข้อร้องเรียน</div>
                            </div>
                            <div style="text-align: center; margin: 5px;">
                                <div style="width: 20px; height: 20px; background: url('https://tile.openstreetmap.org/10/0/0.png') center/cover; display: inline-block;"></div>
                                <div style="font-size: 12px;">แผนที่กรุงเทพฯ (OSM)</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการสร้างแผนที่: {str(e)}")
                        
                        # 🔥 **Fallback: แสดงแบบตาราง**
                        st.subheader("📋 ตารางแสดงพื้นที่ที่มี PM2.5 สูง")
                        top_areas = pm25_grid.sort_values('pm2_5', ascending=False).head(10)
                        st.dataframe(
                            top_areas[['lat_grid', 'lon_grid', 'pm2_5', 'point_count']].rename(
                                columns={
                                    'lat_grid': 'ละติจูด', 
                                    'lon_grid': 'ลองจิจูด', 
                                    'pm2_5': 'PM2.5 (µg/m³)', 
                                    'point_count': 'จำนวนจุด'
                                }
                            ),
                            use_container_width=True
                        )
                
                # 🔥 **แสดงข้อมูลสถิติ**
                st.markdown("---")
                st.subheader("📊 สถิติข้อมูล PM2.5")
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric("ค่า PM2.5 เฉลี่ย", f"{pm25_grid['pm2_5'].mean():.1f} µg/m³")
                    st.metric("จำนวนเซลล์กริด", f"{len(pm25_grid):,}")
                
                with col_stat2:
                    st.metric("ค่า PM2.5 สูงสุด", f"{pm25_grid['pm2_5'].max():.1f} µg/m³")
                    st.metric("ค่า PM2.5 ต่ำสุด", f"{pm25_grid['pm2_5'].min():.1f} µg/m³")
                
                with col_stat3:
                    # ระดับคุณภาพอากาศ
                    avg_pm25 = pm25_grid['pm2_5'].mean()
                    if avg_pm25 <= 15:
                        level = "🟢 ดี"
                    elif avg_pm25 <= 35:
                        level = "🟡 ปานกลาง"
                    elif avg_pm25 <= 50:
                        level = "🟠 เริ่มมีผลกระทบ"
                    elif avg_pm25 <= 100:
                        level = "🔴 อันตราย"
                    else:
                        level = "🔥 อันตรายมาก"
                    
                    st.metric("ระดับคุณภาพอากาศ", level)
                
                with col_stat4:
                    if complaints_filtered_copy is not None:
                        st.metric("จำนวนข้อร้องเรียน", f"{len(complaints_filtered_copy):,}")
                        if len(complaints_filtered_copy) > 0:
                            min_date = complaints_filtered_copy['timestamp_dt'].min().date()
                            max_date = complaints_filtered_copy['timestamp_dt'].max().date()
                            st.metric("ช่วงเวลา", f"{min_date} ถึง {max_date}")
                
                # 🔥 **แสดงพื้นที่เสี่ยง**
                with st.expander("🚨 ดูพื้นที่ที่มี PM2.5 สูงสุด", expanded=False):
                    top_areas = pm25_grid.sort_values('pm2_5', ascending=False).head(10)
                    
                    for idx, row in top_areas.iterrows():
                        pm25_level = row['pm2_5']
                        
                        # กำหนดสีตามระดับ
                        if pm25_level > 100:
                            color = "#8B0000"
                            emoji = "🔥"
                            level = "อันตรายมาก"
                        elif pm25_level > 50:
                            color = "#FF4500"
                            emoji = "⚠️"
                            level = "อันตราย"
                        elif pm25_level > 35:
                            color = "#FFA500"
                            emoji = "😷"
                            level = "เริ่มมีผลกระทบ"
                        elif pm25_level > 15:
                            color = "#FFD700"
                            emoji = "😐"
                            level = "ปานกลาง"
                        else:
                            color = "#228B22"
                            emoji = "✅"
                            level = "ดี"
                        
                        st.markdown(f"""
                        <div style='background-color: {color}15; padding: 10px; margin: 5px 0; 
                                    border-left: 4px solid {color}; border-radius: 3px;'>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{emoji} อันดับ {idx+1}: {pm25_level:.1f} µg/m³</strong><br>
                                    <small style="color: #666;">{level} | 📍 ({row['lat_grid']:.4f}, {row['lon_grid']:.4f})</small>
                                </div>
                                <div style="font-size: 12px; color: #666;">
                                    📊 {row['point_count']} จุดข้อมูล
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # 🔥 **ปุ่มรีเซ็ตแผนที่**
                col_reset, col_info = st.columns([1, 3])
                with col_reset:
                    if st.button("🔄 รีเซ็ตการตั้งค่าแผนที่", type="secondary"):
                        st.session_state.map_style_selected = "Light"
                        st.session_state.complaint_color_selected = [255, 0, 0]
                        st.rerun()
                
                with col_info:
                    st.info("💡 การตั้งค่าจะถูกบันทึกไว้ แม้จะรีเฟรชหน้า")
                    
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
                
                # สรุปข้อมูลข้อร้องเรียนตามเดือน
                if len(complaints_filtered) > 0:
                    complaints_monthly = complaints_filtered.groupby('month').size().reset_index(name='จำนวนข้อร้องเรียน')
                    
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
            st.dataframe(df[['timestamp_dt', 'type_exploded', 'district', 'organization', 'quarter', 'month']].head(10))
        
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