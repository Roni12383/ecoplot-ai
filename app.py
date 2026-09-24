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
from shapely.geometry import shape
from pyproj import Geod
import geopandas as gpd

# Imports from custom project files
from logic import calculate_metrics
from reporting import create_pdf_report
from chatbot import get_ai_response
from satellite_engine import get_real_ndvi, get_ndvi_time_series

# --- CORRECT HECTARE CALCULATION ---
def calculate_true_hectares(geojson_geom):
    geod = Geod(ellps="WGS84")
    area_m2 = 0
    if geojson_geom["type"] == "Polygon":
        lons = [c[0] for c in geojson_geom["coordinates"][0]]
        lats = [c[1] for c in geojson_geom["coordinates"][0]]
        a, _ = geod.polygon_area_perimeter(lons, lats)
        area_m2 = abs(a)
    elif geojson_geom["type"] == "MultiPolygon":
        for poly in geojson_geom["coordinates"]:
            lons = [c[0] for c in poly[0]]
            lats = [c[1] for c in poly[0]]
            a, _ = geod.polygon_area_perimeter(lons, lats)
            area_m2 += abs(a)
    return round(area_m2 / 10000, 3)

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

# --- SIDEBAR - NEW INPUT OPTIONS ---
st.sidebar.header("Farm Input Data")

input_method = st.sidebar.radio("Boundary Input Type",
    ["Single Point (Lat/Lon) - Auto 1ha", "Enter Coordinates List", "Upload Shapefile.zip"],
    index=0)

farm_name = st.sidebar.text_input("Farm Name", "EcoPlot Project")
soil_carbon = st.sidebar.slider("Current Soil Carbon (%)", 0.1, 5.0, 1.2)

lat = lon = None
custom_geojson = None
area_ha_final = 1.0

if input_method == "Single Point (Lat/Lon) - Auto 1ha":
    lat = st.sidebar.number_input("Latitude", value=12.0022, format="%.4f")
    lon = st.sidebar.number_input("Longitude", value=8.5920, format="%.4f")
    area_ha_final = st.sidebar.number_input("Hectares for Analysis", value=1.0, min_value=0.1)

elif input_method == "Enter Coordinates List":
    st.sidebar.info("Paste lon,lat - one per line")
    coords_text = st.sidebar.text_area("Coordinates",
        "8.432, 11.051\n8.435, 11.051\n8.435, 11.048\n8.432, 11.048")
    lat = st.sidebar.number_input("Center Lat (for weather)", value=12.0022, format="%.4f")
    lon = st.sidebar.number_input("Center Lon (for weather)", value=8.5920, format="%.4f")
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
            area_ha_final = calculate_true_hectares(custom_geojson)
            st.sidebar.success(f"Calculated: {area_ha_final} ha")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

else: # Shapefile
    uploaded_zip = st.sidebar.file_uploader("Upload ZIP with.shp.shx.dbf.prj", type=['zip'])
    lat = st.sidebar.number_input("Center Lat (for weather)", value=12.0022, format="%.4f")
    lon = st.sidebar.number_input("Center Lon (for weather)", value=8.5920, format="%.4f")
    if uploaded_zip:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            shp_files = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith('.shp')]
            if shp_files:
                gdf = gpd.read_file(shp_files[0]).to_crs(epsg=4326)
                custom_geojson = json.loads(gdf.geometry.iloc[0].__geo_interface__['geometry'] if hasattr(gdf.geometry.iloc[0], '__geo_interface__') else gdf.geometry.iloc[0].to_json()) if False else gpd.GeoSeries(gdf.geometry).to_json()
                # simpler:
                custom_geojson = json.loads(gdf.to_json())['features'][0]['geometry']
                area_ha_final = calculate_true_hectares(custom_geojson)
                st.sidebar.success(f"Shapefile Area: {area_ha_final} ha - {gdf.shape[0]} polygon(s)")

# --- GET METRICS ---
with st.spinner("Calculating metrics..."):
    if custom_geojson:
        # If custom polygon, still call calculate_metrics with center lat/lon but override area
        # Change this line in app.py
        metrics = calculate_metrics(lat, lon, ndvi_mean=..., custom_geojson=custom_geojson)
        metrics["area_ha"] = area_ha_final # CORRECT hectare overwrite
        metrics["geometry_1ha_geojson"] = custom_geojson
        # Recalculate carbon based on TRUE area
        ndvi = metrics['carbon']['ndvi_mean']
        metrics['carbon']['carbon_stock_tCO2e'] = round(area_ha_final * ndvi * 5.2 * 3.67, 2)
        metrics['carbon']['per_hectare_tCO2e'] = round(ndvi * 5.2 * 3.67, 2)
    else:
        metrics = calculate_metrics(lat, lon, ndvi_mean=st.session_state.actual_ndvi)

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
c1.metric("Area (True Geodesic)", f"{area:.3f} Ha")
c2.metric("Carbon", f"{metrics['carbon']['carbon_stock_tCO2e']} tCO2e")
c3.metric("ESG Score", f"{metrics['sustainability']['esg_score']}")
c4.metric("Rainfall 7d", f"{rain} mm")

#... rest of your code stays same from map onwards...
col_left, col_right = st.columns([2, 1])
with col_left:
    map_type = st.radio("View:", ["Street", "Satellite", "NDVI Heatmap", "Buffers"], horizontal=True)
    m = folium.Map(location=[lat, lon], zoom_start=15)
    if map_type!= "Street":
        esri = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        folium.TileLayer(tiles=esri, attr="Esri").add_to(m)
    folium.GeoJson(gdf, name="1 Hectare", style_function=lambda x: {'fillColor': "#228B22", 'color': 'white', 'weight': 2}).add_to(m)
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

report_type = st.radio("Report Type", ["1-Page SAMPLE", "FULL Report"], horizontal=True)
if st.button("Analyze Farm & Generate Report"):
    with st.spinner("Analyzing..."):
        st.session_state.actual_ndvi = get_real_ndvi(lat, lon, area)
        metrics = calculate_metrics(lat, lon, ndvi_mean=st.session_state.actual_ndvi)
        if custom_geojson:
            metrics["area_ha"] = area_ha_final
            metrics["geometry_1ha_geojson"] = custom_geojson
        st.session_state.pdf_report = create_pdf_report(farm_name=farm_name, metrics=metrics, report_type=report_type)
        st.session_state.ndvi_time_series_df = get_ndvi_time_series(lat, lon)
    st.success("✅ Analysis Complete!")
    if st.session_state.pdf_report is not None:
        file_name = "SIRA_Sample_Report.pdf" if report_type == "1-Page SAMPLE" else "SIRA_Full_Report.pdf"
        st.download_button(label="📄 Download Report", data=bytes(st.session_state.pdf_report), file_name=file_name, mime="application/pdf")
