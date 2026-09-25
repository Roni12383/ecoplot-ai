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
import zipfile, tempfile, os
import geopandas as gpd
from pyproj import Geod

# Imports from custom project files
from logic import calculate_metrics
from reporting import create_pdf_report
from chatbot import get_ai_response
from satellite_engine import get_real_ndvi, get_ndvi_time_series

def calculate_true_hectares(geojson_geom):
    geod = Geod(ellps="WGS84")
    if geojson_geom["type"] == "Polygon":
        lons = [c[0] for c in geojson_geom["coordinates"][0]]
        lats = [c[1] for c in geojson_geom["coordinates"][0]]
        a, _ = geod.polygon_area_perimeter(lons, lats)
        return abs(a) / 10000
    return 1.0

def big_text(text, size="17px"):
    st.markdown(f'<p style="font-size:{size}; line-height:1.7;">{text}</p>', unsafe_allow_html=True)

def big_title(text, size="32px"):
    st.markdown(f'<h1 style="font-size:{size}; font-weight:600;">{text}</h1>', unsafe_allow_html=True)

info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
credentials = ee.ServiceAccountCredentials(info['client_email'], key_data=st.secrets["GCP_SERVICE_ACCOUNT"])
ee.Initialize(credentials, project=info['project_id'])

st.set_page_config(page_title="EcoPlot AI", page_icon="🌱", layout="wide")
if "actual_ndvi" not in st.session_state: st.session_state.actual_ndvi = 0.0
if "pdf_report" not in st.session_state: st.session_state.pdf_report = None
if "ndvi_time_series_df" not in st.session_state:
    st.session_state.ndvi_time_series_df = pd.DataFrame(columns=['date', 'NDVI'])

big_title("🌱 EcoPlot AI: Landscape Restoration Planner", "55px")

# 1. GET KEY FROM STREAMLIT SECRETS
api_key = st.secrets["XEELAA_API_KEY"]

# 2. XEELAA CHATBOT API
def ask_xeelaa(user_message, language="Hausa"):
    url = "https://api.xeelaa.ai/v1/chat"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"message": user_message, "language": language, "assistant_name": "Xeelaa - Jigawa Farm Assistant"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.json().get("reply", "Sorry, Xeelaa is offline")
    except:
        return "Xeelaa connection error"

big_title("Xeelaa - EcoPlotAI Assistant", "22px")
user_input = st.text_input("Ask Xeelaa something in Hausa or English")
if user_input:
    with st.spinner("Xeelaa is thinking..."):
        answer = ask_xeelaa(user_input)
        big_text(answer, "20px")

# --- SIDEBAR WITH DYNAMIC HECTARE ---
st.sidebar.header("Farm Input Data")

input_method = st.sidebar.radio("Boundary Input Type",
    ["Single Point (Lat/Lon)", "Enter Coordinates List", "Upload Shapefile.zip"])

farm_name = st.sidebar.text_input("Farm Name", "EcoPlot Project")
soil_carbon = st.sidebar.slider("Current Soil Carbon (%)", 0.1, 5.0, 1.2)

lat = st.sidebar.number_input("Latitude", value=12.0022, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=8.5920, format="%.4f")

# DYNAMIC HECTARE INPUT - THIS FIXES YOUR 1ha STATIC BUG
area_input = st.sidebar.number_input("Hectares for Analysis", value=1.0, min_value=0.1, max_value=1000.0, step=0.5)
st.sidebar.caption(f"Will generate exactly {area_input} ha")

custom_geojson = None
final_area_ha = area_input

if input_method == "Enter Coordinates List":
    st.sidebar.info("Paste lon,lat per line")
    coords_text = st.sidebar.text_area("Coordinates", "8.432, 11.051\n8.435, 11.051\n8.435, 11.048\n8.432, 11.048")
    try:
        coords = []
        for line in coords_text.strip().split('\n'):
            if ',' in line:
                lon_c, lat_c = map(float, line.split(','))
                coords.append([lon_c, lat_c])
        if coords and coords[0]!= coords[-1]:
            coords.append(coords[0])
        if len(coords) >= 4:
            custom_geojson = {"type": "Polygon", "coordinates": [coords]}
            final_area_ha = calculate_true_hectares(custom_geojson)
            st.sidebar.success(f"Polygon Area: {final_area_ha:.3f} ha (calculated)")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

