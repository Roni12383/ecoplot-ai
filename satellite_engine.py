import math
import pandas as pd
import ee
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



def _make_square_roi(lat, lon, area_ha):
    """
    Build an approximate square ROI around a lat/lon based on area in hectares.
    """
    area_m2 = area_ha * 10000.0
    side_m = math.sqrt(area_m2)
    half_side_m = side_m / 2.0

    point = ee.Geometry.Point([lon, lat])
    roi = point.buffer(half_side_m).bounds()
    return roi


def _mask_s2_clouds(image):
    """
    Mask clouds using QA60 band for Sentinel-2 SR Harmonized.
    """
    qa = image.select("QA60")
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    mask = (
        qa.bitwiseAnd(cloud_bit_mask).eq(0)
        .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    )

    return image.updateMask(mask).copyProperties(image, ["system:time_start"])


def get_real_ndvi(lat, lon, area_ha):
    """
    Get current NDVI for a square ROI centered on the given lat/lon.
    Returns a float NDVI value.
    """
    try:
        roi = _make_square_roi(lat, lon, area_ha)

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(roi)
            .filterDate(
                ee.Date.now().advance(-90, "day"),
                ee.Date.now()
            )
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .map(_mask_s2_clouds)
        )

        image_count = collection.size().getInfo()
        if image_count == 0:
            return 0.0

        image = collection.median()

        ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

        stats = ndvi.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=10,
            maxPixels=1e9
        ).getInfo()

        ndvi_value = stats.get("NDVI", 0.0)
        if ndvi_value is None:
            return 0.0

        return float(ndvi_value)

    except Exception as e:
        print(f"Error in get_real_ndvi: {e}")
        return 0.0


def get_ndvi_time_series(lat, lon, area_ha, months=24):
    """
    Get monthly NDVI time series for the ROI over the last `months`.
    Returns a DataFrame with columns: ['date', 'NDVI']
    """
    try:
        roi = _make_square_roi(lat, lon, area_ha)

        end_date = ee.Date.now()
        start_date = end_date.advance(-months, "month")

        collection = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(roi)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .map(_mask_s2_clouds)
        )

        month_offsets = list(range(months))

        records = []

        for offset in month_offsets:
            month_start = start_date.advance(offset, "month")
            month_end = month_start.advance(1, "month")

            monthly_collection = collection.filterDate(month_start, month_end)
            image_count = monthly_collection.size().getInfo()

            if image_count == 0:
                continue

            monthly_image = monthly_collection.median()
            monthly_ndvi = monthly_image.normalizedDifference(["B8", "B4"]).rename("NDVI")

            stats = monthly_ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=10,
                maxPixels=1e9
            ).getInfo()

            ndvi_value = stats.get("NDVI", None)
            if ndvi_value is None:
                continue

            date_str = month_start.format("YYYY-MM-dd").getInfo()

            records.append({
                "date": date_str,
                "NDVI": float(ndvi_value)
            })

        if not records:
            return pd.DataFrame(columns=["date", "NDVI"])

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Error in get_ndvi_time_series: {e}")
        return pd.DataFrame(columns=["date", "NDVI"])
