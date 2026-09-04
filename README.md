# 🌱 EcoPlotAI: Landscape Restoration Planner
### Powered by SIRA VENTURES + Xeelaa Integration

EcoPlotAI is a dMRV platform that turns satellite data into audit-ready ESG + Carbon reports in 30 seconds. Built for farmers, miners, and developers in Nigeria.

---

### **Problem**
ESG reporting in Africa is slow, expensive, and manual. Companies need verifiable data on land area, vegetation health, and carbon sequestration to access climate finance and meet compliance.

### **Solution**
EcoPlotAI uses Google Earth Engine + NDVI + GIS to automatically calculate:
1.  **Land Area & Coordinates**: Accurate 1-hectare boundary mapping
2.  **Carbon Stock**: tCO2e calculated from NDVI * Area * IPCC factors  
3.  **ESG Score**: Vegetation health, degradation risk, and compliance rating A/B/C
4.  **Professional Reports**: 1-Page SAMPLE for leads, FULL Report for clients

All branded under **SIRA VENTURES**.

---

### **Key Features for Startup Abuja Innovation Challenge**

| Feature | Tech Used | Why It Matters |
| --- | --- | --- |
| **Live Satellite Analysis** | Google Earth Engine, Sentinel-2 | Real-time NDVI, no field visit needed |
| **Carbon Calculation** | Custom IPCC Tier 2 Formula | Audit-ready for carbon credits |
| **Buffer Analysis** | GeoPandas, Shapely | 100m / 500m compliance zones |
| **PDF Report Generator** | FPDF2 | SIRA branded, SAMPLE vs FULL toggle |
| **Xeelaa AI Assistant** | Xeelaa API + Widget | Multilingual farm advisor in Hausa/English. Required for challenge. |

---

### **How to Use**
1.  Enter `Latitude` and `Longitude` in sidebar
2.  Click `Fetch Live NDVI` to get current vegetation
3.  Choose `Report Type`: `1-Page SAMPLE` or `FULL Report`
4.  Click `Analyze Farm & Generate Report`
5.  Download PDF with SIRA branding

You can also ask **Xeelaa - EcoPlotAI Assistant** questions in Hausa or English.

---

### **Tech Stack**
`Streamlit` | `Google Earth Engine` | `GeoPandas` | `Folium` | `FPDF2` | `Plotly` | `Xeelaa API`

### **Installation**
```bash
pip install -r requirements.txt
streamlit run app.py

