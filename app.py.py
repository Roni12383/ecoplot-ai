import streamlit as st
import plotly_express as px
import requests
import folium
import numpy as np
from streamlit_folium import st_folium

# Imports from custom project files
from logic import calculate_metrics
from reporting import create_pdf_report
from chatbot import get_ai_response
from satellite_engine import get_real_ndvi, get_ndvi_time_series

st.set_page_config(page_title="EcoPlot AI", layout="wide")

if "actual_ndvi" not in st.session_state:
    st.session_state.actual_ndvi = 0.0

st.title("🌱 EcoPlot AI: Landscape Restoration Planner")

# --- SIDEBAR ---
st.sidebar.header("Farm Input Data")
lat = st.sidebar.number_input("Latitude", value=12.0022, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=8.5920, format="%.4f")
soil_carbon = st.sidebar.slider("Current Soil Carbon (%)", 0.1, 5.0, 1.2)

area, gdf = calculate_metrics(lat, lon)


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
c1, c2, c3 = st.columns(3)
c1.metric("Area", f"{area:.2f} Ha")
c2.metric("Rainfall (7d)", f"{rain} mm")
c3.metric("Temp", f"{temp} °C")

# --- MAP & SUSTAINABILITY ---
col_left, col_right = st.columns([2, 1])

with col_left:
    map_type = st.radio("View:", ["Street", "Satellite", "NDVI Heatmap"], horizontal=True)
    m = folium.Map(location=[lat, lon], zoom_start=17)

    if map_type != "Street":
        esri = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        folium.TileLayer(tiles=esri, attr="Esri").add_to(m)

    color = "#228B22" if map_type == "NDVI Heatmap" else "#3388ff"
    folium.GeoJson(gdf, style_function=lambda x: {'fillColor': color, 'color': 'white'}).add_to(m)
    st_folium(m, width=800, height=450)

with col_right:
    st.subheader("Sustainability")
    potential = (5.0 - soil_carbon) * area * 25
    st.write(f"**Carbon Potential:** {potential:.1f} Tons CO2e")

    if st.button("Generate Plan"):
        st.success("Plan Generated! Recommendation: Plant Acacia trees.")

    pdf_data = create_pdf_report("EcoPlot Project", area, potential)
    st.download_button("📄 Download ESG Report", data=pdf_data, file_name="Report.pdf")

# --- TRENDS ---
st.divider()
if st.button("Analyze Historical NDVI Trend"):
    df = get_ndvi_time_series(lat, lon)
    fig = px.line(df, x='date', y='NDVI', title="Vegetation Health Trend")
    st.plotly_chart(fig, use_container_width=True)

# --- SIDEBAR CHATBOT & NDVI ---
st.sidebar.divider()
if st.sidebar.button("Fetch Live NDVI"):
    val = get_real_ndvi(lat, lon)
    st.session_state.actual_ndvi = val
    st.sidebar.write(f"Current NDVI: {val:.2f}")

st.sidebar.subheader("🤖 EcoPlot AI Advisor")
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.sidebar.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.sidebar.chat_input("Ask about your farm..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.sidebar.chat_message("user"): st.markdown(prompt)

    metrics = {'lat': lat, 'lon': lon, 'area': area, 'rain': rain, 'ndvi': st.session_state.actual_ndvi}
    response = get_ai_response(prompt, metrics)

    with st.sidebar.chat_message("assistant"): st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
