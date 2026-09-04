import streamlit as st
import plotly_express as px
import requests
import folium
import numpy as np
import ee
import pandas as pd
import json
import streamlit.components.v1 as components
from streamlit_folium import st_folium

# Imports from custom project files
from logic import calculate_metrics
from reporting import create_pdf_report
from chatbot import get_ai_response
from satellite_engine import get_real_ndvi, get_ndvi_time_series


def big_text(text, size="17px"):
    st.markdown(f'<p style="font-size:{size}; line-height:1.7;">{text}</p>', unsafe_allow_html=True)

def big_title(text, size="32px"):
    st.markdown(f'<h1 style="font-size:{size}; font-weight:600;">{text}</h1>', unsafe_allow_html=True)

info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
credentials = ee.ServiceAccountCredentials(info['client_email'], key_data=st.secrets["GCP_SERVICE_ACCOUNT"])
ee.Initialize(credentials, project=info['project_id'])

st.set_page_config(page_title="EcoPlot AI", page_icon="🌱", layout="wide")

if "actual_ndvi" not in st.session_state:
    st.session_state.actual_ndvi = 0.0
if "pdf_report" not in st.session_state:
    st.session_state.pdf_report = None
if "ndvi_time_series_df" not in st.session_state:
    st.session_state.ndvi_time_series_df = pd.DataFrame(columns=['date', 'NDVI'])

big_title("🌱 EcoPlot AI: Landscape Restoration Planner", "55px")

# 1. GET KEY FROM STREAMLIT SECRETS
api_key = st.secrets["XEELAA_API_KEY"]

# 2. EXAMPLE: CALL XEELAA CHATBOT API
def ask_xeelaa(user_message, language="Hausa"):
    url = "https://api.xeelaa.ai/v1/chat" # replace with your real Xeelaa endpoint
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": user_message,
        "language": language,
        "assistant_name": "Xeelaa - Jigawa Farm Assistant"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()["reply"]

# 3. USE IT IN STREAMLIT
big_title("Xeelaa - EcoPlotAI Assistant", "22px")
user_input = st.text_input("Ask Xeelaa something in Hausa or English")

if user_input:
    with st.spinner("Xeelaa is thinking..."):
        answer = ask_xeelaa(user_input)
        big_text(answer, "20px") # FIXED: was big_write

# --- SIDEBAR ---
st.sidebar.header("Farm Input Data")
lat = st.sidebar.number_input("Latitude", value=12.0022, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=8.5920, format="%.4f")
soil_carbon = st.sidebar.slider("Current Soil Carbon (%)", 0.1, 5.0, 1.2)
farm_name = st.sidebar.text_input("Farm Name", "EcoPlot Project")
area_input = st.sidebar.number_input("Hectares for Analysis", value=1.0, min_value=0.1) # User can override 1ha

# --- GET METRICS FROM NEW LOGIC.PY ---
with st.spinner("Calculating metrics..."):
    metrics = calculate_metrics(lat, lon, ndvi_mean=st.session_state.actual_ndvi)
area = metrics["area_ha"]
gdf = metrics["geometry_1ha_geojson"]

# --- WEATHER DATA ---
def get_weather_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
        res = requests.get(url).json()
        return sum(res['daily']['precipitation_sum'][:7]), res['daily']['temperature_2m_max'][0]
    except:
        return 0, 0

rain, temp = get_weather_data(lat, lon)

# --- HEADER METRICS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Area", f"{area:.2f} Ha")
c2.metric("Carbon", f"{metrics['carbon']['carbon_stock_tCO2e']} tCO2e")
c3.metric("ESG Score", f"{metrics['sustainability']['esg_score']}")
c4.metric("Rainfall 7d", f"{rain} mm")

# --- MAP & SUSTAINABILITY ---
col_left, col_right = st.columns([2, 1])

with col_left:
    map_type = st.radio("View:", ["Street", "Satellite", "NDVI Heatmap", "Buffers"], horizontal=True)
    m = folium.Map(location=[lat, lon], zoom_start=15)

    if map_type!= "Street":
        esri = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        folium.TileLayer(tiles=esri, attr="Esri").add_to(m)

    # Main 1ha plot
    folium.GeoJson(gdf, name="1 Hectare", style_function=lambda x: {'fillColor': "#228B22", 'color': 'white', 'weight': 2}).add_to(m)
    
    # Show buffers if selected
    if map_type == "Buffers":
        for name, geojson in metrics["buffers_geojson"].items():
            folium.GeoJson(geojson, name=name, style_function=lambda x: {'fillOpacity': 0, 'color': 'red'}).add_to(m)

    st_folium(m, width=800, height=450)

