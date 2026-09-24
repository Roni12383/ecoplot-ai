import math
from shapely.geometry import Point, Polygon
from pyproj import Geod
import json

geod = Geod(ellps="WGS84")

def calculate_true_hectares(geojson_geom):
    """Geodesic area - accurate for Nigeria"""
    if geojson_geom["type"] == "Polygon":
        lons = [c[0] for c in geojson_geom["coordinates"][0]]
        lats = [c[1] for c in geojson_geom["coordinates"][0]]
        area, _ = geod.polygon_area_perimeter(lons, lats)
        return abs(area) / 10000
    elif geojson_geom["type"] == "MultiPolygon":
        total = 0
        for poly in geojson_geom["coordinates"]:
            lons = [c[0] for c in poly[0]]
            lats = [c[1] for c in poly[0]]
            a, _ = geod.polygon_area_perimeter(lons, lats)
            total += abs(a)
        return total / 10000
    return 1.0

def create_1ha_polygon(lat, lon, hectares=1.0):
    """Create square polygon around center point with TRUE area"""
    # 1 ha = 10000 m2. Side = sqrt(10000) = 100m
    # Convert 100m to degrees approx, then adjust via geod for accuracy
    # For simplicity: create buffer in meters using geod

    # 1 degree ~ 111km at equator
    # side in degrees = sqrt(hectares*10000) / 111000
    side_deg = math.sqrt(hectares * 10000) / 111320

    # Square coords
    coords = [
        [lon - side_deg/2, lat - side_deg/2],
        [lon + side_deg/2, lat - side_deg/2],
        [lon + side_deg/2, lat + side_deg/2],
        [lon - side_deg/2, lat + side_deg/2],
        [lon - side_deg/2, lat - side_deg/2],
    ]

    geojson = {"type": "Polygon", "coordinates": [coords]}
    # Now calculate TRUE area of what we created
    true_ha = calculate_true_hectares(geojson)

    return geojson, true_ha

def calculate_metrics(lat, lon, ndvi_mean=0.45, custom_geojson=None):
    """
    Main function called by app.py
    If custom_geojson provided, use its TRUE hectares
    """
    if custom_geojson:
        geojson_1ha = custom_geojson
        area_ha = calculate_true_hectares(custom_geojson)
    else:
        geojson_1ha, area_ha = create_1ha_polygon(lat, lon, hectares=1.0)

    # --- CARBON CALCULATION (IPCC Tier 2 for Savanna) ---
    # Carbon = Area_ha * NDVI * 5.2 * 3.67
    # 5.2 = biomass factor, 3.67 = C to CO2e
    if ndvi_mean <= 0:
        ndvi_mean = 0.45 # fallback if not fetched yet

    per_ha_co2e = ndvi_mean * 5.2 * 3.67
    total_co2e = area_ha * per_ha_co2e

    # --- SUSTAINABILITY LOGIC ---
    if ndvi_mean > 0.6:
        veg_health = "Healthy"
        risk = "Low"
        esg_score = 85
        degradation = 5
    elif ndvi_mean > 0.4:
        veg_health = "Moderate"
        risk = "Medium"
        esg_score = 65
        degradation = 25
    else:
        veg_health = "Degraded"
        risk = "High"
        esg_score = 35
        degradation = 60

    # --- BUFFERS (for map) ---
    # Create 100m, 500m buffer squares
    buffers = {}
    for buf_name, buf_size in [("100m Buffer", 0.001), ("500m Buffer", 0.005)]:
        buf_coords = [
            [lon - buf_size, lat - buf_size],
            [lon + buf_size, lat - buf_size],
            [lon + buf_size, lat + buf_size],
            [lon - buf_size, lat + buf_size],
            [lon - buf_size, lat - buf_size],
        ]
        buffers[buf_name] = {"type": "Polygon", "coordinates": [buf_coords]}

    return {
        "area_ha": round(area_ha, 3),
        "center_coord": {"lat": lat, "lon": lon},
        "bounding_box": f"{lon:.4f}, {lat:.4f}",
        "geometry_1ha_geojson": geojson_1ha,
        "buffers_geojson": buffers,
        "carbon": {
            "ndvi_mean": round(ndvi_mean, 3),
            "per_hectare_tCO2e": round(per_ha_co2e, 2),
            "carbon_stock_tCO2e": round(total_co2e, 2)
        },
        "sustainability": {
            "vegetation_health": veg_health,
            "risk_level": risk,
            "esg_score": esg_score,
            "degradation_percent": degradation
        }
    }
