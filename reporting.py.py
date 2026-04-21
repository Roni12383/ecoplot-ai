import os
import datetime

# Try to import FPDF (specifically fpdf2)
try:
    from fpdf import FPDF
except ImportError:
    print("Error: fpdf2 library not found. Install it using 'pip install fpdf2'")


    # Define a dummy class to prevent NameError crash if library is missing
    class FPDF:
        pass


class EcoPlotReport(FPDF):
    def header(self):
        # Logo handling
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 33)
        else:
            # Placeholder if logo is missing
            self.set_draw_color(200, 200, 200)
            self.rect(10, 8, 33, 20)
            self.set_font("helvetica", size=8)
            self.text(12, 18, "LOGO PLACEHOLDER")

        # Header Title
        self.set_font("helvetica", 'B', 20)
        self.cell(80)
        self.cell(110, 10, "EcoPlot AI", align='R', new_x="LMARGIN", new_y="NEXT")

        self.set_font("helvetica", 'I', 10)
        self.cell(80)
        self.cell(110, 10, "Decarbonizing the Energy Sector", align='R', new_x="LMARGIN", new_y="NEXT")

        self.ln(5)
        self.line(10, 45, 200, 45)  # Horizontal separator
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()} | ESG Confidential', align='C')


def create_pdf_report(farm_name, area, carbon_tons, output_filename=None):
    """
    Generates a professional ESG Carbon report.
    """
    # Ensure FPDF is available before running logic
    if FPDF.__module__ == '__main__':
        return None

    pdf = EcoPlotReport()
    pdf.add_page()

    # 1. Title
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, "ESG Verification Report", align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 10, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", align='C', new_x="LMARGIN",
             new_y="NEXT")
    pdf.ln(10)

    # 2. Project Summary Table
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, "Project Information", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=11)

    # Table Rows
    pdf.cell(95, 10, "Farm/Project Name:", border=1)
    pdf.cell(95, 10, f"{farm_name}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(95, 10, "Total Managed Area:", border=1)
    pdf.cell(95, 10, f"{area:.2f} Hectares", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # 3. Carbon Data Highlights
    pdf.set_fill_color(230, 255, 230)  # Light green highlight
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 15, f"Verified Carbon Offset: {carbon_tons:.2f} Tons CO2e", align='C', fill=True, border=1,
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # 4. Verification Statement
    pdf.set_font("helvetica", 'I', 9)
    pdf.multi_cell(0, 5, "Verification Statement: This data is generated via the EcoPlot AI dMRV protocol, "
                         "utilizing ground-truth soil sensors and GIS-based landscape modeling. "
                         "This report is audit-ready for Scope 3 emissions offsetting.")

    if output_filename:
        pdf.output(output_filename)
        return output_filename
    else:
        # Returns as bytearray for Streamlit download button
        return pdf.output()
