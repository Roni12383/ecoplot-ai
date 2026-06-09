import os
import datetime
from fpdf import FPDF


class EcoPlotReport(FPDF):
    def header(self):
        logo_path = "logo.png"

        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 33)
        else:
            self.set_draw_color(200, 200, 200)
            self.rect(10, 8, 33, 20)
            self.set_font("helvetica", size=8)
            self.text(12, 18, "LOGO PLACEHOLDER")

        self.set_font("helvetica", "B", 20)
        self.cell(80)
        self.cell(110, 10, "EcoPlot AI", align="R", new_x="LMARGIN", new_y="NEXT")

        self.set_font("helvetica", "I", 10)
        self.cell(80)
        self.cell(
            110,
            10,
            "Decarbonizing the Energy Sector",
            align="R",
            new_x="LMARGIN",
            new_y="NEXT"
        )

        self.ln(5)
        self.line(10, 45, 200, 45)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} | ESG Confidential", align="C")


def create_pdf_report(
    farm_name,
    area,
    carbon_tons,
    growth_rate=0.0,
    avg_ndvi=None,
    current_ndvi=None,
    output_filename=None
):
    """
    Create a PDF report and return bytes suitable for Streamlit download.
    """

    pdf = EcoPlotReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "ESG Verification Report", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", size=10)
    pdf.cell(
        0,
        10,
        f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT"
    )
    pdf.ln(10)

    # Project Information
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Project Information", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", size=11)
    pdf.cell(95, 10, "Farm/Project Name:", border=1)
    pdf.cell(95, 10, str(farm_name), border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.cell(95, 10, "Total Managed Area:", border=1)
    pdf.cell(95, 10, f"{area:.2f} Hectares", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Vegetation Metrics
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Vegetation Metrics", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", size=11)

    pdf.cell(95, 10, "Current NDVI:", border=1)
    pdf.cell(
        95,
        10,
        f"{current_ndvi:.4f}" if current_ndvi is not None else "N/A",
        border=1,
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.cell(95, 10, "Average Annual NDVI:", border=1)
    pdf.cell(
        95,
        10,
        f"{avg_ndvi:.4f}" if avg_ndvi is not None else "N/A",
        border=1,
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.cell(95, 10, "Growth Rate:", border=1)
    pdf.cell(
        95,
        10,
        f"{growth_rate * 100:.2f}%",
        border=1,
        new_x="LMARGIN",
        new_y="NEXT"
    )
    pdf.ln(10)

    # Carbon result
    pdf.set_fill_color(230, 255, 230)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(
        0,
        15,
        f"Verified Carbon Offset: {carbon_tons:.2f} Tons CO2e",
        align="C",
        fill=True,
        border=1,
        new_x="LMARGIN",
        new_y="NEXT"
    )
    pdf.ln(10)

    # Analysis summary
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Analysis Summary", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", size=10)

    if growth_rate > 0.10:
        trend_text = "Vegetation health is improving strongly over time."
    elif growth_rate > 0:
        trend_text = "Vegetation health shows moderate positive growth."
    elif growth_rate == 0:
        trend_text = "Vegetation health appears stable or insufficient data was available."
    else:
        trend_text = "Vegetation health shows signs of decline and may require intervention."

    summary_text = (
        f"This report uses satellite-derived NDVI analysis to estimate vegetation performance "
        f"and carbon sequestration potential for the selected project area. "
        f"The estimated carbon offset is {carbon_tons:.2f} tons CO2e across {area:.2f} hectares. "
        f"{trend_text}"
    )

    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(5)

    # Verification statement
    pdf.set_font("helvetica", "I", 9)
    pdf.multi_cell(
        0,
        5,
        "Verification Statement: This data is generated via the EcoPlot AI dMRV protocol, "
        "utilizing satellite observations, GIS-based landscape analysis, and automated reporting logic. "
        "This report is intended to support ESG documentation and carbon project screening."
    )

    if output_filename:
        pdf.output(output_filename)
        return output_filename

    return bytes(pdf.output(dest="S"))
