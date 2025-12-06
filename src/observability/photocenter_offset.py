"""
Photocenter-Barycenter Offset Module
Category G6: Advanced Observations [LOW]

If Planet 9 has large moon(s), the photocenter (bright spot) wobbles
around the barycenter. This creates positional uncertainty.

Impact: Search box must be larger to account for moon-induced wobble.

Reference: Batygin & Brown (2016) uncertainty budget
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PHOTOCENTER - %(message)s')

class PhotocenterOffset:
    """Models offset between brightness center and mass center."""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        logging.info(f"Photocenter Offset: {'ENABLED' if enabled else 'DISABLED'}")
    
    def calculate_moon_induced_wobble(self, m_planet_earth, m_moon_fraction=0.01,
                                     a_moon_planet_radii=10, distance_au=500):
        """
        Calculate wobble amplitude from moon.
        
        Args:
            m_planet_earth: Planet mass (Earth masses)
            m_moon_fraction: Moon mass / Planet mass
            a_moon_planet_radii: Moon distance (planet radii)
            distance_au: Distance to observer (AU)
        
        Returns:
            dict: Wobble parameters
        """
        if not self.enabled:
            return {'wobble_arcsec': 0.0}
        
        # Barycenter offset = a * (M_moon / (M_planet + M_moon))
        offset_fraction = m_moon_fraction / (1 + m_moon_fraction)
        
        # Convert to physical distance
        R_earth_km = 6371
        R_planet_km = R_earth_km * (m_planet_earth / 5)**(1/3)  # Mass-radius
        offset_km = offset_fraction * a_moon_planet_radii * R_planet_km
        
        # Convert to angular wobble at distance
        au_to_km = 149597870.7
        distance_km = distance_au * au_to_km
        wobble_rad = offset_km / distance_km
        wobble_arcsec = wobble_rad * 206265
        
        result = {
            'moon_mass_fraction': m_moon_fraction,
            'offset_km': offset_km,
            'wobble_arcsec': wobble_arcsec,
            'distance_au': distance_au
        }
        
        logging.info(f"Photocenter Analysis:")
        logging.info(f"  Moon mass: {m_moon_fraction*100:.1f}% of planet")
        logging.info(f"  Physical offset: {offset_km:.0f} km")
        logging.info(f"  Angular wobble: {wobble_arcsec:.3f} arcsec")
        
        return result
    
    def search_box_expansion(self, base_uncertainty_arcmin=5, 
                            wobble_arcsec=0.05, confidence_level=0.99):
        """
        Calculate expanded search box accounting for photocenter wobble.
        
        Args:
            base_uncertainty_arcmin: Baseline position uncertainty (arcmin)
            wobble_arcsec: Photocenter wobble amplitude (arcsec)
            confidence_level: Confidence level (0-1)
        
        Returns:
            dict: Search box parameters
        """
        # Convert to same units
        base_uncertainty_arcsec = base_uncertainty_arcmin * 60
        
        # Total uncertainty (quadrature sum)
        total_uncertainty = np.sqrt(base_uncertainty_arcsec**2 + wobble_arcsec**2)
        
        # Expand for confidence level (Gaussian)
        # 99% = 2.58 sigma
        sigma_factor = {
            0.68: 1.0,
            0.95: 1.96,
            0.99: 2.58,
            0.999: 3.29
        }.get(confidence_level, 2.58)
        
        search_radius = total_uncertainty * sigma_factor
        
        # Area
        search_area_arcsec2 = np.pi * search_radius**2
        search_area_arcmin2 = search_area_arcsec2 / 3600
        
        result = {
            'base_uncertainty_arcsec': base_uncertainty_arcsec,
            'wobble_arcsec': wobble_arcsec,
            'total_uncertainty_arcsec': total_uncertainty,
            'search_radius_arcsec': search_radius,
            'search_area_arcmin2': search_area_arcmin2,
            'confidence_level': confidence_level
        }
        
        logging.info(f"\nSearch Box:")
        logging.info(f"  Base uncertainty: {base_uncertainty_arcsec:.1f} arcsec")
        logging.info(f"  Wobble: {wobble_arcsec:.3f} arcsec")
        logging.info(f"  Total: {total_uncertainty:.1f} arcsec")
        logging.info(f"  Search radius ({confidence_level*100:.0f}%): {search_radius:.1f} arcsec")
        logging.info(f"  Search area: {search_area_arcmin2:.2f} arcmin²")
        
        return result


if __name__ == "__main__":
    print("=== Testing Photocenter Offset ===\n")
    
    photocenter = PhotocenterOffset(enabled=True)
    
    # Calculate wobble for 5 M⊕ planet with 1% mass moon
    wobble = photocenter.calculate_moon_induced_wobble(
        m_planet_earth=5.0,
        m_moon_fraction=0.01,  # 1% (like Earth-Moon ~1.2%)
        a_moon_planet_radii=10,
        distance_au=500
    )
    
    # Calculate expanded search box
    search = photocenter.search_box_expansion(
        base_uncertainty_arcmin=5,
        wobble_arcsec=wobble['wobble_arcsec'],
        confidence_level=0.99
    )
    
    print(f"\nConclusion:")
    if wobble['wobble_arcsec'] > 0.1:
        print(f"  Significant wobble - expand search box")
    else:
        print(f"  Negligible wobble - standard search OK")
