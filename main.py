import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from tuya_connector import TuyaOpenAPI
import os
import pytz
from datetime import datetime

# --- 1. ตั้งค่าการเชื่อมต่อ (ดึงจาก Fly.io Secrets) ---
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
# สำหรับประเทศไทย แนะนำให้ลองใช้ Endpoint นี้ครับ
API_ENDPOINT = "https://openapi.tuyacn.com" 

# --- 2. ฟังก์ชันดึงข้อมูลสถานะอุปกรณ์จาก Tuya ---
def get_tuya_status(device_id):
    try:
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_SECRET)
        openapi.connect()
        response = openapi.get(f"/v1.0/devices/{device_id}/status")
        if response.get("success"):
            # แปลงรูปแบบข้อมูลให้อ่านง่าย
            return {item["code"]: item["value"] for item in response["result"]}
        return {}
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
        return {}

# --- 3. ฟังก์ชันสร้าง Gauge สวยๆ ด้วย Plotly ---
def create_gauge(value, title, color, unit="W", max_val=5000):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 20}},
        number = {'suffix': f" {unit}", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [0, max_val], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "#e0e0e0",
            'steps': [
                {'range': [0, max_val*0.2], 'color': "#f0f0f0"},
                {'range': [max_val*0.8, max_val], 'color': "#fdf2f2"}
            ],
        }
    ))
    fig.update_layout(height=280, margin=dict(l=30, r=30, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
    return fig

# --- 4. ส่วนแสดงผลบนหน้าเว็บ (UI) ---
st.set_page_config(page_title="Solar Monitoring Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center;'>☀️ Smart Solar Energy Dashboard</h1>", unsafe_allow_html=True)

# จัดการเรื่องเวลาไทย
tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz)
st.markdown(f"<p style='text-align: center; color: gray;'>อัปเดตล่าสุด: {now.strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)

# --- 5. การดึงข้อมูลจริง (คุณต้องแทนที่ DEVICE_ID_... ด้วย ID จริงจาก Tuya) ---
# ตัวอย่าง:
# data_pv = get_tuya_status("DEVICE_ID_ของ_PV_SOLAR")
# power_pv = data_pv.get("cur_power", 0) / 10 # ตัวอย่างการหารทศนิยม

# สำหรับตัวอย่างนี้ ผมใส่ค่าคงที่ไว้ให้เห็น Layout ก่อนครับ:
power_pv = 490
power_inv = 440
power_pea1 = 10
power_pea2 = 10

# แบ่ง 4 คอลัมน์สำหรับ Gauge 4 ตัว
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.plotly_chart(create_gauge(power_pv, "PV Solar", "#2ecc71"), use_container_width=True)
    st.metric("Voltage", "399.07 V")

with col2:
    st.plotly_chart(create_gauge(power_inv, "Inverter", "#3498db"), use_container_width=True)
    st.metric("Today's Yield", "0.05 kWh")

with col3:
    st.plotly_chart(create_gauge(power_pea1, "PEA MAIN", "#e67e22"), use_container_width=True)
    st.metric("Current", "0.114 A")

with col4:
    st.plotly_chart(create_gauge(power_pea2, "PEA 2", "#e74c3c"), use_container_width=True)
    st.metric("Voltage", "234.8 V")

# --- 6. กราฟเส้นแสดงแนวโน้ม (Trend) ---
st.markdown("---")
st.subheader("📊 Real-time Power Trends (30s refresh)")

# สร้างข้อมูลจำลองสำหรับกราฟ
chart_data = pd.DataFrame({
    'Time': [now.strftime('%H:%M:%S') for _ in range(5)],
    'PV Power': [480, 485, 490, 488, 492],
    'Inverter': [430, 435, 440, 438, 442]
})
st.line_chart(chart_data.set_index('Time'))
