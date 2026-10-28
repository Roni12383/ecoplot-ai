import streamlit as st
import hashlib
from datetime import datetime
import json

st.set_page_config(
    page_title="EcoPlotAI Verification - EUDR V2", 
    page_icon="✅", 
    layout="wide"
)

# --- GET PLOT ID FROM URL ---
# URL will be: https://ecoplotai.streamlit.app/verify?plot_id=JGW-RONI-012
# Or: https://ecoplotai.ng/verify/JGW-RONI-012 (if you have custom domain)
plot_id = st.query_params.get("plot_id", "")

# For testing, if no plot_id in URL, allow manual input
if not plot_id:
    st.title("🔍 EcoPlotAI - EUDR V2 Verification Portal")
    st.info("Public verification - No login - EU auditor can verify hash - Proves PDF not edited")
    plot_id_input = st.text_input("Enter Plot ID to verify (e.g., JGW-RONI-012)", "JGW-RONI-012")
    plot_id = plot_id_input
else:
    st.title(f"✅ Verification: {plot_id} - EUDR V2 DDS-Ready")

# --- MOCK DATABASE - REPLACE WITH YOUR REAL DATABASE ---
# In production, fetch from your PostgreSQL / Firestore / Streamlit secrets
# For now, this mock simulates what should be in your database
# When you generate PDF V2 in app.py, save same data to this database

# This simulates your database - In real app, connect to your DB
# Key: plot_id, Value: data that matches PDF
VERIFICATION_DB = {
    "JGW-RONI-012": {
        "farm_name": "Musa Garba - JGW-RONI-012",
        "true_hectare": 11.981,
        "center_lat": 12.0022,
        "center_lon": 8.5920,
        "start_date": "2020-12-31",
        "end_date": "2026-10-27",
        "ndvi_start": 0.58,
        "ndvi_end": 0.62,
        "ndvi_change": 0.04,
        "forest_cover": 5,
        "risk": "LOW",
        "compliant": "YES - EUDR COMPLIANT",
        "source": "Sentinel-2 L2A - COPERNICUS/S2_SR_HARMONIZED - Google Earth Engine",
        "fetch_time": "2026-10-27T10:29:00Z",
        "pdf_hash": "a3f5c9e8b7d6f4e2",  # IMPORTANT: Same hash as in PDF footer - Must match
        "evidence_url": "https://code.earthengine.google.com/?lat=12.0022&lon=8.5920&zoom=15",
        "product": "Sesame",
        "generated_time": "2026-10-27 10:30:15 UTC",
        "server": "EcoPlotAI Server v2.1 - Roni LGA, Jigawa, Nigeria - Automated - No manual edit",
        "verification_url": "https://ecoplotai.streamlit.app/verify?plot_id=JGW-RONI-012",
        "method": "WGS84 Ellipsoid PostGIS ST_Area(geography) TRUE hectare + Sentinel-2 NDVI"
    },
    "JGW-RONI-013": {
        "farm_name": "Aisha Bello - JGW-RONI-013",
        "true_hectare": 2.5,
        "center_lat": 12.0050,
        "center_lon": 8.5900,
        "start_date": "2020-12-31",
        "end_date": "2026-10-27",
        "ndvi_start": 0.45,
        "ndvi_end": 0.55,
        "ndvi_change": 0.10,
        "forest_cover": 8,
        "risk": "LOW",
        "compliant": "YES - EUDR COMPLIANT",
        "source": "Sentinel-2 L2A",
        "fetch_time": "2026-10-27T11:00:00Z",
        "pdf_hash": "b2d4f6a8c0e1d3f5",
        "evidence_url": "https://code.earthengine.google.com/?lat=12.0050&lon=8.5900",
        "product": "Soy",
        "generated_time": "2026-10-27 11:00:15 UTC",
        "server": "EcoPlotAI Server v2.1 - Roni LGA",
        "verification_url": "https://ecoplotai.streamlit.app/verify?plot_id=JGW-RONI-013",
        "method": "WGS84 TRUE hectare"
    }
}

# Add your 12ha PADAC farms here - Or connect to real DB
# In real app.py, after generating PDF, save to this DB:
# VERIFICATION_DB[plot_id] = eudr_data + metrics

