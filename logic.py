import geopandas as gpd
import tempfile
import zipfile
from shapely.geometry import Polygon
import numpy as np

def process_shapefile(uploaded_file):
    """Takes uploaded zip, returns geometry and area in hectares"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        try:
            gdf = gpd.read_file(tmpdir)
            geometry = gdf.geometry.iloc[0]
            if gdf.crs and gdf.crs.is_projected:
                area_m2 = geometry.area
            else:
                gdf_proj = gdf.to_crs(epsg=3857)
                area_m2 = gdf_proj.geometry.iloc[0].area
            area_ha = area_m2 / 10000
            return geometry, area_ha, str(gdf.crs)
        except Exception as e:
            raise ValueError(f"Error reading shapefile: {e}")

def process_coordinates(coords_text):
    """Takes lat,lon text, returns geometry and area in hectares"""
    try:
        points = [tuple(map(float, line.split(','))) for line in coords_text.split('\n') if line.strip()]
        if len(points) < 3:
            raise ValueError("Need at least 3 points to form a polygon")
        poly = Polygon([(lon, lat) for lat, lon in points])
        area_ha = poly.area * 12364
        return poly, area_ha
    except Exception as e:
        raise ValueError(f"Invalid coordinates: {e}")

def get_ndvi_placeholder():
    """Placeholder for future satellite NDVI fetch from Sentinel-2"""
    return round(np.random.uniform(0.4, 0.8), 2)
