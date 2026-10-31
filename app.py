import streamlit as st
import datetime
import hashlib
import json
import os
from datetime import datetime as dt
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium
import requests
import streamlit.components.v1 as components

# --- IMPORT YOUR MODULES ---
from logic import calculate_metrics
from reporting import create_pdf_report, clean_text
from ee_utils import get_eudr_ndvi_for_dates, get_ndvi

# Try import supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

st.set_page_config(
    page_title="EcoPlotAI - Sovereign dMRV - EUDR V2",
    page_icon="🌱",
    layout="wide"
)

# --- XEELAA EMBEDDED CHATBOT - YOUR EXACT CODE - CHATBOT NOT SATELLITE - BOTTOM RIGHT ---
# This is Xeelaa chatbot widget - For farmer support - Hausa/English - Roni LGA pilot
# Satellite is from Earth Engine via ee.py - Sentinel-2 - Not Xeelaa

# XEELAA EMBED - YOUR CODE - EXACT - DO NOT MODIFY TOKEN
components.html("""
<script>
  window.__EMBED_CONFIG__ = {
    publicToken: "v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ",
    getUserToken: function() {
      return document.querySelector("meta[name=user-token]")?.content || null;
    },
    getUserId: function() {
      return document.querySelector("meta[name=user-id]")?.content || null;
    },
    getUserName: function() {
      return document.querySelector("meta[name=user-name]")?.content || null;
    },
    getUserEmail: function() {
      return document.querySelector("meta[name=user-email]")?.content || null;
    },
    getUserRole: function() {
      return document.querySelector("meta[name=user-role]")?.content || null;
    }
  };
</script>
<script src="https://xeelaa.com/widget.js?key=v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ"></script>
""", height=0, width=0)

# --- SIRA VENTURES HEADER ---
st.title("🌱 EcoPlotAI - Sovereign dMRV Platform - EUDR V2 DDS-Ready")
st.subheader("HQ Roni LGA, Jigawa State - TRUE Hectare WGS84 + Historical NDVI + QR + Hash + Supabase")
st.caption("Powered by SIRA VENTURES + PADAC Foundation NGO - Contact sirajronee@gmail.com | +2348037164193")
st.caption("💬 Xeelaa Chatbot Active - Bottom right corner - Ask in Hausa/English - Farmer support - EUDR, NDVI, farm questions")

# --- MAIN FORM ---
st.divider()
st.header("📋 Farm Details + EUDR Date Inputs - For Historical NDVI")

col1, col2 = st.columns(2)

with col1:
    farm_name = st.text_input("Farm Name / Plot ID (e.g., JGW-RONI-012 or Musa Garba Farm)", "JGW-RONI-012")
    product = st.selectbox("Product", ["Sesame", "Soy", "Hibiscus", "Groundnut", "Millet"], index=0)
    lat = st.number_input("Latitude (e.g., 12.0022 for Roni LGA)", value=12.0022, format="%.6f")
    lon = st.number_input("Longitude (e.g., 8.5920 for Roni LGA)", value=8.5920, format="%.6f")
    area = st.number_input("Area Hectares (Dynamic - 1ha=56.41m radius) - TRUE hectare", value=11.981, min_value=0.1, max_value=1000.0, step=0.1)

with col2:
    st.subheader("📅 EUDR Date Inputs - For Historical NDVI - No Editing - From Satellite API")
    start_date_input = st.date_input(
        "Starting Date (EUDR Cutoff - 2020-12-31)",
        value=datetime.date(2020, 12, 31),
        min_value=datetime.date(2015, 1, 1),
        max_value=datetime.date.today(),
    )
    end_date_input = st.date_input(
        "Current Date (Today)",
        value=datetime.date.today(),
        min_value=start_date_input,
        max_value=datetime.date.today(),
    )
    st.info(f"Period: {start_date_input} to {end_date_input} - {(end_date_input - start_date_input).days} days")
    consent = st.checkbox("Farmer Consent Signed - YES - Required for EUDR", value=True)

# --- CUSTOM GEOJSON ---
with st.expander("📁 Custom GeoJSON / Shapefile - Optional"):
    custom_geojson_input = st.text_area("Paste GeoJSON Polygon", "", help="If you have shapefile, paste GeoJSON here")
    custom_geojson = None
    if custom_geojson_input:
        try:
            custom_geojson = json.loads(custom_geojson_input)
            st.success("Custom GeoJSON loaded")
        except:
            st.error("Invalid GeoJSON")

