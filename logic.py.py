import geopandas as gpd
from shapely.geometry import Point
import pandas as pd


def calculate_metrics(lat, lon):
    # Create a point and buffer it by 50m to create a 1-hectare area
    df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")

    # Project to meters for accurate buffering
    gdf_meter = gdf.to_crs(epsg=3857)
    gdf_meter['geometry'] = gdf_meter.geometry.buffer(50, cap_style=3)

    # Back to Lat/Lon for mapping
    gdf_final = gdf_meter.to_crs(epsg=4326)
    area_ha = 1.0

    return area_ha, gdf_final.__geo_interface__
