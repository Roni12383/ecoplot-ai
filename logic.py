import math
import geopandas as gpd
from shapely.geometry import Polygon


def calculate_metrics(lat, lon, area_ha=10.0):
    """
    Create a square polygon centered on (lat, lon) based on a target area in hectares.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees
    lon : float
        Longitude in decimal degrees
    area_ha : float, optional
        Target area in hectares. Default is 10.0

    Returns
    -------
    calculated_area_ha : float
        Area of the generated polygon in hectares
    gdf : geopandas.GeoDataFrame
        Polygon as a GeoDataFrame in EPSG:4326
    """
    if lat is None or lon is None:
        raise ValueError("Latitude and longitude are required.")

    if area_ha <= 0:
        raise ValueError("area_ha must be greater than 0.")

    # Convert hectares to square meters
    area_m2 = area_ha * 10000.0

    # Square side length in meters
    side_meters = math.sqrt(area_m2)

    # Approximate conversion from meters to degrees
    meters_per_degree_lat = 111320.0
    meters_per_degree_lon = 111320.0 * math.cos(math.radians(lat))

    if abs(meters_per_degree_lon) < 1e-9:
        raise ValueError("Longitude conversion failed near the poles.")

    half_side_lat_deg = (side_meters / 2.0) / meters_per_degree_lat
    half_side_lon_deg = (side_meters / 2.0) / meters_per_degree_lon

    # Create square polygon around the center point
    polygon = Polygon([
        (lon - half_side_lon_deg, lat - half_side_lat_deg),
        (lon + half_side_lon_deg, lat - half_side_lat_deg),
        (lon + half_side_lon_deg, lat + half_side_lat_deg),
        (lon - half_side_lon_deg, lat + half_side_lat_deg),
        (lon - half_side_lon_deg, lat - half_side_lat_deg),
    ])

    gdf = gpd.GeoDataFrame(
        {"name": ["Farm Plot"]},
        geometry=[polygon],
        crs="EPSG:4326"
    )

    # Reproject for area calculation
    calculated_area_m2 = gdf.to_crs(epsg=3857).geometry.area.iloc[0]
    calculated_area_ha = calculated_area_m2 / 10000.0

    return calculated_area_ha, gdf