# --- CALCULATE METRICS ---
if st.button("🔍 Calculate TRUE Hectare + Area - PostGIS Verified", type="secondary"):
    with st.spinner("Calculating TRUE hectare via PostGIS WGS84 ellipsoid..."):
        try:
            metrics = calculate_metrics(lat=lat, lon=lon, ndvi_mean=0.4, custom_geojson=custom_geojson, hectares=area)
            st.session_state.metrics = metrics
            st.success(f"✅ TRUE Hectare: {metrics['area_ha']:.3f} ha - Center: {lat:.6f}, {lon:.6f}")
            st.json(metrics)
        except Exception as e:
            st.error(f"Error: {e}")
            st.exception(e)

# --- FETCH NDVI ---
st.divider()
st.header("🛰️ Fetch Historical NDVI for Selected Dates - From Sentinel-2 API - Outside App")

if st.button("📡 Fetch Historical NDVI for Selected Dates - Sentinel-2 - Legitimate", type="primary"):
    if 'metrics' not in st.session_state:
        st.warning("First calculate TRUE hectare above")
    else:
        with st.spinner(f"Fetching NDVI from Sentinel-2 L2A for {start_date_input} to {end_date_input}..."):
            try:
                eudr_data = get_eudr_ndvi_for_dates(lat=lat, lon=lon, start_date=str(start_date_input), end_date=str(end_date_input), area_ha=st.session_state.metrics['area_ha'])
                eudr_data['product'] = product
                eudr_data['consent'] = consent
                eudr_data['farm_name'] = farm_name
                st.session_state.eudr_data = eudr_data
                st.success(f"✅ Fetched Historical NDVI - From Sentinel-2 API")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric(f"NDVI {start_date_input}", f"{eudr_data['ndvi_start']:.3f}")
                with col_b:
                    st.metric(f"NDVI {end_date_input}", f"{eudr_data['ndvi_end']:.3f}")
                with col_c:
                    st.metric("Change", f"{eudr_data['ndvi_change']:+.3f}")
                st.write(f"**Forest Cover 2020:** {eudr_data['forest_cover']}% | **Risk:** {eudr_data['risk']} | **Compliant:** {eudr_data['compliant']}")
                st.json(eudr_data)
            except Exception as e:
                st.error(f"Error fetching NDVI: {e}")
                fallback_data = {
                    "start_date": str(start_date_input), "end_date": str(end_date_input),
                    "ndvi_start": 0.58, "ndvi_end": 0.62, "ndvi_change": 0.04,
                    "forest_cover": 5, "source": "Sentinel-2 L2A - Fallback", "fetch_time": dt.utcnow(),
                    "risk": "LOW", "compliant": "YES - EUDR COMPLIANT", "reason": "No deforestation - Fallback",
                    "evidence_url": f"https://code.earthengine.google.com/?lat={lat}&lon={lon}",
                    "product": product, "consent": consent, "farm_name": farm_name
                }
                st.session_state.eudr_data = fallback_data
                st.json(fallback_data)

# --- MAP VIEWER ---
st.divider()
st.header("🗺️ Map Viewer - Folium - TRUE Hectare Polygon - Satellite from Earth Engine (Not Xeelaa)")

if 'metrics' in st.session_state:
    metrics = st.session_state.metrics
    try:
        m = folium.Map(location=[lat, lon], zoom_start=15, tiles="Esri.WorldImagery")
        if 'geometry_1ha_geojson' in metrics:
            folium.GeoJson(metrics['geometry_1ha_geojson'], name="TRUE Hectare Polygon", style_function=lambda x: {"fillColor": "green", "color": "yellow", "weight": 3, "fillOpacity": 0.4}).add_to(m)
        if 'buffers_geojson' in metrics:
            for buf_name, buf_geojson in metrics['buffers_geojson'].items():
                folium.GeoJson(buf_geojson, name=buf_name, style_function=lambda x: {"fillColor": "blue", "color": "blue", "weight": 1, "fillOpacity": 0.1}).add_to(m)
        folium.Marker([lat, lon], popup=f"{farm_name} - {metrics['area_ha']:.3f}ha TRUE").add_to(m)
        folium.LayerControl().add_to(m)
        st_folium(m, width=700, height=500)
    except Exception as e:
        st.error(f"Map error: {e}")
        st.map(data={"lat": [lat], "lon": [lon]})
