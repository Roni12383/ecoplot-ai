import ee
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Initialize Earth Engine - requires 'earthengine authenticate' in terminal
if "GCP_SERVICE_ACCOUNT" in st.secrets:
    info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    credentials = ee.ServiceAccountCredentials(info['client_email'], key_data=st.secrets["GCP_SERVICE_ACCOUNT"])
    ee.Initialize(credentials, project=info['project_id'])


def get_real_ndvi(lat, lon):
    point = ee.Geometry.Point([lon, lat])
    image = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
             .filterBounds(point)
             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
             .sort('system:time_start', False)
             .first())

    if not image: return 0.0

    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    stats = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=point, scale=10)
    return stats.get('NDVI').getInfo() or 0.0


def get_ndvi_time_series(lat, lon):
    point = ee.Geometry.Point([lon, lat])
    start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')

    collection = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(point)
                  .filterDate(start_date, datetime.now().strftime('%Y-%m-%d'))
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)))

    def extract_data(img):
        ndvi_img = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
        stats = ndvi_img.reduceRegion(ee.Reducer.mean(), point, 10)
        ndvi_value = stats.get('NDVI')

        return ee.Feature(None, {'date': img.date().format('YYYY-MM-01'), 'NDVI': ndvi})

    data = collection.map(extract_data).getInfo()
    features = [f['properties'] for f in data['features'] if f['properties']['NDVI'] is not None]
    return pd.DataFrame(features).drop_duplicates('date').sort_values('date')
