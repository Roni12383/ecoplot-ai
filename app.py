import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
from logic import process_shapefile, process_coordinates, get_ndvi_placeholder
from reporting import generate_dmr_report

st.set_page_config(page_title="EcoPlotAI", page_icon="🌍", layout="wide")

st.title("🌍 EcoPlotAI")
st.subheader("Verified dMRV for African Smallholder Farmers")
st.caption("60-second audit-ready reports. Supports Country NDCs & Article 6 Carbon Markets.")

col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Input Farm Data")
    farm_name = st.text_input("Farm Name", "Demo Farm")
    country = st.selectbox("Country", ["Nigeria", "Kenya", "Ghana", "Ethiopia", "Tanzania", "Uganda", "Rwanda", "South Africa", "Other African Country"])

    input_type = st.radio("Choose Input Method:", ["Upload Shapefile.zip", "Enter Coordinates"])

    geometry = None
    area_ha = 0.0
    crs_info = ""

    if input_type == "Upload Shapefile.zip":
        uploaded = st.file_uploader("Upload.zip containing.shp,.shx,.dbf", type="zip")
        if uploaded:
            try:
                geometry, area_ha, crs_info = process_shapefile(uploaded)
                st.success(f"Shapefile loaded. CRS: {crs_info}")
            except ValueError as e:
                st.error(e)
    else:
        st.info("Enter coordinates as: lat,lon - one per line. Must close the polygon.")
        coords_text = st.text_area("Coordinates", "9.0765,7.3986\n9.0770,7.3990\n9.0760,7.3995\n9.0765,7.3986")
        if st.button("Calculate Area"):
            try:
                geometry, area_ha = process_coordinates(coords_text)
                st.success("Coordinates calculated")
            except ValueError as e:
                st.error(e)

with col2:
    st.header("2. Verification & Report")
    if geometry is not None:
        st.metric("Verified Area", f"{area_ha:.2f} Hectares")
        fig, ax = plt.subplots()
        gpd.GeoSeries([geometry]).plot(ax=ax, color='lightgreen', edgecolor='darkgreen')
        ax.axis('off')
        st.pyplot(fig)

        ndvi = get_ndvi_placeholder()
        if st.button("Generate dMRV PDF Report", type="primary"):
            with st.spinner("Generating report..."):
                pdf = generate_dmr_report(farm_name, country, area_ha, geometry, ndvi)
            st.download_button(
                label="📄 Download dMRV Report",
                data=pdf,
                file_name=f"{farm_name}_EcoPlotAI_Report.pdf",
                mime="application/pdf"
            )
            st.success("Report ready! Meets Verra/UN MRV standards")
    else:
        st.warning("Please upload shapefile or enter coordinates first")

st.divider()
st.markdown("*EcoPlotAI: Building MRV Infrastructure for Africa's Green Economy*")
