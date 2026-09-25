import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
import json

CARBON_FACTOR_TON_PER_HA = 5.2 # tC/ha for savanna
NDVI_TO_CARBON_MULTIPLIER = 0.8

def calculate_metrics(lat, lon, ndvi_mean=0.4, buffer_sizes=[100, 500], custom_geojson=None, hectares=1.0):
    """
    Calculate area, carbon, ESG metrics and buffers
    - lat, lon: center point
    - ndvi_mean: 0-1 from satellite
    - custom_geojson: Polygon from shapefile or coordinates list
    - hectares: dynamic input (1, 2, 5 etc) - fixes static 1ha bug
    """

    # 1. CREATE GEOMETRY - HANDLE 3 INPUT TYPES
    if custom_geojson:
        # CASE A: User uploaded shapefile or typed coordinates list
        # custom_geojson = {"type": "Polygon", "coordinates": [[...]]}
        gdf_wgs = gpd.GeoDataFrame.from_features(
            [{"type": "Feature", "geometry": custom_geojson, "properties": {}}],
            crs="EPSG:4326"
        )
        # Use UTM Zone 32N for Nigeria - accurate meters, not 3857
        gdf_meter = gdf_wgs.to_crs(epsg=32632)
        gdf_meter['geometry_1ha'] = gdf_meter.geometry
        area_ha = gdf_meter.geometry.area.iloc[0] / 10000

        # For buffers, we need a point version too
        gdf_point_meter = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy([lon], [lat]), crs="EPSG:4326"
        ).to_crs(epsg=32632)

    else:
        # CASE B: Single point + dynamic hectares (2ha = 2ha)
        df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        gdf_wgs = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")

        # FIX: Use EPSG:32632 (UTM 32N) for Nigeria - not 3857 which stretches 18%
        gdf_meter = gdf_wgs.to_crs(epsg=32632)

        # DYNAMIC radius: sqrt(hectares * 10000 / pi)
        # 1ha = 56.41m radius, 2ha = 79.78m radius
        radius_for_ha = np.sqrt((hectares * 10000) / np.pi)
        gdf_meter['geometry_1ha'] = gdf_meter.geometry.buffer(radius_for_ha)
        area_ha = gdf_meter['geometry_1ha'].area.iloc[0] / 10000

        gdf_point_meter = gdf_meter

    # 2. CREATE BUFFERS (100m, 500m)
    buffers_meter = {}
    for size in buffer_sizes:
        if custom_geojson:
            buffers_meter[f'buffer_{size}m'] = gdf_meter.geometry.buffer(size)
        else:
            buffers_meter[f'buffer_{size}m'] = gdf_point_meter.geometry.buffer(size)

    # 3. CARBON CALCULATION - Uses TRUE area
    if ndvi_mean <= 0:
        ndvi_mean = 0.4

    carbon_stock_tC = area_ha * ndvi_mean * CARBON_FACTOR_TON_PER_HA
    carbon_stock_tCO2e = carbon_stock_tC * 3.67

    # 4. SUSTAINABILITY / ESG
    if ndvi_mean > 0.5:
        veg_health = "Good"
        esg_score = "A"
        risk = "Low"
    elif ndvi_mean > 0.3:
        veg_health = "Moderate"
        esg_score = "B"
        risk = "Medium"
    else:
        veg_health = "Poor"
        esg_score = "C"
        risk = "High"

    degradation_percent = round((1 - ndvi_mean) * 100, 2)

    # 5. BACK TO LAT/LON FOR MAPPING - FIXED to return Polygon not FeatureCollection
    gdf_1ha_wgs = gpd.GeoDataFrame(geometry=gdf_meter['geometry_1ha'], crs="EPSG:32632").to_crs(epsg=4326)
    bounds = gdf_1ha_wgs.total_bounds # [minx, miny, maxx, maxy]

    # Single Polygon geometry for folium
    geometry_1ha_geojson = json.loads(gdf_1ha_wgs.to_json())['features'][0]['geometry']

    # Buffers to GeoJSON
    buffers_geojson = {}
    for k, v in buffers_meter.items():
        buf_wgs = gpd.GeoDataFrame(geometry=v, crs="EPSG:32632").to_crs(epsg=4326)
        buffers_geojson[k] = json.loads(buf_wgs.to_json())['features'][0]['geometry']

    # 6. BUILD OUTPUT
    result = {
        "area_ha": round(area_ha, 3),
        "center_coord": {"lat": lat, "lon": lon},
        "bounding_box": {
            "min_lon": bounds[0],
            "min_lat": bounds[1],
            "max_lon": bounds[2],
            "max_lat": bounds[3]
        },
        "geometry_1ha_geojson": geometry_1ha_geojson,
        "buffers_geojson": buffers_geojson,
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