elif input_method == "Upload Shapefile.zip":
    uploaded_zip = st.sidebar.file_uploader("Upload ZIP with.shp.shx.dbf.prj", type=['zip'])
    if uploaded_zip:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            shp_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith('.shp')]
            if shp_files:
                gdf = gpd.read_file(shp_files[0]).to_crs(epsg=4326)
                custom_geojson = json.loads(gdf.to_json())['features'][0]['geometry']
                final_area_ha = calculate_true_hectares(custom_geojson)
                st.sidebar.success(f"Shapefile: {final_area_ha:.3f} ha")

# --- GET METRICS WITH CORRECT HECTARE ---
with st.spinner("Calculating metrics..."):
    # Pass area_input to logic.py so 2ha = 2ha
    metrics = calculate_metrics(lat, lon, ndvi_mean=st.session_state.actual_ndvi, hectares=area_input, custom_geojson=custom_geojson)

area = metrics["area_ha"]
gdf = metrics["geometry_1ha_geojson"]

# --- WEATHER ---
def get_weather_data(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=auto"
        res = requests.get(url).json()
        return sum(res['daily']['precipitation_sum'][:7]), res['daily']['temperature_2m_max'][0]
    except: return 0, 0
rain, temp = get_weather_data(lat, lon)

# --- HEADER METRICS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Area (True)", f"{area:.3f} Ha")
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
    folium.GeoJson(gdf, name=f"{area} Hectare", style_function=lambda x: {'fillColor': "#228B22", 'color': 'white', 'weight': 2}).add_to(m)
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

# --- REPORT GENERATION ---
report_type = st.radio("Report Type", ["1-Page SAMPLE", "FULL Report"], horizontal=True)
if st.button("Analyze Farm & Generate Report"):
    with st.spinner("Analyzing..."):
        st.session_state.actual_ndvi = get_real_ndvi(lat, lon, area)
        metrics = calculate_metrics(lat, lon, ndvi_mean=st.session_state.actual_ndvi, hectares=area_input, custom_geojson=custom_geojson)
        st.session_state.pdf_report = create_pdf_report(farm_name=farm_name, metrics=metrics, report_type=report_type)
        st.session_state.ndvi_time_series_df = get_ndvi_time_series(lat, lon)
    st.success("✅ Analysis Complete!")
    if st.session_state.pdf_report is not None:
        file_name = "SIRA_Sample_Report.pdf" if report_type == "1-Page SAMPLE" else "SIRA_Full_Report.pdf"
        st.download_button(label="📄 Download Report", data=bytes(st.session_state.pdf_report), file_name=file_name, mime="application/pdf")

# --- HISTORICAL TRENDS - BROUGHT BACK ---
st.divider()
st.subheader("📈 Historical Vegetation Trend")
if st.button("Analyze Historical NDVI Trend"):
    df = get_ndvi_time_series(lat, lon)
    if df is not None and not df.empty:
        fig = px.line(df, x='date', y='NDVI', title="Vegetation Health Trend (Last 2 Years)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No clear satellite data found for this location in the last 2 years.")

# --- SIDEBAR CHATBOT & NDVI - BROUGHT BACK ---
st.sidebar.divider()
if st.sidebar.button("Fetch Live NDVI"):
    val = get_real_ndvi(lat, lon, area)
    st.session_state.actual_ndvi = val
    st.sidebar.write(f"Current NDVI: {val:.2f}")

st.sidebar.subheader("🤖 EcoPlot AI Advisor")
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.sidebar.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.sidebar.chat_input("Ask about your farm..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.sidebar.chat_message("user"):
        st.markdown(prompt)
    metrics_for_ai = {'lat': lat, 'lon': lon, 'area': area, 'rain': rain, 'ndvi': st.session_state.actual_ndvi}
    response = get_ai_response(prompt, metrics_for_ai)
    with st.sidebar.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# ================= XEELAA EMBED - DO NOT REMOVE =================
components.html("""<script>
 window.__EMBED_CONFIG__ = {
 publicToken: "v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ",
 getUserToken: function() { return document.querySelector("meta[name=user-token]")?.content || null; },
 getUserId: function() { return document.querySelector("meta[name=user-id]")?.content || null; },
 getUserName: function() { return document.querySelector("meta[name=user-name]")?.content || null; },
 getUserEmail: function() { return document.querySelector("meta[name=user-email]")?.content || null; },
 getUserRole: function() { return document.querySelector("meta[name=user-role]")?.content || null; }
 };
</script>
<script src="https://xeelaa.com/widget.js?key=v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ"></script>
""", height=0, width=0)
