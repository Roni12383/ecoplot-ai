import math


def calculate_buffer_radius(area_ha):
    """
    Calculates the radius of a circle in meters that corresponds to a given area in hectares.
    1 hectare = 10,000 square meters.
    Area of circle = pi * r^2
    r = sqrt(Area / pi)
    """
    if area_ha <= 0:
        return 0  # Cannot have a non-positive area
    area_sqm = area_ha * 10000  # Convert hectares to square meters
    radius = math.sqrt(area_sqm / math.pi)
    return radius


def create_pdf_report(farm_name, area, carbon_tons):
    """
    Generates a simple PDF report.
    This function should be in your reporting.py or utils.py.
    """
    from fpdf import FPDF  # Ensure fpdf2 is installed, not fpdf

    class PDF(FPDF):
        def header(self):
            # Logo (ensure 'logo.png' exists in your repo or remove this)
            logo_path = "logo.png"
            if os.path.exists(logo_path):
                self.image(logo_path, 10, 8, 33)
            else:
                self.set_font("Arial", 'B', 12)
                self.text(10, 20, "EcoPlot AI")

            self.set_font('Arial', 'B', 15)
            # Move to the right
            self.cell(80)
            # Title
            self.cell(110, 10, "ESG Report: Farm Assessment", align='R', ln=1)
            # Line break
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    pdf.cell(0, 10, f"Farm Name: {farm_name}", 0, 1)
    pdf.cell(0, 10, f"Assessed Area: {area:.2f} Hectares", 0, 1)
    pdf.cell(0, 10, f"Estimated Carbon Sequestration: {carbon_tons:.2f} Tons CO2eq", 0, 1)
    pdf.ln(10)
    pdf.cell(0, 10, "--- Detailed Analysis ---", 0, 1, 'C')
    pdf.cell(0, 10, "This report provides an estimate of vegetation health and carbon sequestration potential", 0, 1)
    pdf.cell(0, 10, "based on satellite data from Google Earth Engine.", 0, 1)
    pdf.cell(0, 10, "Higher NDVI values generally indicate healthier, denser vegetation.", 0, 1)
    pdf.ln(10)

    # Placeholder for more detailed content
    pdf.multi_cell(0, 10, "Further analysis, including historical trends and land cover classification, "
                          "can be found in the EcoPlot AI dashboard. Carbon sequestration estimates are "
                          "based on scientific models and should be verified with ground truth data.")

    return pdf.output()
