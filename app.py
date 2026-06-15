import streamlit as st
import ee
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import math # Needed for calculate_buffer_radius if not in utils.py
import os # For checking logo.png existence in PDF report

# Import helper functions

# If create_pdf_report is in reporting.py:
# from reporting import create_pdf_report 


# --- Streamlit Page Configuration ---
st.set_page_config(page_title="EcoPlot AI", page_icon="🌱", layout="wide")

# --- Google Earth Engine Initialization ---
# This block handles authentication for both local (earthengine authenticate) and cloud (secrets)
try:
    if "GCP_SERVICE_ACCOUNT" in st.secrets:
        info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
        credentials = ee.ServiceAccountCredentials(info['client_email'], key_data=st.secrets["GCP_SERVICE_ACCOUNT"])
        ee.Initialize(credentials, project=info['project_id'])
    else:
        # Fallback for local development if secrets are not set, requires 'earthengine authenticate'
        ee.Initialize() 
except Exception as e:
    st.error(f"Failed to initialize Earth Engine. Ensure 'earthengine authenticate' is run locally or 'GCP_SERVICE_ACCOUNT' is set in Streamlit Secrets: {e}")
    st.stop() # Stop the app if GEE can't initialize

# --- Session State Initialization ---
# This ensures variables persist across Streamlit reruns
if 'current_ndvi_value' not in st.session_state:
    st.session_state.current_ndvi_value = 0.0
if 'carbon_tons_calculated' not in st.session_state:
    st.session_state.carbon_tons_calculated = 0.0
if 'pdf_report' not in st.session_state:
    st.session_state.pdf_report = None
if 'ndvi_time_series_df' not in st.session_state:
    st.session_state.ndvi_time_series_df = pd.DataFrame(columns=['date', 'NDVI'])


# --- Earth Engine Data Retrieval Functions ---

def get_real_ndvi(lat, lon, area_ha):
    """
    Fetches the current NDVI value for a dynamically sized circular area.
    """
    # Calculate radius based on hectares
    radius = calculate_buffer_radius(area_ha)
    if radius == 0: return 0.0

    point_geom = ee.Geometry.Point([lon, lat]).buffer(radius)
    
    image = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
             .filterBounds(point_geom)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50)) # Relaxed cloud filter
             .sort('system:time_start', False)
             .first())

    if not image: return 0.0

    ndvi_image = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    stats = ndvi_image.reduceRegion(
        reducer=ee.Reducer.mean(), 
        geometry=point_geom, 
        scale=10, # Sentinel-2 resolution
        maxPixels=1e9 # Important for larger areas
    )
    return stats.get('NDVI').getInfo() or 0.0


def get_ndvi_time_series(lat, lon, area_ha):
    """
    Fetches NDVI time series data for a dynamically sized circular area.
    """
    # Calculate radius based on hectares
    radius = calculate_buffer_radius(area_ha)
    if radius == 0: return pd.DataFrame(columns=['date', 'NDVI'])

    point_geom = ee.Geometry.Point([lon, lat]).buffer(radius)
    
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(point_geom)
                  .filterDate(start_date, end_date)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50))) # Relaxed cloud filter

    def extract_data(img):
        ndvi_band = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
        stats = ndvi_band.reduceRegion(
            reducer=ee.Reducer.mean(), 
            geometry=point_geom, 
            scale=10,
            maxPixels=1e9
        )
        return ee.Feature(None, {'date': img.date().format('YYYY-MM-01'), 'NDVI': stats.get('NDVI')})

    # Execute and get data
    data = collection.map(extract_data).getInfo()
    
    features = []
    for f in data['features']:
        props = f['properties']
        # Robustly check if 'NDVI' exists and is not None
        if props.get('NDVI') is not None:
            features.append(props)
    
    if not features:
        return pd.DataFrame(columns=['date', 'NDVI'])
        
    df = pd.DataFrame(features)
    # Ensure 'date' is datetime for sorting and plotting
    df['date'] = pd.to_datetime(df['date']) 
    return df.drop_duplicates(subset='date').sort_values('date') # Use subset for clarity


# --- Streamlit UI ---

st.title("🌱 EcoPlot AI Dashboard")

with st.sidebar:
    st.header("Farm Location & Size")
    farm_name = st.text_input("Enter Farm Name:", "My EcoPlot Farm")
    area_ha = st.number_input("Farm Area (Hectares):", min_value=0.1, value=1.0, format="%.1f")
    lat = st.number_input("Latitude", value=9.0820, format="%.4f") # Abuja example
    lon = st.number_input("Longitude", value=8.6753, format="%.4f") # Abuja example

    # Main action button
    if st.button("Analyze Farm & Generate Report"):
        st.session_state.current_ndvi_value = 0.0 # Reset for new calculation
        st.session_state.carbon_tons_calculated = 0.0 # Reset
        st.session_state.pdf_report = None # Reset PDF

        with st.spinner("Fetching satellite data and calculating..."):
            # Get current NDVI for the *entire* specified area
            st.session_state.current_ndvi_value = get_real_ndvi(lat, lon, area_ha)
            
            # Estimate carbon sequestration (adjust formula as needed for relevance)
            # This calculation now uses the actual area and average NDVI for that area
            if st.session_state.current_ndvi_value > 0:
                # Example: Assume a certain carbon capture per hectare per NDVI unit
                # This is a simplified model, adapt with real scientific coeffs if available
                st.session_state.carbon_tons_calculated = area_ha * st.session_state.current_ndvi_value * 50 # Example multiplier
            else:
                st.session_state.carbon_tons_calculated = 0.0

            # Generate PDF report
            st.session_state.pdf_report = create_pdf_report(
                farm_name, area_ha, st.session_state.carbon_tons_calculated
            )
            
            # Fetch NDVI time series for the *entire* specified area
            st.session_state.ndvi_time_series_df = get_ndvi_time_series(lat, lon, area_ha)

        st.success("✅ Analysis Complete! Results below.")


# --- Display Metrics ---
st.header("Current Farm Health Overview")
col1, col2 = st.columns(2)
with col1:
    st.metric("Vegetation Health (Current NDVI)", f"{st.session_state.current_ndvi_value:.2f}")
with col2:
    st.metric("Estimated Carbon Sequestration (Tons CO2eq)", f"{st.session_state.carbon_tons_calculated:.2f}")


# --- Display Historical NDVI Trend ---
st.header("Historical Vegetation Health Trend")
if not st.session_state.ndvi_time_series_df.empty:
    fig = px.line(
        st.session_state.ndvi_time_series_df, 
        x='date', 
        y='NDVI', 
        title=f"NDVI Trend for {farm_name} ({area_ha:.1f} Ha)",
        labels={'date': 'Date', 'NDVI': 'Average NDVI'}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning(f"⚠️ No sufficient clear satellite data found for {farm_name} ({area_ha:.1f} Ha) in the last 2 years with current cloud filtering.")


# --- Download Report Button ---
if st.session_state.pdf_report is not None:
    st.download_button(
        label="📄 Download ESG Report",
        data=bytes(st.session_state.pdf_report),
        file_name=f"{farm_name}_EcoPlot_Report.pdf",
        mime="application/pdf"
    )
