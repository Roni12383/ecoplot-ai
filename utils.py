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