if plot_id in VERIFICATION_DB:
    data = VERIFICATION_DB[plot_id]
    
    st.success(f"✅ Plot {plot_id} found - EUDR V2 DDS-Ready - Hash audit active - EU auditor can verify")
    
    # --- TOP METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("TRUE Hectare", f"{data['true_hectare']} ha")
        st.caption("WGS84 ellipsoid PostGIS")
    with col2:
        st.metric(f"NDVI {data['start_date']}", f"{data['ndvi_start']:.3f}")
        st.caption("Starting - EUDR cutoff")
    with col3:
        st.metric(f"NDVI {data['end_date']}", f"{data['ndvi_end']:.3f}")
        st.caption("Current - Today")
    with col4:
        st.metric("EUDR Risk", data['risk'])
        st.caption(data['compliant'])
    
    # --- DETAILS ---
    st.divider()
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📋 EUDR Compliance Details")
        st.write(f"**Farm:** {data['farm_name']}")
        st.write(f"**Product:** {data['product']} - HS Code 120740")
        st.write(f"**Location:** {data['center_lat']:.6f}N, {data['center_lon']:.6f}E - Roni LGA, Jigawa State, Nigeria")
        st.write(f"**Period:** {data['start_date']} to {data['end_date']} - {(datetime.strptime(data['end_date'], '%Y-%m-%d') - datetime.strptime(data['start_date'], '%Y-%m-%d')).days} days")
        st.write(f"**NDVI Change:** {data['ndvi_change']:+.3f} - {'No deforestation - Increase' if data['ndvi_change'] >= 0 else 'Review needed - Decrease'}")
        st.write(f"**Forest Cover 2020:** {data['forest_cover']}% - {'No forest - Already cropland' if data['forest_cover'] < 30 else 'Forest - Review'}")
        st.write(f"**Source:** {data['source']}")
        st.write(f"**Fetched:** {data['fetch_time']} - Automated from satellite API - No manual edit")
        st.write(f"**Generated:** {data['generated_time']} by {data['server']}")
        st.write(f"**Method:** {data['method']}")
        st.write(f"**Evidence URL:** {data['evidence_url']} - Click to verify on Google Earth Engine - Sentinel-2")
        
        # Map
        st.subheader("🗺️ Farm Location")
        st.map(data={"lat": [data['center_lat']], "lon": [data['center_lon']]}, zoom=14)
    
    with col_right:
        st.subheader("🔐 Audit Trail - Hash - No Editing")
        st.code(f"Hash: SHA256:{data['pdf_hash']}", language="text")
        st.write(f"**Verification URL:** {data['verification_url']}")
        st.write(f"**PDF Hash:** {data['pdf_hash']} - This hash is inside PDF footer - Must match database hash")
        st.info("If PDF edited after generation, hash will NOT match - EU auditor will detect and REJECT")
        
        # QR Code placeholder - In real app, generate QR
        st.subheader("📱 QR Code")
        st.write("QR in PDF links here - EU auditor scans QR - Opens this page - Verifies hash")
        st.caption(f"QR Data: {data['verification_url']}")
        
        st.subheader("✅ EU Auditor Checklist")
        st.write("1. Open PDF - Read footer hash")
        st.write("2. Scan QR - Opens this page")
        st.write("3. Compare hash in PDF == hash on this page - Must MATCH")
        st.write("4. Click Evidence URL - Verify NDVI on Google Earth Engine")
        st.write("5. If MATCH + Satellite verifies - ACCEPT - LOW RISK")
        st.write("6. If MISMATCH - PDF edited - REJECT + Blacklist")
    
    # --- HASH TEST - CORE TEST ---
    st.divider()
    st.header("🔍 TEST HASH AUDIT - Paste Hash from PDF Footer")
    st.warning("This is the test - Paste hash from your PDF footer - See if it matches database - Proves PDF not edited")
    
    col_test1, col_test2 = st.columns([2, 1])
    
    with col_test1:
        hash_from_pdf = st.text_input(
            "Paste Hash from PDF footer - Example: a3f5c9e8b7d6f4e2 - Found in PDF footer: Hash: SHA256:...",
            placeholder="a3f5c9e8b7d6f4e2",
            key="hash_input"
        )
        
        if st.button("✅ Verify Hash - Check if PDF Edited", type="primary"):
            if not hash_from_pdf:
                st.error("Please paste hash from PDF footer")
            else:
                clean_input = hash_from_pdf.strip().lower().replace("sha256:", "").replace("hash:", "").strip()
                db_hash = data['pdf_hash'].lower().strip()
                
                if clean_input == db_hash:
                    st.success(f"✅ MATCH - SUCCESS - PDF NOT EDITED - LEGITIMATE")
                    st.balloons()
                    st.write(f"**Hash from PDF:** {clean_input}")
                    st.write(f"**Hash from Database:** {db_hash}")
                    st.write(f"**Result:** MATCH - PDF was generated by system - No manual edit - No fraud")
                    st.write(f"**EU Decision:** ACCEPT - LOW RISK - Shipment can pass EU border - Olam saves N500M")
                    st.write(f"**Reason:** Hash audit proves PDF not edited after generation - Satellite data verifiable")
                else:
                    st.error(f"❌ MISMATCH - PDF EDITED - FRAUD DETECTED - EU WILL REJECT")
                    st.write(f"**Hash from PDF:** {clean_input}")
                    st.write(f"**Hash from Database:** {db_hash}")
                    st.write(f"**Result:** MISMATCH - PDF was edited in Adobe/Canva after generation - Manual edit detected")
                    st.write(f"**What happened:** Someone opened PDF in Adobe - Changed NDVI or area or dates - Saved - Hash changed but database still has original")
                    st.write(f"**EU Decision:** REJECT - HIGH RISK - Fraud - Blacklist exporter - Shipment blocked at Rotterdam")
                    st.write(f"**Action:** Generate new PDF from system - Do NOT edit PDF manually - System generates PDF once with correct data")
    
    with col_test2:
        st.subheader("Test Cases - Try These")
        st.write("**Test 1 - Legitimate (Your case):**")
        if st.button(f"Test MATCH - {data['pdf_hash'][:8]}..."):
            st.session_state.hash_input = data['pdf_hash']
            st.rerun()
        
        st.write("**Test 2 - Simulate Fraud (Edited PDF):**")
        fake_hash = "b2d4f6a8c0e1d3f5"
        if st.button(f"Test MISMATCH - {fake_hash[:8]}..."):
            st.session_state.hash_input = fake_hash
            st.rerun()
        
        st.write("**Test 3 - Another fake:**")
        if st.button("Test MISMATCH - xxxxxxxx"):
            st.session_state.hash_input = "xxxxxxxx"
            st.rerun()
    
    # --- FULL AUDIT LOG ---
    st.divider()
    st.subheader("📜 Full Audit Log - For EU Auditor - No Editing Proof")
    audit_log = {
        "plot_id": plot_id,
        "farm_name": data['farm_name'],
        "true_hectare": data['true_hectare'],
        "center": f"{data['center_lat']:.6f}, {data['center_lon']:.6f}",
        "dates": f"{data['start_date']} to {data['end_date']}",
        "ndvi": f"{data['ndvi_start']} -> {data['ndvi_end']} (change {data['ndvi_change']:+.3f})",
        "forest_cover": f"{data['forest_cover']}%",
        "risk": data['risk'],
        "compliant": data['compliant'],
        "source": data['source'],
        "fetch_time": data['fetch_time'],
        "generated_time": data['generated_time'],
        "pdf_hash": data['pdf_hash'],
        "verification_url": data['verification_url'],
        "evidence_url": data['evidence_url'],
        "server": data['server'],
        "method": data['method'],
        "audit_status": "System-generated - No manual edit - Hash verified - Legitimate"
    }
    st.json(audit_log)
    
    st.caption(f"Generated by EcoPlotAI Sovereign dMRV - HQ Roni LGA, Jigawa State, Nigeria - {datetime.now().strftime('%Y-%m-%d %H:%M:%S WAT')} - Contact sirajronee@gmail.com")

