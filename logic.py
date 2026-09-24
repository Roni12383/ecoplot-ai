import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
import json
from pyproj import Geod

CARBON_FACTOR_TON_PER_HA = 5.2
geod = Geod(ellps="WGS84")

def calculate_true_hectares_from_gdf(gdf_meter):
    """True area from meter-projected gdf"""
    area_m2 = gdf_meter.geometry.area.iloc[0]
    return area_m2 / 10000

def calculate_metrics(lat, lon, ndvi_mean=0.4, buffer_sizes=[100, 500], custom_geojson=None):
    """
    FIXED VERSION - Supports:
    1. Single point -> auto 1ha
    2. custom_geojson from coordinates/shapefile -> true hectares
    """
    # --- CASE 1: Custom polygon from shapefile or coordinates list ---
    if custom_geojson:
        # custom_geojson is dict like {"type":"Polygon", "coordinates":[...]}
        gdf_custom = gpd.GeoDataFrame.from_features([{"type":"Feature","geometry":custom_geojson,"properties":{}}], crs="EPSG:4326")
        # Use Nigeria UTM Zone 32N for TRUE area - not 3857
        gdf_meter = gdf_custom.to_crs(epsg=32632) # UTM 32N accurate for Nigeria
        area_ha = gdf_meter.geometry.area.iloc[0] / 10000

        # For map
        gdf_1ha = gdf_custom
        bounds = gdf_custom.total_bounds

        # Buffers from custom polygon
        buffers = {}
        for size in buffer_sizes:
            buf_meter = gdf_meter.geometry.buffer(size)
            buf_wgs = gpd.GeoDataFrame(geometry=buf_meter, crs="EPSG:32632").to_crs(epsg=4326)
            buffers[f'buffer_{size}m'] = json.loads(buf_wgs.to_json())['features'][0]['geometry']

        gdf_final_geojson = custom_geojson # keep original

    else:
        # --- CASE 2: Single point -> create 1ha circle ---
        df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")

        # FIX: Use UTM 32N (EPSG:32632) for Nigeria, not 3857
        gdf_meter = gdf.to_crs(epsg=32632)

        radius_for_1ha = np.sqrt(10000 / np.pi) # 56.41m
        gdf_meter['geometry_1ha'] = gdf_meter.geometry.buffer(radius_for_1ha)

        area_ha = gdf_meter['geometry_1ha'].area.iloc[0] / 10000 # Should be exactly 1.0 now

        buffers = {}
        for size in buffer_sizes:
            buffers[f'buffer_{size}m'] = gdf_meter.geometry.buffer(size)

        # Back to WGS84 for mapping - FIX: Return single geometry, not FeatureCollection
        gdf_1ha_wgs = gpd.GeoDataFrame(geometry=gdf_meter['geometry_1ha'], crs="EPSG:32632").to_crs(epsg=4326)
        gdf_final_geojson = json.loads(gdf_1ha_wgs.to_json())['features'][0]['geometry']
        bounds = gdf_1ha_wgs.total_bounds

        # Convert buffers to geojson geometries
        buffers_geojson = {}
        for k, v in buffers.items():
            buf_wgs = gpd.GeoDataFrame(geometry=v, crs="EPSG:32632").to_crs(epsg=4326)
            buffers_geojson[k] = json.loads(buf_wgs.to_json())['features'][0]['geometry']
        buffers = buffers_geojson

    # --- CARBON (same formula but with TRUE area) ---
    if ndvi_mean <= 0: ndvi_mean = 0.4
    carbon_stock_tC = area_ha * ndvi_mean * CARBON_FACTOR_TON_PER_HA
    carbon_stock_tCO2e = carbon_stock_tC * 3.67

    # --- ESG ---
    if ndvi_mean > 0.5:
        veg_health = "Good"; esg_score = "A"; risk = "Low"
    elif ndvi_mean > 0.3:
        veg_health = "Moderate"; esg_score = "B"; risk = "Medium"
    else:
        veg_health = "Poor"; esg_score = "C"; risk = "High"

    degradation_percent = round((1 - ndvi_mean) * 100, 2)

    result = {
        "area_ha": round(area_ha, 3), # TRUE hectares now
        "center_coord": {"lat": lat, "lon": lon},
        "bounding_box": {"min_lon": bounds[0], "min_lat": bounds[1], "max_lon": bounds[2], "max_lat": bounds[3]},
        "geometry_1ha_geojson": gdf_final_geojson, # Single Polygon, not FeatureCollection
        "buffers_geojson": buffers,
        "carbon": {
            "ndvi_mean": round(ndvi_mean, 3),
            "carbon_stock_tC": round(carbon_stock_tC, 3),
            "carbon_stock_tCO2e": round(carbon_stock_tCO2e, 3),
            "per_hectare_tCO2e": round(carbon_stock_tCO2e / area_ha if area_ha else 0, 3)
        },
        "sustainability": {
            "vegetation_health": veg_health,
            "degradation_percent": degradation_percent,
            "esg_score": esg_score,
            "risk_level": risk
        }
    }
    return result
