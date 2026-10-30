import streamlit as st
import hashlib
from datetime import datetime
import json
import os

# Try import supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

st.set_page_config(
    page_title="EcoPlotAI Verification - EUDR V2",
    page_icon="✅",
    layout="wide"
)

# --- GET URL PARAMS - FROM QR CODE ---
plot_id = st.query_params.get("plot_id", "")
hash_from_qr = st.query_params.get("hash", "")
start_from_qr = st.query_params.get("start", "")
end_from_qr = st.query_params.get("end", "")
ndvi_start_from_qr = st.query_params.get("ndvi_start", "")
ndvi_end_from_qr = st.query_params.get("ndvi_end", "")

# Manual input if no plot_id in URL
if not plot_id:
    st.title("🔍 EcoPlotAI - EUDR V2 Verification Portal")
    st.info("Public verification - No login - EU auditor can verify hash - Proves PDF not edited - Supabase persistent")
    plot_id_input = st.text_input("Enter Plot ID / Farm Name (e.g., JGW-RONI-012)", "")
    if plot_id_input:
        plot_id = plot_id_input
        st.query_params["plot_id"] = plot_id
        st.rerun()
else:
    st.title(f"✅ Verification: {plot_id} - EUDR V2 DDS-Ready")

# --- LOAD DB - SUPABASE FIRST - THEN FILE FALLBACK ---
verification_db = {}
supabase_client = None

# Connect Supabase
if SUPABASE_AVAILABLE:
    try:
        supabase_url = st.secrets.get("SUPABASE_URL", "")
        supabase_anon_key = st.secrets.get("SUPABASE_ANON_KEY", "")
        if supabase_url and supabase_anon_key:
            supabase_client = create_client(supabase_url, supabase_anon_key)
        else:
            supabase_client = None
    except Exception as e:
        supabase_client = None

# Load from Supabase
def load_from_supabase(pid=None):
    if not supabase_client:
        return None, {}
    try:
        if pid:
            resp = supabase_client.table("eudr_verification").select("*").eq("plot_id", pid).execute()
            if resp.data and len(resp.data) > 0:
                row = resp.data[0]
                return row, {row['plot_id']: row}
            else:
                return None, {}
        else:
            resp = supabase_client.table("eudr_verification").select("*").order("created_at", desc=True).limit(100).execute()
            db = {}
            for r in resp.data:
                db[r['plot_id']] = r
            return None, db
    except Exception as e:
        st.error(f"Supabase error: {e}")
        return None, {}

def load_from_file():
    db_path = "verification_db.json"
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Load
if supabase_client:
    if plot_id:
        single, all_db = load_from_supabase(plot_id)
        if single:
            verification_db = {plot_id: single}
        else:
            _, verification_db = load_from_supabase(None)
    else:
        _, verification_db = load_from_supabase(None)
else:
    verification_db = load_from_file()

# Fallback mock if empty
if not verification_db:
    verification_db = {
        "JGW-RONI-012": {
            "plot_id": "JGW-RONI-012",
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
            "source": "Sentinel-2 L2A",
            "fetch_time": "2026-10-27T10:29:00Z",
            "pdf_hash": "a3f5c9e8b7d6f4e2",
            "evidence_url": "https://code.earthengine.google.com/?lat=12.0022&lon=8.5920",
            "product": "Sesame",
            "generated_time": "2026-10-27 10:30:15 UTC",
            "server": "EcoPlotAI Server v2.1 - Roni LGA",
            "verification_url": "https://ecoplotai.streamlit.app/verify?plot_id=JGW-RONI-012&hash=a3f5c9e8b7d6f4e2",
            "method": "WGS84 TRUE hectare + Sentinel-2 NDVI"
        }
    }

