import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np

CARBON_FACTOR_TON_PER_HA = 5.2 # Example: tC/ha for savanna. Change per biome
NDVI_TO_CARBON_MULTIPLIER = 0.8 # Tune based on your EcoplotAI model

def calculate_metrics(lat, lon, ndvi_mean=0.4, buffer_sizes=[100, 500]):
    """
    Calculate area, carbon, ESG metrics and buffers for SIRA VENTURES report
    lat, lon: float
    ndvi_mean: 0-1 from your satellite analysis
    buffer_sizes: list of meters for buffer zones
    """
    # 1. Create point and calculate TRUE 1-hectare area
    df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")

    # Project to meters for accurate area/buffer
    gdf_meter = gdf.to_crs(epsg=3857)
    
    # For 1 hectare: radius = sqrt(10000 / pi) = 56.419m
    radius_for_1ha = np.sqrt(10000 / np.pi) 
    gdf_meter['geometry_1ha'] = gdf_meter.geometry.buffer(radius_for_1ha, cap_style=3)
    area_ha = gdf_meter['geometry_1ha'].area.iloc[0] / 10000 # Convert m2 to ha. Should be ~1.0

    # 2. Create additional buffers: 100m, 500m
    buffers = {}
    for size in buffer_sizes:
        buffers[f'buffer_{size}m'] = gdf_meter.geometry.buffer(size, cap_style=3)

    # 3. CARBON SEQUESTRATION CALCULATION
    # Formula: Carbon tCO2e = Area_ha * NDVI * Carbon_Factor * 3.67
    carbon_stock_tC = area_ha * ndvi_mean * CARBON_FACTOR_TON_PER_HA
    carbon_stock_tCO2e = carbon_stock_tC * 3.67
    
    # 4. SUSTAINABILITY / ESG SCORING
    # Simple logic: NDVI > 0.5 = Good, 0.3-0.5 = Moderate, <0.3 = Poor
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

    # 5. Back to Lat/Lon for mapping
    gdf_final = gdf_meter.to_crs(epsg=4326)
    gdf_1ha = gpd.GeoDataFrame(geometry=gdf_meter['geometry_1ha'], crs="EPSG:3857").to_crs(epsg=4326)
    
    # Get bounding box coordinates
    bounds = gdf_1ha.total_bounds # [minx, miny, maxx, maxy]
    
    # Build output dict
    result = {
        "area_ha": round(area_ha, 3),
        "center_coord": {"lat": lat, "lon": lon},
        "bounding_box": {"min_lon": bounds[0], "min_lat": bounds[1], "max_lon": bounds[2], "max_lat": bounds[3]},
        "geometry_1ha_geojson": gdf_1ha.__geo_interface__,
        "buffers_geojson": {k: gpd.GeoDataFrame(geometry=v, crs="EPSG:3857").to_crs(epsg=4326).__geo_interface__ for k,v in buffers.items()},
        "carbon": {
            "ndvi_mean": ndvi_mean,
            "carbon_stock_tC": round(carbon_stock_tC, 3),
            "carbon_stock_tCO2e": round(carbon_stock_tCO2e, 3),
            "per_hectare_tCO2e": round(carbon_stock_tCO2e / area_ha, 3)
        },
        "sustainability": {
            "vegetation_health": veg_health,
            "degradation_percent": degradation_percent,
            "esg_score": esg_score,
            "risk_level": risk
        }
    }
    return result

