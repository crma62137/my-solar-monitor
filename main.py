import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from tuya_connector import TuyaOpenAPI
from streamlit_autorefresh import st_autorefresh
import os
import pytz
from datetime import datetime

# --- 1. การเชื่อมต่อระบบ ---
ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")

# รายชื่อรหัสอุปกรณ์ที่อัปเดตตามบัญชีของคุณแล้ว
DEVICES = {
    "PV Solar": "eb12a07e6d81bfad689phl",
    "Inverter": "eb366e7f16c29b4d66uoab",
    "PEA MAIN": "ebc4f09a8470bd323bkia0",
    "PEA 2": "ebe67840ae208eef35yseh" 
}

# รายชื่อ Endpoint ที่จะให้ระบบลองไล่เชื่อมต่อ (ถ้า US ไม่ติด จะไป EU หรือ CN อัตโนมัติ)
ENDPOINTS = [
    "https://openapi.tuyaus.com",
    "https://openapi.tuyaeu.com",
    "https://openapi.tuyacn.com"
]

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="My Solar Monitor", layout="wide")
st_autorefresh(interval=30 * 1000, key="solar_refresh")

# ฟังก์ชันดึงข้อมูลแบบ Advance (ลองหลาย Endpoint และดักรหัสค่าไฟฟ้า)
def get_tuya_data(device_id):
    result_data = {"watt": 0, "voltage": 0, "current": 0}
    
    for url in ENDPOINTS:
        try:
            openapi = TuyaOpenAPI(url, ACCESS_ID, ACCESS_SECRET)
            if not openapi.connect():
                continue
                
            response = openapi.get(f"/v1.0/devices/{device_id}/status")
            if response.get("success"):
                # ดึงรหัสทั้งหมดที่อุปกรณ์ส่งมา
                raw_status = {item["code"]: item["value"] for item in response["result"]}
                
                # --- ดักจับค่า WATT (ลองทุกชื่อที่เป็นไปได้) ---
                p_watt = (raw_status.get("cur_power") or 
                          raw_status.get("active_power") or 
                          raw_status.get("total_power") or 
                          raw_status.get("add_ele") or 0)
                
                # ถ้าค่ามาเป็นหลักหมื่น (เช่น 15470) ให้หาร 10 ตามมาตรฐานอุปกรณ์ Tuya
                if p_watt > 20000: p_watt = p_watt / 10
                result_data["watt"] = float(p_watt)

                # --- ดักจับค่า VOLTAGE ---
                v_raw = raw_status.get("cur_voltage") or raw_status.get("voltage") or 0
                result_data["voltage"] = float(v_raw) / 10 if v_raw > 0 else 0

                # --- ดักจับค่า CURRENT ---
                a_raw = raw_status.get("cur_current") or raw_status.get("current") or 0
                result_data["current"] = float(a_raw) / 1000 if a_raw > 0 else 0
                
                return result_data # ถ้าสำเร็จที่ Endpoint ไหนให้หยุดและส่งค่าเลย
        except:
            continue
    return result_data

# ฟังก์ชันสร้างรูปเกจ
def create_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': f"<b>{title}</b>", 'font': {'size': 18, 'color': 'white'}},
        number = {'suffix': " W", 'font': {'size': 24, 'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 5000], 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "#333333",
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig

# --- ส่วนการแสดงผล ---
st.markdown("<h2 style='text-align: center; color: #FFD700;'>☀️ MyHouseControl: Solar Dashboard</h2>", unsafe_allow_html=True)

tz = pytz.timezone('Asia/Bangkok')
now = datetime.now(tz).strftime('%H:%M:%S')
st.markdown(f"<p style='text-align: center; color: #AAAAAA;'>อัปเดตล่าสุด: {now}</p>", unsafe_allow_html=True)

cols = st.columns(4)
colors = ["#2ecc71", "#3498db", "#f39c12", "#e74c3c"]

for i, (name, dev_id) in enumerate(DEVICES.items()):
    data = get_tuya_data(dev_id)
    with cols[i]:
        st.plotly_chart(create_gauge(data["watt"], name, colors[i]), use_container_width=True)
        st.markdown(f"<p style='text-align:center; color: white;'>{data['voltage']:.1f}V | {data['current']:.2f}A</p>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("🏠 Home Control")
b1, b2, b3, b4 = st.columns(4)
b1.button("💡 Outdoor Lights", use_container_width=True)
b2.button("🚿 Water Pump", use_container_width=True)
b3.button("🍃 Eco Mode", use_container_width=True)
if b4.button("🔄 Refresh Data", use_container_width=True):
    st.rerun()
