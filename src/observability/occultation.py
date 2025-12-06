"""
TAOS-II Occultation Probability Module
Category G3: Advanced Observations [HIGH]

Planet 9 passing in front of a star = stellar occultation.
TAOS-II (Taiwan-American Occultation Survey) monitors thousands of stars.

Probability depends on: planet size, sky position, telescope FOV.

Reference: Lehner et al. (2016) "TAOS-II: A Robotic Survey for Occultations"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - OCCULTATION - %(message)s')

class OccultationProbability:
    """
    Calculates probability of detecting Planet 9 via stellar occultation.
    """
    
    def __init__(self, enabled=True):
        """
        Args:
            enabled: Enable occultation calculations
        """
        self.enabled = enabled
        
        # TAOS-II Survey parameters
        self.taos_fov_deg2 = 2.1  # Square degrees
        self.taos_n_telescopes = 3
        self.taos_cadence_hz = 20  # 20 Hz photometry
        
        logging.info(f"Occultation Probability: {'ENABLED' if enabled else 'DISABLED'}")
    
    def calculate_geometric_cross_section(self, radius_km, distance_au):
        """
        Calculate geometric cross-section for occultation.
        
        Args:
            radius_km: Planet radius (km)
            distance_au: Distance from Earth (AU)
        
        Returns:
            float: Cross-section (square arc-seconds)
        """
        # Convert radius to arcseconds at distance
        au_to_km = 149597870.7
        distance_km = distance_au * au_to_km
        
        # Angular radius (radians)
        angular_radius_rad = radius_km / distance_km
        
        #Convert to arcseconds
        angular_radius_arcsec = angular_radius_rad * 206265
        
        # Cross-section area
        cross_section = np.pi * angular_radius_arcsec**2
        
        return cross_section
    
    def calculate_stellar_density(self, galactic_lat_deg):
        """
        Estimate stellar density at galactic latitude.
        
        More stars near galactic plane (lat=0°)
        
        Args:
            galactic_lat_deg: Galactic latitude (degrees)
        
        Returns:
            float: Stars per square degree
        """
        # Simplified model
        # Plane: ~1000 stars/deg² (V < 20)
        # Pole: ~100 stars/deg²
        
        lat_rad = np.radians(abs(galactic_lat_deg))
        density = 100 + 900 * np.exp(-lat_rad / 0.5)
        
        return density
    
    def estimate_occultation_rate(self, radius_km, distance_au, 
                                  velocity_km_s, galactic_lat=30):
        """
        Estimate how often Planet 9 occults a star.
        
        Args:
            radius_km: Planet radius (km)
            distance_au: Distance (AU)
            velocity_km_s: Transverse velocity (km/s)
            galactic_lat: Galactic latitude (degrees)
        
        Returns:
            dict: Occultation statistics
        """
        # Geometric cross-section
        cross_section_arcsec2 = self.calculate_geometric_cross_section(
            radius_km, distance_au
        )
        
        # Stellar density
        star_density = self.calculate_stellar_density(galactic_lat)
        
        # Occultation rate = cross_section * star_density * velocity
        # Convert to events per year
        
        # Sky swept per year (arcsec²/year)
        arcsec_per_deg = 3600
        deg_per_rad = 180 / np.pi
        
        # Velocity in arcsec/year
        au_to_km = 149597870.7
        km_per_year = velocity_km_s * 86400 * 365.25
        angular_velocity = (km_per_year / (distance_au * au_to_km)) * deg_per_rad * arcsec_per_deg
        
        # Path swept = velocity * diameter
        diameter_arcsec = np.sqrt(cross_section_arcsec2 / np.pi) * 2
        path_width_arcsec2_per_year = diameter_arcsec * angular_velocity
        
        # Convert stellar density from /deg² to /arcsec²
        star_density_arcsec2 = star_density / (arcsec_per_deg**2)
        
        # Events per year
        events_per_year = path_width_arcsec2_per_year * star_density_arcsec2
        
        # Duration of occultation
        duration_sec = (2 * radius_km) / velocity_km_s
        
        result = {
            'cross_section_arcsec2': cross_section_arcsec2,
            'star_density_deg2': star_density,
            'angular_velocity_arcsec_yr': angular_velocity,
            'events_per_year': events_per_year,
            'duration_sec': duration_sec,
            'radius_km': radius_km,
            'distance_au': distance_au
        }
        
        logging.info(f"Occultation Analysis:")
        logging.info(f"  Radius: {radius_km:.0f} km")
        logging.info(f"  Distance: {distance_au:.0f} AU")
        logging.info(f"  Velocity: {velocity_km_s:.1f} km/s")
        logging.info(f"  Cross-section: {cross_section_arcsec2:.3e} arcsec²")
        logging.info(f"  Star density: {star_density:.0f} /deg²")
        logging.info(f"  Occultation rate: {events_per_year:.2e} /year")
        logging.info(f"  Event duration: {duration_sec:.1f} seconds")
        
        return result
    
    def taos_detection_probability(self, radius_km, distance_au, 
                                   velocity_km_s=3, survey_years=5):
        """
        TAOS-II specific detection probability.
        
        Args:
            radius_km: Planet radius (km)
            distance_au: Distance (AU)
            velocity_km_s: Velocity (km/s)
            survey_years: Survey duration (years)
        
        Returns:
            dict: Detection assessment
        """
        # Occultation rate
        occ = self.estimate_occultation_rate(
            radius_km, distance_au, velocity_km_s
        )
        
        # TAOS-II coverage
        # Total sky: 41,253 deg²
        # TAOS-II FOV: 2.1 deg² × 3 telescopes = 6.3 deg²
        coverage_fraction = (self.taos_fov_deg2 * self.taos_n_telescopes) / 41253
        
        # Detected events = rate × coverage × time
        detected_events = occ['events_per_year'] * coverage_fraction * survey_years
        
        # Probability of at least one detection
        prob_detection = 1 - np.exp(-detected_events)
        
        result = {
            **occ,
            'coverage_fraction': coverage_fraction,
            'expected_detections': detected_events,
            'detection_probability': prob_detection,
            'survey_years': survey_years
        }
        
        logging.info(f"\nTAOS-II Detection Probability:")
        logging.info(f"  Survey years: {survey_years}")
        logging.info(f"  Coverage: {coverage_fraction*100:.2f}% of sky")
        logging.info(f"  Expected detections: {detected_events:.3f}")
        logging.info(f"  Detection probability: {prob_detection*100:.1f}%")
        
        return result


if __name__ == "__main__":
    # Test module
    print("=== Testing TAOS-II Occultation Probability ===\n")
    
    occ = OccultationProbability(enabled=True)
    
    # Planet 9 parameters (5 M⊕, 2.5 R⊕ at 500 AU)
    R_earth_km = 6371
    radius_p9 = 2.5 * R_earth_km  # km
    
    # Test detection probability
    result = occ.taos_detection_probability(
        radius_km=radius_p9,
        distance_au=500,
        velocity_km_s=3.0,
        survey_years=5
    )
    
    print(f"\nConclusion:")
    if result['detection_probability'] > 0.5:
        print(f"  HIGH chance of detection ({result['detection_probability']*100:.0f}%)")
    elif result['detection_probability'] > 0.1:
        print(f"  MODERATE chance ({result['detection_probability']*100:.0f}%)")
    else:
        print(f"  LOW chance ({result['detection_probability']*100:.1f}%)")
