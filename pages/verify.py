import streamlit as st
import hashlib
from datetime import datetime
import json
import os

# --- GET PARAMS FROM URL - FIXED ---
plot_id_raw = st.query_params.get("plot_id", "")
hash_from_qr = st.query_params.get("hash", "")
# IGNORE these - Do NOT use them to recompute hash, they are for display only
start_from_qr = st.query_params.get("start", "")
end_from_qr = st.query_params.get("end", "")
ndvi_start_from_qr = st.query_params.get("ndvi_start", "")
ndvi_end_from_qr = st.query_params.get("ndvi_end", "")

# Normalize - FIX FOR ZIP: Shapefile Plot_ID often has space / lowercase
plot_id = str(plot_id_raw).strip().upper() if plot_id_raw else ""
hash_from_qr = str(hash_from_qr).strip().lower() if hash_from_qr else ""

if not plot_id:
    st.title("🔍 EcoPlotAI - EUDR V2 Verification Portal - Supabase Persistent")
    st.info("Public verification - No login - EU auditor can verify hash - Supabase persistent DB - Works for unlimited reports")
    plot_id_input = st.text_input("Enter Plot ID / Farm Name (e.g., JGW-RONI-012)", "")
    if plot_id_input:
        plot_id = str(plot_id_input).strip().upper()
        st.query_params["plot_id"] = plot_id
        st.rerun()
    else:
        st.stop()
else:
    st.title(f"✅ Verification: {plot_id} - EUDR V2 DDS-Ready - Supabase")

# --- LOOKUP - NEVER RECOMPUTE HASH ---
found = None
lookup_error = ""

# 1. Try Supabase first
try:
    supabase_client = st.session_state.get('supabase_client', None)
    if supabase_client is not None:
        # Try normalized ID first
        res = supabase_client.table("eudr_verification").select("*").eq("plot_id", plot_id).execute()
        if res.data:
            found = res.data[0]
        else:
            # Try raw ID (for old ZIP uploads with space / lowercase)
            res2 = supabase_client.table("eudr_verification").select("*").eq("plot_id", plot_id_raw).execute()
            if res2.data:
                found = res2.data[0]
            else:
                # Try case-insensitive scan - last resort for ZIP bug
                all_rows = supabase_client.table("eudr_verification").select("*").execute()
                for row in all_rows.data:
                    if str(row.get("plot_id","")).strip().upper() == plot_id:
                        found = row
                        break
except Exception as e:
    lookup_error = str(e)

# 2. Fallback to local file DB
if not found:
    try:
        if os.path.exists("verification_db.json"):
            with open("verification_db.json") as f:
                db = json.load(f)
            for k, v in db.items():
                if str(k).strip().upper() == plot_id:
                    found = v
                    break
    except Exception as e:
        lookup_error = str(e)

# --- COMPARE ---
if not found:
    st.error(f"❌ Plot {plot_id} NOT FOUND")
    st.write(f"Supabase error: {lookup_error}")
    st.info("Tip: This happens for ZIP uploads if Plot_ID in .dbf has a space. Re-upload ZIP after fixing Plot_ID, or search with exact Plot_ID from shapefile.")
    st.stop()

# Found - Compare stored hash vs QR hash
stored_hash = str(found.get("pdf_hash", "")).strip().lower()

st.write(f"**Plot ID:** {found.get('plot_id', plot_id)}")
st.write(f"**Hash from QR / PDF:** `{hash_from_qr}`")
st.write(f"**Hash in Supabase:** `{stored_hash}`")

# If user came via manual input (no hash in URL), show stored hash as verified
if not hash_from_qr:
    st.success(f"✅ FOUND - Plot {plot_id} exists in Supabase")
    st.write(f"Stored Hash: `{stored_hash}`")
    st.write(f"Farm: {found.get('farm_name')}")
    st.write(f"Area: {found.get('true_hectare')} ha")
    st.write(f"Risk: {found.get('risk')} | {found.get('compliant')}")
    st.write(f"NDVI: {found.get('ndvi_start')} → {found.get('ndvi_end')} | Dates: {found.get('start_date')} to {found.get('end_date')}")
    st.stop()

if stored_hash == hash_from_qr and stored_hash != "":
    st.success(f"✅ VERIFIED - Authentic - Plot {plot_id}")
    st.balloons()
    st.write(f"**Farm:** {found.get('farm_name')}")
    st.write(f"**Area:** {found.get('true_hectare')} ha")
    st.write(f"**Center:** {found.get('center_lat')}, {found.get('center_lon')}")
    st.write(f"**Risk:** {found.get('risk')} | **Compliant:** {found.get('compliant')}")
    st.write(f"**NDVI:** {found.get('ndvi_start')} → {found.get('ndvi_end')} (Change: {found.get('ndvi_change')})")
    st.write(f"**Dates:** {found.get('start_date')} to {found.get('end_date')}")
    st.write(f"**Source:** {found.get('source')}")
    if start_from_qr:
        st.caption(f"QR Params (display only): {start_from_qr} to {end_from_qr} | NDVI {ndvi_start_from_qr} → {ndvi_end_from_qr}")
else:
    st.error(f"❌ MISMATCH - Certificate Tampered or Old Version")
    st.write(f"URL hash: `{hash_from_qr}`")
    st.write(f"DB hash: `{stored_hash}`")
    st.write("Generate a NEW PDF after the fix. Old ZIP PDFs are invalid.")
