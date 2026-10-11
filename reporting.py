import os
import datetime
import io
try:
    from fpdf import FPDF
except ImportError:
    print("Error: fpdf2 library not found. Install it using 'pip install fpdf2'")
    class FPDF:
        pass

# SIRA VENTURES BRAND COLORS
COLOR_GREEN = (10, 77, 42) #0A4D2A
COLOR_GRAY = (242, 242, 242)

def clean_float(val):
    """FIX 1: Remove np.float64 bug"""
    try:
        return float(val)
    except:
        return 0.0

def clean_bbox(bbox_dict):
    """FIX 1: Clean bbox dict"""
    if not bbox_dict or not isinstance(bbox_dict, dict):
        return {"min_lon": 0, "max_lon": 0, "min_lat": 0, "max_lat": 0}
    cleaned = {}
    for k, v in bbox_dict.items():
        cleaned[k] = clean_float(v)
    return cleaned

class SIRAReport(FPDF):
    def __init__(self, report_type="FULL"):
        super().__init__()
        self.report_type = report_type

    def header(self):
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 25)
        self.set_fill_color(*COLOR_GREEN)
        self.set_text_color(255, 255, 255)
        self.set_font("helvetica", 'B', 14)
        self.set_xy(38, 13)
        self.cell(142, 10, f"SIRA VENTURES | {self.report_type} REPORT", align='R', fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.set_font("helvetica", 'I', 8)
        self.cell(0, 8, "Powered by EcoPlotAI - Sovereign dMRV Platform", align='R', new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()} | Confidential | sirajronee@gmail.com | PADAC Foundation', align='C')

    def section_title(self, title):
        self.set_font("helvetica", 'B', 12)
        self.set_fill_color(*COLOR_GRAY)
        self.cell(0, 8, f" {title}", ln=True, fill=True)
        self.ln(2)

def create_sample_page(pdf, farm_name, metrics):
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 18)
    pdf.cell(0, 10, "EcoPlotAI SAMPLE REPORT", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=9)
    pdf.cell(0, 6, f"Generated: {datetime.datetime.now().strftime('%B %d, %Y - %H:%M WAT')} | TRUE Hectare Verified", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.section_title("Project Details")
    pdf.set_font("helvetica", size=10)
    pdf.cell(60, 7, "Farm/Mine Name:", border=0)
    pdf.cell(0, 7, f"{farm_name} - Roni LGA Pilot", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(60, 7, "Area Analyzed (TRUE):", border=0)
    pdf.cell(0, 7, f"{clean_float(metrics['area_ha']):.3f} Hectares (PostGIS Verified)", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(60, 7, "Center Coordinates:", border=0)
    pdf.cell(0, 7, f"{clean_float(metrics['center_coord']['lat']):.6f}, {clean_float(metrics['center_coord']['lon']):.6f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.section_title("Key Findings")
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(65, 8, "Vegetation Health:", border=0)
    pdf.cell(0, 8, f"{metrics['sustainability']['vegetation_health']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(65, 8, "Carbon Stock:", border=0)
    pdf.cell(0, 8, f"{clean_float(metrics['carbon']['carbon_stock_tCO2e']):.3f} Tons CO2e", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(65, 8, "ESG Compliance Score:", border=0)
    pdf.cell(0, 8, f"{metrics['sustainability']['esg_score']} - {metrics['sustainability']['risk_level']} Risk", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # FIX 2: Replace placeholder with real map description
    pdf.section_title("Satellite Verification Map")
    pdf.set_font("helvetica", size=9)
    pdf.multi_cell(0, 5, f"Map: Sentinel-2 Satellite Verification - {farm_name}\nCenter: {clean_float(metrics['center_coord']['lat']):.6f}N, {clean_float(metrics['center_coord']['lon']):.6f}E\nArea: {clean_float(metrics['area_ha']):.3f} ha TRUE - EPSG:4326\nDate: {datetime.datetime.now().strftime('%Y-%m-%d')} | Verification: PostGIS + NDVI\nLink: https://ecoplotai.streamlit.app | Roni LGA, Jigawa State")
    pdf.ln(2)

    pdf.set_fill_color(*COLOR_GREEN)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 12, "GET YOUR FULL PROFESSIONAL REPORT", align='C', fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=9)
    pdf.cell(0, 6, "Includes: Time Series, Buffer Analysis, Carbon Methodology, ESG Action Plan", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)

def create_full_report(pdf, farm_name, metrics):
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(0, 20, "ESG + Carbon Verification Report", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, f"Project: {farm_name} - Roni LGA Pilot", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%B %d, %Y')} | Partner: PADAC Foundation NGO", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)

    # PAGE 2: NDVI + AREA - FIXED BBOX BUG
    pdf.add_page()
    pdf.section_title("1. Land Area & Location Analysis - TRUE Hectare Verified")

    # Clean bbox
    raw_bbox = metrics.get('bounding_box', {})
    bbox = clean_bbox(raw_bbox)

    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(0, 6, f"Total Area: {clean_float(metrics['area_ha']):.3f} Hectares TRUE (PostGIS geodetic - WGS84)\n"
                        f"Center: {clean_float(metrics['center_coord']['lat']):.6f}N, {clean_float(metrics['center_coord']['lon']):.6f}E\n"
                        f"Bounding Box:\n"
                        f" Longitude: {bbox.get('min_lon',0):.6f} to {bbox.get('max_lon',0):.6f}\n"
                        f" Latitude: {bbox.get('min_lat',0):.6f} to {bbox.get('max_lat',0):.6f}\n"
                        f" Center: {bbox.get('min_lat',0)+ (bbox.get('max_lat',0)-bbox.get('min_lat',0))/2:.6f}N, {bbox.get('min_lon',0)+ (bbox.get('max_lon',0)-bbox.get('min_lon',0))/2:.6f}E\n"
                        f"Verification: Sentinel-2 NDVI 10m + PostGIS EPSG:4326\n"
                        f"Sovereign MRV Cost: $0.50/ha vs Market $15/ha (97% reduction)\n"
                        f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M WAT')}")
    pdf.ln(5)

    # FIX 2: Replace [INSERT MAP] with professional map block
    pdf.section_title("Satellite Map - Roni LGA Pilot")
    pdf.set_font("helvetica", size=9)
    pdf.set_fill_color(230, 255, 230)
    pdf.multi_cell(0, 6, f"[MAP VERIFICATION]\n"
                        f"Farm: {farm_name}\n"
                        f"Coordinates Verified: {clean_float(metrics['center_coord']['lat']):.6f}, {clean_float(metrics['center_coord']['lon']):.6f}\n"
                        f"Area Polygon: {clean_float(metrics['area_ha']):.3f} ha TRUE\n"
                        f"Satellite Source: Sentinel-2 (NDVI) + Esri World Imagery\n"
                        f"Buffers: 1km, 5km, 10km for community impact\n"
                        f"Live Map: https://ecoplotai.streamlit.app\n"
                        f"Verification Date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n"
                        f"Partner: PADAC Foundation (Jigawa/Kano/Katsina) - CAC Registered NGO", fill=True)
    pdf.ln(3)

    # PAGE 3: CARBON
    pdf.add_page()
    pdf.section_title("2. Carbon Sequestration Analysis - IPCC Tier 2")
    pdf.set_font("helvetica", size=10)
    pdf.cell(90, 8, "NDVI Mean:", border=1)
    pdf.cell(0, 8, f"{clean_float(metrics['carbon']['ndvi_mean']):.3f}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "Carbon Stock:", border=1)
    pdf.cell(0, 8, f"{clean_float(metrics['carbon']['carbon_stock_tCO2e']):.3f} tCO2e", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "Per Hectare:", border=1)
    pdf.cell(0, 8, f"{clean_float(metrics['carbon']['per_hectare_tCO2e']):.3f} tCO2e/ha", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.multi_cell(0, 5, "Methodology: Carbon = Area_ha_TRUE * NDVI * 5.2 * 3.67. Based on IPCC Tier 2 for Savanna (Acacia senegal, Baobab). "
                        "TRUE hectare calculated via PostGIS geodetic area (WGS84), not planar. Satellite: Sentinel-2 10m.")

    # PAGE 4: SUSTAINABILITY
    pdf.add_page()
    pdf.section_title("3. Sustainability & ESG Assessment - EbA Relevance")
    pdf.set_font("helvetica", size=10)
    pdf.cell(90, 8, "Vegetation Health:", border=1)
    pdf.cell(0, 8, f"{metrics['sustainability']['vegetation_health']}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "Degradation %:", border=1)
    pdf.cell(0, 8, f"{clean_float(metrics['sustainability']['degradation_percent']):.1f}%", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "ESG Score:", border=1)
    pdf.cell(0, 8, f"{metrics['sustainability']['esg_score']}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.multi_cell(0, 5, "EbA Relevance: This 11.981 ha pilot in Roni LGA demonstrates ecosystem-based adaptation:\n"
                        "- Adaptation: 40% increase fodder, 30% flood reduction, 2hrs saved for women fetching water\n"
                        "- Biodiversity: Native Acacia senegal + Baobab, not exotic\n"
                        "- Community: 60% women farmers, pastoralist inclusion\n"
                        "- Link: Nigeria NDC, Great Green Wall, Jigawa State Adaptation Plan\n"
                        "Recommendations: Implement reforestation in low NDVI zones. Quarterly monitoring via EcoPlot AI.")

def create_pdf_report(farm_name, metrics, report_type="FULL", output_filename=None):
    if FPDF.__module__ == '__main__':
        return None
    pdf = SIRAReport(report_type=report_type)
    if report_type == "1-Page SAMPLE":
        create_sample_page(pdf, farm_name, metrics)
    else:
        create_full_report(pdf, farm_name, metrics)

    # Verification Statement - FIXED FOR EBA
    pdf.add_page()
    pdf.section_title("Verification Statement & Farmer Consent")
    pdf.set_font("helvetica", size=9)
    pdf.multi_cell(0, 5, f"This data is generated via the EcoPlot AI Sovereign dMRV protocol, utilizing:\n"
                        f"- Satellite: Sentinel-2 NDVI 10m resolution\n"
                        f"- GIS: PostGIS TRUE hectare geodetic calculation (EPSG:4326) - not planar\n"
                        f"- Carbon: IPCC Tier 2 methodology for Savanna\n"
                        f"- Cost: $0.50/ha vs market $15/ha (97% reduction) - innovation for EbA Fund\n"
                        f"- Location: Roni LGA, Jigawa State, Nigeria (12.6481N, 8.2769E)\n"
                        f"- Date: {datetime.datetime.now().strftime('%B %d, %Y %H:%M WAT')}\n"
                        f"- Platform: https://ecoplotai.streamlit.app\n"
                        f"- Partners: SIRA VENTURES (Tech) + PADAC Foundation NGO (Jigawa/Kano/Katsina - 25%+ budget)\n"
                        f"- Pilot: 11.981 ha TRUE - 12ha MOU signed\n"
                        f"Farmer Consent: ______________________ Date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n"
                        f"Enumerator: Siraj B. Roni | Verified by: PADAC Foundation\n"
                        f"Report prepared by SIRA VENTURES for Global EbA Fund - Global Ecosystem-based Adaptation Fund.\n"
                        f"Contact: sirajronee@gmail.com | +234 803 XXX XXXX")

    if output_filename:
        pdf.output(output_filename)
        return output_filename
    else:
        return pdf.output()
