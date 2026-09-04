import os
import datetime

try:
    from fpdf import FPDF
except ImportError:
    print("Error: fpdf2 library not found. Install it using 'pip install fpdf2'")
    class FPDF:
        pass

# SIRA VENTURES BRAND COLORS
COLOR_GREEN = (10, 77, 42)  #0A4D2A
COLOR_GRAY = (242, 242, 242)

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
        self.cell(0, 12, f"SIRA VENTURES | {self.report_type} REPORT", align='R', fill=True, new_x="LMARGIN", new_y="NEXT")
        
        self.set_text_color(0, 0, 0)
        self.set_font("helvetica", 'I', 8)
        self.cell(0, 8, "Powered by EcoPlotAI - dMRV Platform", align='R', new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()} | Confidential | contact@siraventures.com', align='C')

    def section_title(self, title):
        self.set_font("helvetica", 'B', 12)
        self.set_fill_color(*COLOR_GRAY)
        self.cell(0, 8, f" {title}", ln=True, fill=True)
        self.ln(2)

def create_sample_page(pdf, farm_name, metrics):
    """ 1-PAGE SAMPLE FOR LEADS """
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 18)
    pdf.cell(0, 10, "EcoPlotAI SAMPLE REPORT", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=9)
    pdf.cell(0, 6, f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d')}", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Project Info
    pdf.section_title("Project Details")
    pdf.set_font("helvetica", size=10)
    pdf.cell(60, 7, "Farm/Mine Name:", border=0)
    pdf.cell(0, 7, f"{farm_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(60, 7, "Area Analyzed:", border=0)
    pdf.cell(0, 7, f"{metrics['area_ha']:.2f} Hectares", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(60, 7, "Center Coordinates:", border=0)
    pdf.cell(0, 7, f"{metrics['center_coord']['lat']:.4f}, {metrics['center_coord']['lon']:.4f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Key KPIs
    pdf.section_title("Key Findings")
    pdf.set_font("helvetica", 'B', 11)
    pdf.cell(65, 8, "Vegetation Health:", border=0)
    pdf.cell(0, 8, f"{metrics['sustainability']['vegetation_health']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(65, 8, "Carbon Stock:", border=0)
    pdf.cell(0, 8, f"{metrics['carbon']['carbon_stock_tCO2e']} Tons CO2e", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(65, 8, "ESG Compliance Score:", border=0)
    pdf.cell(0, 8, f"{metrics['sustainability']['esg_score']} - {metrics['sustainability']['risk_level']} Risk", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Watermark for map placeholder
    pdf.section_title("NDVI Map")
    pdf.set_font("helvetica", 'I', 8)
    pdf.set_text_color(200, 200, 200)
    pdf.cell(0, 50, "[SATELLITE MAP GOES HERE]", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # CTA
    pdf.set_fill_color(*COLOR_GREEN)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 12, "GET YOUR FULL PROFESSIONAL REPORT", align='C', fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=9)
    pdf.cell(0, 6, "Includes: Time Series, Buffer Analysis, Carbon Methodology, ESG Action Plan", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)


def create_full_report(pdf, farm_name, metrics):
    """ FULL 5-PAGE REPORT FOR CLIENTS """
    pdf.add_page()
    # PAGE 1: COVER
    pdf.set_font("helvetica", 'B', 20)
    pdf.cell(0, 20, "ESG + Carbon Verification Report", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, f"Project: {farm_name}", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)

    # PAGE 2: NDVI + AREA
    pdf.add_page()
    pdf.section_title("1. Land Area & Location Analysis")
    pdf.set_font("helvetica", size=10)
    pdf.multi_cell(0, 6, f"Total Area: {metrics['area_ha']:.3f} Hectares\nCenter: {metrics['center_coord']['lat']:.4f}, {metrics['center_coord']['lon']:.4f}\nBounding Box: {metrics['bounding_box']}")
    pdf.ln(3)
    pdf.cell(0, 50, "[INSERT 1HA MAP + BUFFERS HERE]", align='C')

    # PAGE 3: CARBON
    pdf.add_page()
    pdf.section_title("2. Carbon Sequestration Analysis")
    pdf.set_font("helvetica", size=10)
    pdf.cell(90, 8, "NDVI Mean:", border=1)
    pdf.cell(0, 8, f"{metrics['carbon']['ndvi_mean']}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "Carbon Stock:", border=1)
    pdf.cell(0, 8, f"{metrics['carbon']['carbon_stock_tCO2e']} tCO2e", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "Per Hectare:", border=1)
    pdf.cell(0, 8, f"{metrics['carbon']['per_hectare_tCO2e']} tCO2e/ha", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.multi_cell(0, 5, "Methodology: Carbon = Area_ha * NDVI * 5.2 * 3.67. Based on IPCC Tier 2 for Savanna.")

    # PAGE 4: SUSTAINABILITY
    pdf.add_page()
    pdf.section_title("3. Sustainability & ESG Assessment")
    pdf.set_font("helvetica", size=10)
    pdf.cell(90, 8, "Vegetation Health:", border=1)
    pdf.cell(0, 8, f"{metrics['sustainability']['vegetation_health']}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "Degradation %:", border=1)
    pdf.cell(0, 8, f"{metrics['sustainability']['degradation_percent']}%", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(90, 8, "ESG Score:", border=1)
    pdf.cell(0, 8, f"{metrics['sustainability']['esg_score']}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.multi_cell(0, 5, "Recommendations: Implement reforestation in low NDVI zones. Quarterly monitoring advised.")

def create_pdf_report(farm_name, metrics, report_type="FULL", output_filename=None):
    """
    Generates a professional ESG Carbon report.
    metrics: dict from calculate_metrics()
    report_type: "SAMPLE" or "FULL"
    """
    if FPDF.__module__ == '__main__':
        return None

    pdf = SIRAReport(report_type=report_type)
    
    if report_type == "1-Page SAMPLE":
        create_sample_page(pdf, farm_name, metrics)
    else:
        create_full_report(pdf, farm_name, metrics)

    # Verification Statement
    pdf.add_page()
    pdf.section_title("Verification Statement")
    pdf.set_font("helvetica", 'I', 9)
    pdf.multi_cell(0, 5, "This data is generated via the EcoPlot AI dMRV protocol, utilizing satellite NDVI, "
                         "GIS-based modeling, and IPCC carbon factors. Report prepared by SIRA VENTURES.")

    if output_filename:
        pdf.output(output_filename)
        return output_filename
    else:
        # FIX FOR STREAMLIT CLOUD: Use bytearray directly
        return bytearray(pdf.output())

