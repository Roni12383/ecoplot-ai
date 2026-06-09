import ee
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


def get_real_ndvi(lat, lon):
    point = ee.Geometry.Point([lon, lat])
    image = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
             .filterBounds(point)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
             .sort('system:time_start', False)
             .first())

    if not image: return 0.0

    ndvi_image = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    stats = ndvi_image.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=10)
    return stats.get('NDVI').getInfo() or 0.0


def get_ndvi_time_series(lat, lon):
    # 1. Create a 50-meter buffer around the point (more robust than a single point)
    point = ee.Geometry.Point([lon, lat]).buffer(50)

    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(point)
                  .filterDate(start_date, end_date)
                  # 2. Relax the cloud filter to 50% to get more data points
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 50)))

    def extract_data(img):
        # Scale is 10 for Sentinel-2
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

    # Execute and get data
    data = collection.map(extract_data).getInfo()

    features = []
    for f in data['features']:
        props = f['properties']
        if props.get('NDVI') is not None:
            features.append(props)

    if not features:
        return pd.DataFrame(columns=['date', 'NDVI'])

    df = pd.DataFrame(features)
    # Drop duplicates so we only have one value per month
    return df.drop_duplicates('date’)