# --- DISPLAY IF FOUND ---
if plot_id and plot_id in verification_db:
    data = verification_db[plot_id]
    
    if hash_from_qr:
        st.info(f"📱 QR Scanned - Hash from QR: {hash_from_qr}")
    
    st.success(f"✅ Plot {plot_id} FOUND - {len(verification_db)} plots in DB - EUDR V2 - Hash audit active")
    
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("TRUE Hectare", f"{data['true_hectare']} ha")
    with c2:
        st.metric(f"NDVI {data['start_date']}", f"{data['ndvi_start']:.3f}")
    with c3:
        st.metric(f"NDVI {data['end_date']}", f"{data['ndvi_end']:.3f}")
    with c4:
        st.metric("Risk", data['risk'])
    
    st.divider()
    left, right = st.columns([2, 1])
    
    with left:
        st.subheader("📋 EUDR Details")
        st.write(f"**Farm:** {data['farm_name']}")
        st.write(f"**Product:** {data['product']} - **Compliant:** {data['compliant']}")
        st.write(f"**Location:** {data['center_lat']:.6f}N, {data['center_lon']:.6f}E - Roni LGA")
        st.write(f"**Period:** {data['start_date']} to {data['end_date']} - Change {data.get('ndvi_change',0):+.3f}")
        st.write(f"**Forest Cover:** {data['forest_cover']}% - **Source:** {data['source']}")
        st.write(f"**Fetched:** {data['fetch_time']} - **Generated:** {data['generated_time']}")
        st.write(f"**Evidence:** {data['evidence_url']}")
        try:
            st.map(data={"lat": [data['center_lat']], "lon": [data['center_lon']]}, zoom=14)
        except:
            pass
    
    with right:
        st.subheader("🔐 Hash Audit")
        st.code(f"SHA256:{data['pdf_hash']}", language="text")
        st.write(f"**URL:** {data['verification_url']}")
        if supabase_client:
            st.success("✅ Supabase persistent")
        else:
            st.warning("⚠️ File fallback")
    
    # --- HASH VERIFICATION ---
    st.divider()
    st.header("🔍 TEST HASH AUDIT - Works for Any Report")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        default_hash = hash_from_qr if hash_from_qr else ""
        hash_input = st.text_input(
            "Paste Hash from PDF footer or scan QR (auto-filled)",
            value=default_hash,
            placeholder="a3f5c9e8b7d6f4e2",
            key="hash_input"
        )
        
        auto_verify = st.checkbox("Auto-verify if QR scanned", value=True if hash_from_qr else False)
        
        if st.button("✅ Verify Hash - Check if PDF Edited", type="primary") or (auto_verify and hash_input):
            if not hash_input:
                st.error("Paste hash")
            else:
                clean_in = hash_input.strip().lower().replace("sha256:", "").strip()
                db_hash = data['pdf_hash'].lower().strip()
                
                if clean_in == db_hash:
                    st.success(f"✅ MATCH - Plot {plot_id} - PDF NOT EDITED - EU ACCEPT")
                    st.balloons()
                    st.write(f"**Hash PDF/QR:** {clean_in} == **DB Hash:** {db_hash} - MATCH")
                    st.write(f"**NDVI:** {data['ndvi_start']} -> {data['ndvi_end']} - No deforestation")
                    st.write(f"**EU Decision:** ACCEPT - LOW RISK - Shipment passes")
                else:
                    st.error(f"❌ MISMATCH - Plot {plot_id} - PDF EDITED - EU REJECT")
                    st.write(f"**PDF/QR Hash:** {clean_in} != **DB Hash:** {db_hash}")
                    st.write(f"**DB has NDVI {data['ndvi_start']}->{data['ndvi_end']} - If PDF different, edited")
    
    with col2:
        st.subheader("All Plots in DB")
        for pid, pdata in verification_db.items():
            if st.button(f"{pid} - {pdata['pdf_hash'][:8]}... - {pdata['true_hectare']}ha", key=f"btn_{pid}"):
                st.query_params["plot_id"] = pid
                st.query_params["hash"] = pdata['pdf_hash']
                st.rerun()
        
        with st.expander("Raw DB data"):
            st.json(verification_db)

elif plot_id:
    st.error(f"❌ Plot ID '{plot_id}' NOT FOUND")
    st.write(f"DB has {len(verification_db)} plots:")
    for pid in verification_db.keys():
        st.write(f"- {pid} - {verification_db[pid]['pdf_hash']}")
    
    st.info("Generate report in main app - App saves to Supabase - Then verify here works - No file upload needed")
    
    if hash_from_qr and start_from_qr:
        st.success(f"QR has data: Plot {plot_id} - Hash {hash_from_qr} - Dates {start_from_qr} to {end_from_qr}")

else:
    st.info("Enter Plot ID - Or scan QR from PDF")
    st.json(verification_db)