with col_right:
    st.subheader("Sustainability & ESG")
    st.write(f"**Vegetation Health:** {metrics['sustainability']['vegetation_health']}")
    st.write(f"**Degradation Risk:** {metrics['sustainability']['risk_level']}")
    st.write(f"**Carbon Stock:** {metrics['carbon']['carbon_stock_tCO2e']} tCO2e")
    st.write(f"**Coords:** {lat:.4f}, {lon:.4f}")

    if st.button("Generate Plan"):
        st.success("Recommendation: Plant Acacia trees in low NDVI zones.")

    # --- NEW: REPORT GENERATION TOGGLE ---
    report_type = st.radio("Report Type", ["1-Page SAMPLE", "FULL Report"], horizontal=True)
    
    if st.button("Analyze Farm & Generate Report"):
        with st.spinner("Analyzing..."):
            # 1. Fetch live NDVI
            st.session_state.actual_ndvi = get_real_ndvi(lat, lon, area_input)
            metrics = calculate_metrics(lat, lon, ndvi_mean=st.session_state.actual_ndvi) # Recalculate with live NDVI

            # 2. Generate the PDF with new metrics
            st.session_state.pdf_report = create_pdf_report(
                farm_name=farm_name,
                metrics=metrics, # Pass full dict now
                report_type=report_type # SAMPLE or FULL
            )

            # 3. Fetch the time series
            st.session_state.ndvi_time_series_df = get_ndvi_time_series(lat, lon)

        st.success("✅ Analysis Complete!")

    if st.session_state.pdf_report is not None:
        file_name = "SIRA_Sample_Report.pdf" if report_type == "1-Page SAMPLE" else "SIRA_Full_Report.pdf"
        st.download_button(
            label="📄 Download Report",
            data=bytes(st.session_state.pdf_report),
            file_name=file_name,
            mime="application/pdf"
        )

# --- TRENDS ---
if st.button("Analyze Historical NDVI Trend"):
    df = get_ndvi_time_series(lat, lon)
    if df is not None and not df.empty:
        fig = px.line(df, x='date', y='NDVI', title="Vegetation Health Trend")
        st.plotly_chart(fig)
    else:
        st.warning("No clear satellite data found for this location in the last 2 years.")

# --- SIDEBAR CHATBOT & NDVI ---
st.sidebar.divider()
if st.sidebar.button("Fetch Live NDVI"):
    val = get_real_ndvi(lat, lon, area_input)
    st.session_state.actual_ndvi = val
    st.sidebar.write(f"Current NDVI: {val:.2f}")

st.sidebar.subheader("🤖 EcoPlot AI Advisor")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.sidebar.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.sidebar.chat_input("Ask about your farm..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.sidebar.chat_message("user"): st.markdown(prompt)

    metrics_for_ai = {'lat': lat, 'lon': lon, 'area': area, 'rain': rain, 'ndvi': st.session_state.actual_ndvi}
    response = get_ai_response(prompt, metrics_for_ai)

    with st.sidebar.chat_message("assistant"): st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})


# ================= XEELAA EMBED - DO NOT REMOVE =================
# Required for Startup Abuja Innovation Challenge
components.html("""<script>
  window.__EMBED_CONFIG__ = {
    publicToken: "v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ",
    // baseUrl: "https://xeelaa.com",
    getUserToken: function() {
      return document.querySelector("meta[name=user-token]")?.content || null;
    },
    getUserId: function() {
      return document.querySelector("meta[name=user-id]")?.content || null;
    },
    getUserName: function() {
      return document.querySelector("meta[name=user-name]")?.content || null;
    },
    getUserEmail: function() {
      return document.querySelector("meta[name=user-email]")?.content || null;
    },
    getUserRole: function() {
      return document.querySelector("meta[name=user-role]")?.content || null;
    }
  };
</script>
<script src="https://xeelaa.com/widget.js?key=v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ"></script>
""", height=0, width=0)
# =================================================================

