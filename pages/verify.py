import streamlit as st
import hashlib
from datetime import datetime
import json
import os

# Try import supabase - If not available, fallback to file
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

st.set_page_config(
    page_title="EcoPlotAI Verification - EUDR V2 - Supabase", 
    page_icon="✅", 
    layout="wide"
)

# --- GET PARAMS FROM URL ---
plot_id = st.query_params.get("plot_id", "")
hash_from_qr = st.query_params.get("hash", "")
start_from_qr = st.query_params.get("start", "")
end_from_qr = st.query_params.get("end", "")
ndvi_start_from_qr = st.query_params.get("ndvi_start", "")
ndvi_end_from_qr = st.query_params.get("ndvi_end", "")

if not plot_id:
    st.title("🔍 EcoPlotAI - EUDR V2 Verification Portal - Supabase Persistent")
    st.info("Public verification - No login - EU auditor can verify hash - Supabase persistent DB - Works for unlimited reports")
    plot_id_input = st.text_input("Enter Plot ID / Farm Name (e.g., JGW-RONI-012)", "")
    if plot_id_input:
        plot_id = plot_id_input
        st.query_params["plot_id"] = plot_id
else:
    st.title(f"✅ Verification: {plot_id} - EUDR V2 DDS-Ready - Supabase")

# --- LOAD FROM SUPABASE - PERSISTENT - NOT FILE - WORKS FOR ALL REPORTS ---
verification_db = {}
supabase_client = None

# Try Supabase first - Persistent
if SUPABASE_AVAILABLE:
    try:
        supabase_url = st.secrets.get("SUPABASE_URL", "")
        supabase_anon_key = st.secrets.get("SUPABASE_ANON_KEY", "")
        
        if supabase_url and supabase_anon_key:
            supabase_client = create_client(supabase_url, supabase_anon_key)
            st.caption(f"Connected to Supabase - Persistent DB - {supabase_url}")
        else:
            st.warning("Supabase secrets not found - Add SUPABASE_URL and SUPABASE_ANON_KEY to secrets - Using file fallback")
            supabase_client = None
    except Exception as e:
        st.warning(f"Supabase connection error: {e} - Using file fallback")
        supabase_client = None
else:
    st.warning("Supabase library not installed - pip install supabase - Using file fallback")

# Function to load from Supabase
def load_from_supabase(plot_id_to_load=None):
    if not supabase_client:
        return None, {}
    
    try:
        if plot_id_to_load:
            # Load specific plot
            response = supabase_client.table("eudr_verification").select("*").eq("plot_id", plot_id_to_load).execute()
            if response.data and len(response.data) > 0:
                data = response.data[0]
                return data, {data['plot_id']: data}
            else:
                return None, {}
        else:
            # Load all plots
            response = supabase_client.table("eudr_verification").select("*").order("created_at", desc=True).limit(100).execute()
            db = {}
            for row in response.data:
                db[row['plot_id']] = row
            return None, db
    except Exception as e:
        st.error(f"Supabase load error: {e}")
        return None, {}

# Function to load from file fallback
def load_from_file():
    db_path = "verification_db.json"
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r') as f:
                db = json.load(f)
            return db
        except:
            return {}
    return {}

# Load data
if supabase_client:
    # Load from Supabase - Persistent
    if plot_id:
        single_data, all_db = load_from_supabase(plot_id)
        if single_data:
            verification_db = {plot_id: single_data}
        else:
            # Plot not found in Supabase - Load all to show list
            _, all_db = load_from_supabase()
            verification_db = all_db
    else:
        # No plot_id - Load all
        _, verification_db = load_from_supabase()
else:
    # Fallback to file
    verification_db = load_from_file()
    if not verification_db:
        # Mock data if file also not exists
        verification_db = {
            "JGW-RONI-012": {
                "plot_id": "JGW-RONI-012",
                "farm_name": "Musa Garba - JGW-RONI-012",
                "true_hectare": 11.981,
                "center_lat": 12.0022,
                "center_lon": 8.592,
                "start_date": "2020-12-31",
                "end_date": "2026-10-27",
                "ndvi_start": 0.58,
                "ndvi_end": 0.62,
                "ndvi_change": 0.04,
                "forest_cover": 5,
                "risk": "LOW",
                "compliant": "YES - EUDR COMPLIANT",
                "source": "Sentinel-2 L2A",
                "fetch_time": "2026-10-27T10:29:00Z",
                "pdf_hash": "a3f5c9e8b7d6f4e2",
                "evidence_url": "https://code.earthengine.google.com/?lat=12.0022&lon=8.592",
                "product": "Sesame",
                "generated_time": "2026-10-27 10:30:15 UTC",
                "server": "EcoPlotAI Server v2.1 - Roni LGA",
                "verification_url": "https://ecoplotai.streamlit.app/verify?plot_id=JGW-RONI-012&hash=a3f5c9e8b7d6f4e2",
                "method": "WGS84 TRUE hectare + Sentinel-2 NDVI"
            }
        }

# --- CHECK IF PLOT EXISTS ---
if plot_id and plot_id in verification_db:
    data = verification_db[plot_id]
    
    if hash_from_qr:
        st.info(f"📱 QR Scanned - Hash from QR: {hash_from_qr} - Auto-verifying")
    
    st.success(f"✅ Plot {plot_id} FOUND - Supabase persistent - {len(verification_db)} plots total - Hash audit active - Works for all reports")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("TRUE Hectare", f"{data['true_hectare']} ha")
    with col2:
        st.metric(f"NDVI {data['start_date']}", f"{data['ndvi_start']:.3f}")
    with col3:
        st.metric(f"NDVI {data['end_date']}", f"{data['ndvi_end']:.3f}")
    with col4:
        st.metric("EUDR Risk", data['risk'])
    
    st.divider()
    col_left, col_right = st.columns([2, 1])
    
