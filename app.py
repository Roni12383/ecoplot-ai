import json
import requests
import streamlit as st
import plotly.express as px
import folium
import pandas as pd
import ee

from streamlit_folium import st_folium

# Custom modules
from logic import calculate_metrics
from reporting import create_pdf_report
from chatbot import get_ai_response
from satellite_engine import get_real_ndvi, get_ndvi_time_series

CARBON_COEFFICIENT = 35.0

st.set_page_config(page_title="EcoPlot AI", page_icon="🌱", layout="wide")

# -----------------------------
# SESSION STATE INITIALIZATION
# -----------------------------
default_session_values = {
    "current_ndvi_value": 0.0,
    "carbon_tons_calculated": 0.0,
    "pdf_report": None,
    "ndvi_time_series_df": pd.DataFrame(columns=["date", "NDVI"]),
    "actual_ndvi": 0.0,
    "messages": [],
}

for key, value in default_session_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------
# EARTH ENGINE INITIALIZATION
# -----------------------------
try:
    info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    credentials = ee.ServiceAccountCredentials(
        info["client_email"],
        key_data=st.secrets["GCP_SERVICE_ACCOUNT"]
    )
    ee.Initialize(credentials, project=info["project_id"])
except Exception as e:
    st.error(f"Earth Engine initialization failed: {e}")
    st.stop()

st.title("🌱 EcoPlot AI: Landscape Restoration Planner")

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.header("Farm Input Data")

lat = st.sidebar.number_input("Latitude", value=12.0022, format="%.4f")
lon = st.sidebar.number_input("Longitude", value=8.5920, format="%.4f")
soil_carbon = st.sidebar.slider("Current Soil Carbon (%)", 0.1, 5.0, 1.2)
farm_name = st.sidebar.text_input("Farm Name", "EcoPlot Project")
area_ha = st.sidebar.number_input("Hectares", min_value=0.1, value=10.0, step=0.1)

# Calculate geometry-based area/polygon using the user-entered area
try:
    calculated_area_ha, gdf = calculate_metrics(lat, lon, area_ha)
except Exception as e:
    st.error(f"Failed to calculate area/geometry: {e}")
    st.stop()

# -----------------------------
# WEATHER DATA
# -----------------------------
def get_weather_data(lat_value, lon_value):
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat_value}&longitude={lon_value}"
            "&daily=precipitation_sum,temperature_2m_max"
            "&timezone=auto"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        rain_7d = sum(data["daily"]["precipitation_sum"][:7])
        temp_today = data["daily"]["temperature_2m_max"][0]
        return rain_7d, temp_today
    except Exception as e:
        st.warning(f"Weather data unavailable: {e}")
        return 0.0, 0.0

rain, temp = get_weather_data(lat, lon)

# -----------------------------
# HEADER METRICS
# -----------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Target Area", f"{area_ha:.2f} Ha")
c2.metric("Calculated Area", f"{calculated_area_ha:.2f} Ha")
c3.metric("Rainfall (7d)", f"{rain:.1f} mm")

c4, _ = st.columns([1, 2])
c4.metric("Temp", f"{temp:.1f} °C")

# -----------------------------
# MAP & RIGHT PANEL
# -----------------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    map_type = st.radio("View:", ["Street", "Satellite", "NDVI Heatmap"], horizontal=True)

    m = folium.Map(location=[lat, lon], zoom_start=17)

    if map_type != "Street":
        esri = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        )
        folium.TileLayer(tiles=esri, attr="Esri").add_to(m)

    color = "#228B22" if map_type == "NDVI Heatmap" else "#3388ff"

    folium.GeoJson(
        gdf,
        style_function=lambda x: {
            "fillColor": color,
            "color": "white",
            "weight": 2,
            "fillOpacity": 0.5
        }
    ).add_to(m)

    st_folium(m, width=800, height=450)

with col_right:
    st.subheader("Sustainability")

    potential = (5.0 - soil_carbon) * area_ha * 25
    st.write(f"**Carbon Potential:** {potential:.1f} Tons CO2e")

    if st.button("Generate Plan"):
        st.success("Plan Generated! Recommendation: Plant Acacia trees.")
        
    #    2. Historical NDVI
df_trends = get_ndvi_time_series(lat, lon)

# ✅ Check for None, empty, and missing column
if df_trends is None or df_trends.empty or "NDVI" not in df_trends.columns:
    st.warning("⚠️ No historical satellite data found for this location.")
    df_trends = pd.DataFrame(columns=["date", "NDVI"])
