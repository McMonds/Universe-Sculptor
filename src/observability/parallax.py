"""
Parallax Correction Module
Category G1: Observational Predictions [CRITICAL]

Converts barycentric coordinates (from simulation) to topocentric coordinates
(where to point the telescope tonight).

Earth moves → apparent position of Planet 9 shifts by several degrees.
Without this correction, your coordinates are useless for observers.
"""
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PARALLAX - %(message)s')

class ParallaxCorrector:
    """
    Calculates apparent position from Earth's surface.
    
    Barycentric (sim) → Heliocentric → Geocentric → Topocentric (telescope)
    """
    
    def __init__(self, observer_lat=0.0, observer_lon=0.0, observer_alt=0.0):
        """
        Args:
            observer_lat: Latitude (degrees)
            observer_lon: Longitude (degrees) 
            observer_alt: Altitude (km)
        """
        self.observer_lat = np.radians(observer_lat)
        self.observer_lon = np.radians(observer_lon)
        self.observer_alt = observer_alt
        
        logging.info(f"Parallax Corrector initialized")
        logging.info(f"  Observer: {np.degrees(self.observer_lat):.2f}°, "
                    f"{np.degrees(self.observer_lon):.2f}°, {observer_alt:.1f} km")
    
    def get_earth_position(self, jd):
        """
        Get Earth's position at Julian Date.
        
        Uses JPL Horizons for precision.
        
        Args:
            jd: Julian Date
        
        Returns:
            tuple: (x, y, z) in AU (heliocentric)
        """
        try:
            from astroquery.jplhorizons import Horizons
            
            # Query Earth position
            obj = Horizons(id='399',  # Earth
                          location='@sun',  # Heliocentric
                          epochs=jd)
            
            vec = obj.vectors()
            
            x = float(vec['x'][0])
            y = float(vec['y'][0])
            z = float(vec['z'][0])
            
            return (x, y, z)
            
        except Exception as e:
            logging.error(f"Failed to query Earth position: {e}")
            # Fallback: circular orbit approximation
            t_year = (jd - 2451545.0) / 365.25  # Years since J2000
            angle = 2 * np.pi * t_year
            
            x = 1.0 * np.cos(angle)
            y = 1.0 * np.sin(angle)
            z = 0.0
            
            return (x, y, z)
    
    def barycentric_to_topocentric(self, x_bary, y_bary, z_bary, jd):
        """
        Convert barycentric to topocentric (telescope) coordinates.
        
        Args:
            x_bary, y_bary, z_bary: Barycentric position (AU)
            jd: Julian Date of observation
        
        Returns:
            dict: {
                'ra': Right Ascension (degrees),
                'dec': Declination (degrees),
                'distance': Distance from Earth (AU),
                'parallax': Parallax shift (arcseconds)
            }
        """
        # Step 1: Get Earth position (heliocentric)
        x_earth, y_earth, z_earth = self.get_earth_position(jd)
        
        # Step 2: Convert to geocentric (from Earth)
        x_geo = x_bary - x_earth
        y_geo = y_bary - y_earth
        z_geo = z_bary - z_earth
        
        # Step 3: Convert to spherical (RA/Dec)
        distance = np.sqrt(x_geo**2 + y_geo**2 + z_geo**2)
        
        # RA (0-360°)
        ra = np.degrees(np.arctan2(y_geo, x_geo))
        if ra < 0:
            ra += 360
        
        # Dec (-90 to +90°)
        dec = np.degrees(np.arcsin(z_geo / distance))
        
        # Step 4: Calculate parallax shift
        # Annual parallax in arcseconds
        parallax_arcsec = (1.0 / distance) * 206265  # 1 AU at 1 AU = 1" parallax
        
        # Diurnal parallax (observer on Earth's surface)
        # This is small for distant objects but included for completeness
        earth_radius_au = 6371 / 149597870.7  # Earth radius in AU
        diurnal_parallax = earth_radius_au / distance * 206265
        
        logging.info(f"Parallax calculation:")
        logging.info(f"  Barycentric: ({x_bary:.1f}, {y_bary:.1f}, {z_bary:.1f}) AU")
        logging.info(f"  Earth position: ({x_earth:.3f}, {y_earth:.3f}, {z_earth:.3f}) AU")
        logging.info(f"  Geocentric distance: {distance:.1f} AU")
        logging.info(f"  RA: {ra:.4f}°, Dec: {dec:.4f}°")
        logging.info(f"  Annual parallax: {parallax_arcsec:.4f}\"")
        
        return {
            'ra': ra,
            'dec': dec,
            'distance': distance,
            'parallax_annual': parallax_arcsec,
            'parallax_diurnal': diurnal_parallax
        }
    
    def format_coordinates(self, ra, dec):
        """
        Format RA/Dec for telescope input.
        
        Args:
            ra: Right Ascension (degrees)
            dec: Declination (degrees)
        
        Returns:
            str: Formatted coordinates
        """
        # RA to hours:minutes:seconds
        ra_hours = ra / 15.0
        ra_h = int(ra_hours)
        ra_m = int((ra_hours - ra_h) * 60)
        ra_s = ((ra_hours - ra_h) * 60 - ra_m) * 60
        
        # Dec to degrees:arcminutes:arcseconds
        dec_sign = '+' if dec >= 0 else '-'
        dec_abs = abs(dec)
        dec_d = int(dec_abs)
        dec_m = int((dec_abs - dec_d) * 60)
        dec_s = ((dec_abs - dec_d) * 60 - dec_m) * 60
        
        return f"RA: {ra_h:02d}h {ra_m:02d}m {ra_s:05.2f}s, Dec: {dec_sign}{dec_d:02d}° {dec_m:02d}' {dec_s:05.2f}\""


if __name__ == "__main__":
    # Test module
    print("=== Testing Parallax Corrector ===\n")
    
    # Mauna Kea Observatory
    corrector = ParallaxCorrector(
        observer_lat=19.8207,
        observer_lon=-155.4681,
        observer_alt=4.2
    )
    
    # Test Planet 9 at 500 AU
    x_bary = 500.0
    y_bary = 100.0
    z_bary = 50.0
    
    # Current Julian Date
    jd = 2451545.0  # J2000
    
    result = corrector.barycentric_to_topocentric(x_bary, y_bary, z_bary, jd)
    
    print(f"\nTelescope Coordinates:")
    formatted = corrector.format_coordinates(result['ra'], result['dec'])
    print(f"  {formatted}")
    print(f"  Distance: {result['distance']:.1f} AU")
    print(f"  Parallax: {result['parallax_annual']:.4f} arcsec/year")