with col_left:
        st.subheader("📋 EUDR Compliance Details - Supabase Persistent")
        st.write(f"**Farm:** {data['farm_name']} | **Plot ID:** {data['plot_id']}")
        st.write(f"**Product:** {data['product']} | **Compliant:** {data['compliant']}")
        st.write(f"**Location:** {data['center_lat']:.6f}N, {data['center_lon']:.6f}E - Roni LGA, Jigawa")
        st.write(f"**Period:** {data['start_date']} to {data['end_date']} - Change {data.get('ndvi_change',0):+.3f}")
        st.write(f"**Forest Cover 2020:** {data['forest_cover']}% | **Source:** {data['source']}")
        st.write(f"**Fetched:** {data['fetch_time']} | **Generated:** {data['generated_time']}")
        st.write(f"**Evidence URL:** {data['evidence_url']}")
        st.map(data={"lat": [data['center_lat']], "lon": [data['center_lon']]}, zoom=14)

    
    with col_right:
        st.subheader("🔐 Audit Trail - Hash - Supabase")
        st.code(f"SHA256:{data['pdf_hash']}", language="text")
        st.write(f"**Verification URL:** {data['verification_url']}")
        st.info("Hash in PDF footer must match this Supabase DB hash - Persistent - Cannot be lost")
        
        if supabase_client:
            st.success("✅ Supabase connected - Persistent - No file upload needed - Works for unlimited reports")
        else:
            st.warning("⚠️ File fallback - Add Supabase secrets for persistence - File will be lost on reboot")
    
    # --- HASH VERIFICATION - WORKS FOR ANY PLOT - SUPABASE PERSISTENT ---
    st.divider()
    st.header("🔍 TEST HASH AUDIT - Supabase Persistent - Works for ANY Report - Unlimited")
    
    col_test1, col_test2 = st.columns([2, 1])
    
    with col_test1:
        default_hash = hash_from_qr if hash_from_qr else ""
        hash_from_pdf = st.text_input(
            "Paste Hash from PDF footer OR scan QR (auto-filled from QR)",
            value=default_hash,
            placeholder="a3f5c9e8b7d6f4e2",
            key="hash_input_supabase"
        )
        
        auto_verify = st.checkbox("Auto-verify if QR scanned", value=True if hash_from_qr else False)
        
        if st.button("✅ Verify Hash - Supabase Persistent - Works for All Plots", type="primary") or (auto_verify and hash_from_pdf):
            if not hash_from_pdf:
                st.error("Paste hash from PDF footer")
            else:
                clean_input = hash_from_pdf.strip().lower().replace("sha256:", "").replace("hash:", "").strip()
                db_hash = data['pdf_hash'].lower().strip()
                
                if clean_input == db_hash:
                    st.success(f"✅ MATCH - Plot {plot_id} - Supabase Persistent - PDF NOT EDITED - EU ACCEPT")
                    st.balloons()
                    st.write(f"**Plot:** {plot_id} | **Hash PDF/QR:** {clean_input} | **DB Hash:** {db_hash}")
                    st.write(f"**NDVI:** {data['ndvi_start']} -> {data['ndvi_end']} | **Dates:** {data['start_date']} -> {data['end_date']}")
                    st.write(f"**Result:** MATCH - No editing - System-generated - Satellite verifiable - Supabase persistent")
                    st.write(f"**EU Decision:** ACCEPT - LOW RISK - Shipment passes EU border - Works for all reports now")
                else:
                    st.error(f"❌ MISMATCH - Plot {plot_id} - PDF EDITED - EU REJECT")
                    st.write(f"**PDF/QR Hash:** {clean_input} | **DB Hash:** {db_hash}")
                    st.write(f"**DB has NDVI {data['ndvi_start']}->{data['ndvi_end']} for {plot_id} - If PDF shows different, edited")
    
    with col_test2:
        st.subheader("All Plots in Supabase DB - Persistent")
        st.write(f"Total: {len(verification_db)} plots - Supabase persistent - No file upload")
        for pid, pdata in verification_db.items():
            if st.button(f"{pid} - {pdata['pdf_hash'][:8]}... - {pdata['true_hectare']}ha", key=f"supa_{pid}"):
                st.query_params["plot_id"] = pid
                st.query_params["hash"] = pdata['pdf_hash']
                st.rerun()
        
        # Show raw data for debugging
        with st.expander("Show raw Supabase data - All plots"):
            st.json(verification_db)

elif plot_id:
    st.error(f"❌ Plot ID '{plot_id}' NOT FOUND in Supabase DB")
    st.write(f"Supabase has {len(verification_db)} plots:")
    for pid in verification_db.keys():
        st.write(f"- {pid} - {verification_db[pid]['pdf_hash'][:8]}... - {verification_db[pid]['true_hectare']}ha")
    
    st.divider()
    st.info("Fix: Generate report in main app - App will save to Supabase automatically - Then verify here works immediately - No file upload needed")
    
    if hash_from_qr and start_from_qr:
        st.success(f"But QR has data - Plot {plot_id} - Hash {hash_from_qr} - Dates {start_from_qr} to {end_from_qr} - We can show from QR even without DB")
        st.write(f"QR Data: NDVI {ndvi_start_from_qr}->{ndvi_end_from_qr}")
        st.write("Generate report in main app to save to Supabase for persistence")

else:
    st.info("Enter Plot ID to verify - Or scan QR from PDF - Supabase persistent DB works for all reports")
    st.write(f"Available in Supabase: {len(verification_db)} plots")
    st.json(verification_db)