else:
    # ✅ Drop NaN NDVI rows before doing anything
    df_trends = df_trends.dropna(subset=["NDVI"])

    # ✅ After dropping NaN, check again if anything is left
    if df_trends.empty:
        st.warning("⚠️ Satellite data was found but all NDVI values were empty.")

st.session_state.ndvi_time_series_df = df_trends

# 3. Compute average NDVI and growth rate
if not df_trends.empty and "NDVI" in df_trends.columns:
    recent_data = df_trends.tail(12).copy()

    # ✅ Drop any remaining NaN values
    recent_data = recent_data.dropna(subset=["NDVI"])

    # ✅ Only calculate if there is valid data
    if not recent_data.empty:
        avg_annual_ndvi = float(recent_data["NDVI"].mean())
    else:
        avg_annual_ndvi = float(current_ndvi) if current_ndvi else 0.0

    if len(recent_data) >= 6:
        split_index = len(recent_data) // 2
        first_half_mean = float(recent_data.iloc[:split_index]["NDVI"].mean())
        second_half_mean = float(recent_data.iloc[split_index:]["NDVI"].mean())

        # ✅ Check both halves are valid before dividing
        if first_half_mean > 0 and not pd.isna(first_half_mean) and not pd.isna(second_half_mean):
            growth_rate = (second_half_mean - first_half_mean) / first_half_mean
        else:
            growth_rate = 0.0
    else:
        growth_rate = 0.0

else:
    # ✅ Safe fallback
    avg_annual_ndvi = float(current_ndvi) if current_ndvi else 0.0
    growth_rate = 0.0

   

 # 4. Carbon estimation
    carbon_tons = area_ha * avg_annual_ndvi * CARBON_COEFFICIENT
    st.session_state.carbon_tons_calculated = carbon_tons

 # 5. Create PDF report
 st.session_state.pdf_report = create_pdf_report( farm_name=farm_name,
     area=area_ha, carbon_tons=carbon_tons, growth_rate=growth_rate, avg_ndvi=avg_annual_ndvi, current_ndvi=current_ndvi )

  st.success("✅ Analysis Complete! Report generated successfully.")
  st.info(
  f"Current NDVI: {current_ndvi:.3f} | "
  f"Avg NDVI: {avg_annual_ndvi:.3f} | "
  f"Growth Rate: {growth_rate * 100:.1f}% | "
  f"Carbon: {carbon_tons:.2f} Tons CO2e")

 except Exception as e:
 st.error(f"Analysis failed: {e}")

    if st.session_state.pdf_report is not None:
        st.download_button(
            label="📄 Download ESG Report",
            data=st.session_state.pdf_report,
            file_name="EcoPlot_Report.pdf",
            mime="application/pdf"
        )

# -----------------------------
# NDVI TREND CHART
# -----------------------------
st.subheader("Historical NDVI Trend")

if st.button("Analyze Historical NDVI Trend"):
    try:
        df = get_ndvi_time_series(lat, lon)

        if df is not None and not df.empty:
            fig = px.line(
                df,
                x="date",
                y="NDVI",
                title="Vegetation Health Trend",
                markers=True
            )
            fig.update_layout(xaxis_title="Date", yaxis_title="NDVI")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No clear satellite data found for this location in the last 2 years.")
    except Exception as e:
        st.error(f"Trend analysis failed: {e}")

# -----------------------------
# SIDEBAR NDVI + CHATBOT
# -----------------------------
st.sidebar.divider()

if st.sidebar.button("Fetch Live NDVI"):
    try:
        val = get_real_ndvi(lat, lon)
        st.session_state.actual_ndvi = val
        st.sidebar.write(f"Current NDVI: {val:.2f}")
    except Exception as e:
        st.sidebar.error(f"Failed to fetch NDVI: {e}")

st.sidebar.subheader("🤖 EcoPlot AI Advisor")

for msg in st.session_state.messages:
    with st.sidebar.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.sidebar.chat_input("Ask about your farm..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.sidebar.chat_message("user"):
        st.markdown(prompt)

    metrics = {
        "lat": lat,
        "lon": lon,
        "area": area_ha,
        "rain": rain,
        "temp": temp,
        "soil_carbon": soil_carbon,
        "ndvi": st.session_state.actual_ndvi,
        "current_ndvi": st.session_state.current_ndvi_value,
        "calculated_area": calculated_area_ha,
        "carbon_tons": st.session_state.carbon_tons_calculated,
    }

    try:
        response = get_ai_response(prompt, metrics)
    except Exception as e:
        response = f"Sorry, I couldn't process that request right now. Error: {e}"

    with st.sidebar.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
