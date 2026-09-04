import ee
import math
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
import json

if "GCP_SERVICE_ACCOUNT" in st.secrets:
    info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    credentials = ee.ServiceAccountCredentials(info['client_email'], key_data=st.secrets["GCP_SERVICE_ACCOUNT"])
    try:
        ee.Initialize(credentials, project=info['project_id'])
    except Exception as e:
        st.error(f"Failed to initialize Earth Engine: {e}")
else:
    st.error("GCP_SERVICE_ACCOUNT secret not found. Check your Streamlit Secrets settings.")


def get_real_ndvi(lat, lon, area_ha):
    """
    Get latest cloud-free NDVI for a given area in hectares
    """
    try:
        # 1. Convert hectares to radius for 1ha circle
        area_sqm = area_ha * 10000
        radius = math.sqrt(area_sqm / math.pi)

        # 2. Use dynamic radius buffer
        point = ee.Geometry.Point([lon, lat]).buffer(radius)

        image = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                 .filterBounds(point)
                 .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                 .filter(ee.Filter.calendarRange(2023, 2026, 'year')) # avoid old data
                 .sort('system:time_start', False)
                 .first())

        if image is None: 
            st.warning("No recent Sentinel-2 image found. Using default NDVI 0.3")
            return 0.3

        ndvi_image = image.normalizedDifference(['B8', 'B4']).rename('NDVI')

        stats = ndvi_image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=point,
            scale=10,
            maxPixels=1e9
        )
        ndvi_val = stats.get('NDVI').getInfo()
        return float(ndvi_val) if ndvi_val is not None else 0.3
        
    except Exception as e:
        st.error(f"EE NDVI Error: {e}")
        return 0.3


def get_ndvi_time_series(lat, lon):
    """
    Get 24-month NDVI time series for trend chart
    """
    try:
        # Use 1ha buffer instead of fixed 50m so it's consistent with report
        radius_for_1ha = math.sqrt(10000 / math.pi)
        point = ee.Geometry.Point([lon, lat]).buffer(radius_for_1ha)

        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                      .filterBounds(point)
                      .filterDate(start_date, end_date)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50)))

        def extract_data(img):
            ndvi_band = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
            stats = ndvi_band.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=10,
                maxPixels=1e9
            )
            return ee.Feature(None, {
                'date': img.date().format('YYYY-MM-01'),
                'NDVI': stats.get('NDVI')
            })

        data = collection.map(extract_data).getInfo()
        features = [f['properties'] for f in data['features'] if f['properties'].get('NDVI') is not None]

        if not features:
            return pd.DataFrame(columns=['date', 'NDVI'])

        df = pd.DataFrame(features)
        # Monthly average
        df['date'] = pd.to_datetime(df['date'])
        df = df.groupby('date').mean().reset_index()
        return df.sort_values('date')
        
    except Exception as e:
        st.error(f"EE Time Series Error: {e}")
        return pd.DataFrame(columns=['date', 'NDVI'])

