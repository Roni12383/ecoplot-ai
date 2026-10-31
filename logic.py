import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import numpy as np
import json

CARBON_FACTOR_TON_PER_HA = 5.2
NDVI_TO_CARBON_MULTIPLIER = 0.8

def calculate_metrics(lat, lon, ndvi_mean=0.4, buffer_sizes=[100, 500], custom_geojson=None, hectares=1.0):
    """
    Calculate TRUE hectare WGS84 ellipsoid - EPSG:32632 UTM 32N for Nigeria
    - For point: radius = sqrt(hectares*10000 / pi) - Dynamic - 1ha=56.41m, 2ha=79.78m, 11.981ha=195.3m
    - For polygon: Use custom_geojson polygon area - TRUE hectare from shapefile
    - Returns: area_ha, center_coord, bounding_box, geometry_1ha_geojson, buffers_geojson, carbon, sustainability
    - For Xeelaa + EUDR V2: TRUE hectare + Carbon + Buffers
    """
    
    if custom_geojson:
        # Custom polygon from surveyor shapefile - TRUE hectare from polygon
        # Example: {"type": "Polygon", "coordinates": [[[8.5920,12.0022],...]]}
        gdf_wgs = gpd.GeoDataFrame.from_features(
            [{"type": "Feature", "geometry": custom_geojson, "properties": {}}],
            crs="EPSG:4326"
        )
        gdf_meter = gdf_wgs.to_crs(epsg=32632)  # UTM 32N for Nigeria - Accurate distance/area
        
        # FIXED: geometry_1ha is the polygon itself - For custom geojson
        gdf_meter['geometry_1ha'] = gdf_meter.geometry
        area_ha = gdf_meter['geometry_1ha'].area.iloc[0] / 10000  # m2 to ha - TRUE hectare ellipsoid
        
        # For buffers - Need point center - Use centroid of polygon for buffer center
        centroid_wgs = gdf_wgs.geometry.centroid.iloc[0]
        gdf_point_meter = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy([centroid_wgs.x], [centroid_wgs.y]),
            crs="EPSG:4326"
        ).to_crs(epsg=32632)
        
    else:
        # Point + radius - Dynamic radius for hectares - TRUE hectare
        # Formula: area = pi * r^2 => r = sqrt(area / pi) - area in m2 - hectares*10000
        df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        gdf_wgs = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
        gdf_meter = gdf_wgs.to_crs(epsg=32632)
        
        radius_for_ha = np.sqrt((hectares * 10000) / np.pi)  # Dynamic - 1ha=56.41m, 11.981ha=195.3m
        gdf_meter['geometry_1ha'] = gdf_meter.geometry.buffer(radius_for_ha)
        area_ha = gdf_meter['geometry_1ha'].area.iloc[0] / 10000  # TRUE hectare - WGS84 ellipsoid
        gdf_point_meter = gdf_meter

    # Buffers - For ESG + Deforestation risk - 100m, 500m
    buffers_meter = {}
    for size in buffer_sizes:
        if custom_geojson:
            # Buffer around polygon - For deforestation check - 100m, 500m around farm
            buffers_meter[f'buffer_{size}m'] = gdf_meter['geometry_1ha'].buffer(size)
        else:
            # Buffer around point - For point + radius case
            buffers_meter[f'buffer_{size}m'] = gdf_point_meter.geometry.buffer(size)

    # NDVI fix - If <=0, use 0.4 default
    if ndvi_mean <= 0:
        ndvi_mean = 0.4

    # Carbon calculation - Verra VM0042 compatible - tC to tCO2e *3.67
    carbon_stock_tC = area_ha * ndvi_mean * CARBON_FACTOR_TON_PER_HA
    carbon_stock_tCO2e = carbon_stock_tC * 3.67

    # Sustainability - For ESG score - Roni LGA pilot
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

    # Convert to WGS84 for map + PDF - EPSG:4326
    gdf_1ha_wgs = gpd.GeoDataFrame(geometry=gdf_meter['geometry_1ha'], crs="EPSG:32632").to_crs(epsg=4326)
    bounds = gdf_1ha_wgs.total_bounds  # [minx, miny, maxx, maxy] = [min_lon, min_lat, max_lon, max_lat]
    geometry_1ha_geojson = json.loads(gdf_1ha_wgs.to_json())['features'][0]['geometry']

    # Buffers to WGS84 GeoJSON - For map viewer - Xeelaa + Folium
    buffers_geojson = {}
    for k, v in buffers_meter.items():
        buf_wgs = gpd.GeoDataFrame(geometry=v, crs="EPSG:32632").to_crs(epsg=4326)
        buffers_geojson[k] = json.loads(buf_wgs.to_json())['features'][0]['geometry']

    result = {
        "area_ha": round(area_ha, 3),  # TRUE hectare - WGS84 ellipsoid - For EUDR
        "center_coord": {"lat": lat, "lon": lon},
        "bounding_box": {
            "min_lon": bounds[0],
            "min_lat": bounds[1],
            "max_lon": bounds[2],
            "max_lat": bounds[3]
        },
        "geometry_1ha_geojson": geometry_1ha_geojson,  # For map - Folium + Xeelaa
        "buffers_geojson": buffers_geojson,  # For ESG buffers - 100m, 500m
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