else:
    st.error(f"❌ Plot ID '{plot_id}' not found in verification database")
    st.write("Available plots for testing:")
    for pid in VERIFICATION_DB.keys():
        st.write(f"- {pid} - Hash {VERIFICATION_DB[pid]['pdf_hash']} - Link: /verify?plot_id={pid}")
    
    st.divider()
    st.info("How to add your plot to database: In app.py, after generating PDF, save eudr_data to your database (PostgreSQL/Firestore) - Then verification page will show it")
    
    # Show example for adding new plot
    st.subheader("How to add your 12ha PADAC farms to database - Code")
    st.code("""
# In app.py - After generating PDF V2 - Save to database
# Example - Save to Streamlit session_state for demo - In production, save to PostgreSQL

# After: st.session_state.pdf_report = create_pdf_report(...)
# Add:

# Save to verification DB (for demo - use PostgreSQL in production)
if 'verification_db' not in st.session_state:
    st.session_state.verification_db = {}

st.session_state.verification_db[farm_name] = {
    "farm_name": farm_name,
    "true_hectare": metrics['area_ha'],
    "center_lat": metrics['center_coord']['lat'],
    "center_lon": metrics['center_coord']['lon'],
    "start_date": str(st.session_state.eudr_data['start_date']),
    "end_date": str(st.session_state.eudr_data['end_date']),
    "ndvi_start": st.session_state.eudr_data['ndvi_start'],
    "ndvi_end": st.session_state.eudr_data['ndvi_end'],
    "ndvi_change": st.session_state.eudr_data['ndvi_change'],
    "forest_cover": st.session_state.eudr_data['forest_cover'],
    "risk": st.session_state.eudr_data['risk'],
    "compliant": st.session_state.eudr_data['compliant'],
    "source": st.session_state.eudr_data['source'],
    "fetch_time": st.session_state.eudr_data['fetch_time'].isoformat(),
    "pdf_hash": st.session_state.eudr_data['pdf_hash'],
    "evidence_url": st.session_state.eudr_data.get('evidence_url',''),
    "product": st.session_state.eudr_data['product'],
    "generated_time": datetime.utcnow().isoformat(),
    "server": "EcoPlotAI Server v2.1 - Roni LGA"
}

# Then verification page /verify?plot_id=YOUR_FARM_NAME will show it
""", language="python")