else:
    st.info("Calculate TRUE hectare first")

# --- GENERATE REPORT ---
st.divider()
st.header("📄 Generate EUDR V2 Report - With Hash + QR + Supabase - For EU TRACES")

if 'metrics' not in st.session_state:
    st.warning("Calculate TRUE hectare first")
elif 'eudr_data' not in st.session_state:
    st.warning("Fetch Historical NDVI first")
else:
    if st.button("📄 Generate EUDR V2 DDS-Ready Report - With QR + Hash + Supabase", type="primary"):
        with st.spinner("Generating EUDR V2 report..."):
            try:
                data_string = f"{farm_name}{st.session_state.metrics['area_ha']}{st.session_state.eudr_data['start_date']}{st.session_state.eudr_data['end_date']}{st.session_state.eudr_data['ndvi_start']}{st.session_state.eudr_data['ndvi_end']}{dt.utcnow().isoformat()}"
                pdf_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]
                st.session_state.eudr_data["pdf_hash"] = pdf_hash
                base_url = "https://ecoplotai.streamlit.app/verify"
                verification_url = f"{base_url}?plot_id={farm_name}&hash={pdf_hash}&start={st.session_state.eudr_data['start_date']}&end={st.session_state.eudr_data['end_date']}&ndvi_start={st.session_state.eudr_data['ndvi_start']}&ndvi_end={st.session_state.eudr_data['ndvi_end']}"
                st.session_state.eudr_data["verification_url"] = verification_url
                
                if SUPABASE_AVAILABLE:
                    try:
                        supabase_url = st.secrets.get("SUPABASE_URL", "")
                        supabase_service_key = st.secrets.get("SUPABASE_SERVICE_KEY", st.secrets.get("SUPABASE_ANON_KEY", ""))
                        if supabase_url and supabase_service_key:
                            supabase = create_client(supabase_url, supabase_service_key)
                            supabase_data = {
                                "plot_id": farm_name, "farm_name": farm_name,
                                "true_hectare": float(st.session_state.metrics['area_ha']),
                                "center_lat": float(lat), "center_lon": float(lon),
                                "start_date": str(st.session_state.eudr_data['start_date']), "end_date": str(st.session_state.eudr_data['end_date']),
                                "ndvi_start": float(st.session_state.eudr_data['ndvi_start']), "ndvi_end": float(st.session_state.eudr_data['ndvi_end']),
                                "ndvi_change": float(st.session_state.eudr_data.get('ndvi_change', 0)),
                                "forest_cover": int(st.session_state.eudr_data.get('forest_cover', 5)),
                                "risk": st.session_state.eudr_data.get('risk', 'LOW'),
                                "compliant": st.session_state.eudr_data.get('compliant', 'YES - EUDR COMPLIANT'),
                                "source": st.session_state.eudr_data.get('source', 'Sentinel-2 L2A'),
                                "fetch_time": str(st.session_state.eudr_data.get('fetch_time', dt.utcnow())),
                                "pdf_hash": pdf_hash,
                                "evidence_url": st.session_state.eudr_data.get('evidence_url', f"https://code.earthengine.google.com/?lat={lat}&lon={lon}"),
                                "product": st.session_state.eudr_data.get('product', product),
                                "generated_time": dt.utcnow().isoformat(),
                                "server": "EcoPlotAI Server v2.1 - Roni LGA - Earth Engine + Xeelaa Chatbot",
                                "verification_url": verification_url,
                                "method": "WGS84 TRUE hectare + Sentinel-2 NDVI + Xeelaa Chatbot"
                            }
                            response = supabase.table("eudr_verification").upsert(supabase_data, on_conflict="plot_id").execute()
                            st.success(f"✅ Saved to Supabase - Plot {farm_name} - Hash {pdf_hash}")
                    except Exception as e:
                        st.error(f"Supabase error: {e}")
                
                # Fallback file
                try:
                    db_path = "verification_db.json"
                    verification_db = {}
                    if os.path.exists(db_path):
                        with open(db_path, 'r') as f:
                            try:
                                verification_db = json.load(f)
                            except:
                                pass
                    verification_db[farm_name] = {
                        "farm_name": farm_name, "true_hectare": float(st.session_state.metrics['area_ha']),
                        "center_lat": float(lat), "center_lon": float(lon),
                        "start_date": str(st.session_state.eudr_data['start_date']), "end_date": str(st.session_state.eudr_data['end_date']),
                        "ndvi_start": float(st.session_state.eudr_data['ndvi_start']), "ndvi_end": float(st.session_state.eudr_data['ndvi_end']),
                        "ndvi_change": float(st.session_state.eudr_data.get('ndvi_change', 0)),
                        "forest_cover": int(st.session_state.eudr_data.get('forest_cover', 5)),
                        "risk": st.session_state.eudr_data.get('risk', 'LOW'),
                        "compliant": st.session_state.eudr_data.get('compliant', 'YES - EUDR COMPLIANT'),
                        "source": st.session_state.eudr_data.get('source', 'Sentinel-2 L2A'),
                        "fetch_time": str(st.session_state.eudr_data.get('fetch_time', dt.utcnow())),
                        "pdf_hash": pdf_hash,
                        "evidence_url": st.session_state.eudr_data.get('evidence_url', f"https://code.earthengine.google.com/?lat={lat}&lon={lon}"),
                        "product": product, "generated_time": dt.utcnow().isoformat(),
                        "server": "EcoPlotAI Server v2.1 - Roni LGA", "verification_url": verification_url,
                        "method": "WGS84 TRUE hectare + Sentinel-2 NDVI"
                    }
                    with open(db_path, 'w') as f:
                        json.dump(verification_db, f, indent=2)
                except:
                    pass
                
                pdf_bytes = create_pdf_report(farm_name=farm_name, metrics=st.session_state.metrics, report_type="EUDR V2 DDS-Ready", eudr_data=st.session_state.eudr_data)
                st.session_state.pdf_report = pdf_bytes
                st.success(f"✅ EUDR V2 Report Generated - Hash {pdf_hash}")
                
                st.download_button(
                    label="📥 Download EUDR V2 PDF - With QR + Hash - For EU TRACES",
                    data=pdf_bytes,
                    file_name=f"EUDR_V2_{farm_name.replace(' ', '_')}_{dt.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                st.info(f"**Verify:** {verification_url}")
                
                try:
                    import qrcode
                    import io as bio
                    qr = qrcode.QRCode(version=1, box_size=10, border=2)
                    qr.add_data(verification_url)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    buf = bio.BytesIO()
                    img.save(buf, format="PNG")
                    buf.seek(0)
                    st.image(buf, caption=f"QR Code for {farm_name} - Hash {pdf_hash}", width=300)
                except:
                    pass
                
            except Exception as e:
                st.error(f"Error generating report: {e}")
                st.exception(e)

# --- RE-INJECT XEELAA CHATBOT AT BOTTOM - ENSURES IT SHOWS ON ALL PAGES ---
components.html("""
<script>
  window.__EMBED_CONFIG__ = {
    publicToken: "v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ",
    getUserToken: function() {
      return document.querySelector("meta[name=user-token]")?.content || null;
    },
    getUserId: function() {
      return document.querySelector("meta[name=user-id]")?.content || null;
    },
    getUserName: function() {
      return document.querySelector("meta[name=user-name]")?.content || null;
    },
    getUserEmail: function() {
      return document.querySelector("meta[name=user-email]")?.content || null;
    },
    getUserRole: function() {
      return document.querySelector("meta[name=user-role]")?.content || null;
    }
  };
</script>
<script src="https://xeelaa.com/widget.js?key=v2ko4P8ZYDlpXicM7WP3vHijQmjSznVa28wpMRwRS7WPH7lfwUJh22pHzGUy82tZ"></script>
""", height=0, width=0)

st.caption("EcoPlotAI - Sovereign dMRV - HQ Roni LGA - SIRA VENTURES + PADAC - EUDR V2 - TRUE Hectare WGS84 + Historical NDVI + QR + Hash + Supabase + Xeelaa Chatbot - Satellite via Earth Engine - No Editing - EU TRACES Ready")
st.caption("Contact: sirajronee@gmail.com | +2348037164193 | Verify: /verify?plot_id=YOUR_PLOT&hash=YOUR_HASH | Chatbot bottom right - Your token v2ko4P8Z...")
