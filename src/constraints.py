import numpy as np
import healpy as hp
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CONSTRAINTS - %(message)s')

class Constraints:
    """
    The Constraints Manager.
    Handles 'Veto Power' from Optical, Infrared, and Gravity surveys.
    """
    def __init__(self):
        # Load REAL Maps (NSIDE=128, based on published data)
        try:
            logging.info("Loading REAL WISE Exclusion Map (Meisner et al. 2020)...")
            self.wise_exclusion_map = hp.read_map('data/real/maps/wise_exclusion_real.fits', verbose=False)
            logging.info(f"  NSIDE = {hp.get_nside(self.wise_exclusion_map)}")
            
            logging.info("Loading REAL Gaia DR3 Density Map...")
            self.gaia_density_map = hp.read_map('data/real/maps/gaia_density_real.fits', verbose=False)
            logging.info(f"  NSIDE = {hp.get_nside(self.gaia_density_map)}")
            logging.info(f"  Density range: {self.gaia_density_map.min():.0f}-{self.gaia_density_map.max():.0f} stars/sq-deg")
        except FileNotFoundError:
            logging.error("REAL HEALPix maps not found. Run download_real_data.py first.")
            self.wise_exclusion_map = None
            self.gaia_density_map = None
        
        # Cassini Limit: Max acceleration on Saturn (m/s^2)
        self.cassini_limit = 1e-9
        
        # Tier 5: Satellite Telemetry
        self.cassini_range_limit = 100  # meters (Saturn position error)
        self.mars_bary_shift_limit = 10  # meters over 10 years
        
        # Tier 6: NANOGrav Pulsar Timing
        self.nanograv_accel_limit = 1e-9  # m/s² (SSB acceleration)
        
        # Tier 7: High-inclination centaurs (for dynamical validation)
        # Not a constraint, but targets for sim validation

    def check_cassini_range(self, p9_params):
        """
        Tier 5A: Cassini Range Residuals
        Check if P9 disturbs Saturn's orbit by >100 meters
        """
        # Calculate gravitational force on Saturn from Planet 9
        # F = G * M_p9 * M_saturn / r²
        # Position change over 13 years (Cassini mission duration)
        
        G = 6.67430e-11  # m³/(kg·s²)
        M_p9_kg = p9_params['m'] * 1.989e30  # Solar masses to kg
        M_saturn = 5.683e26  # kg
        
        # Distance Saturn-P9 (worst case: closest approach)
        a_saturn = 9.58  # AU
        a_p9 = p9_params['a']
        r_min_au = abs(a_p9 - a_saturn)
        r_min_m = r_min_au * 1.496e11
        
        # Acceleration
        acc = G * M_p9_kg / (r_min_m ** 2)
        
        # Position change over 13 years (Cassini: 2004-2017)
        t_years = 13
        t_sec = t_years * 365.25 * 24 * 3600
        delta_pos = 0.5 * acc * (t_sec ** 2)
        
        if delta_pos > self.cassini_range_limit:
            logging.warning(f"Cassini Veto: Saturn shift {delta_pos:.1f}m > {self.cassini_range_limit}m")
            return False
        
        return True

    def check_nanograv(self, p9_params):
        """
        Tier 6: NANOGrav Pulsar Timing Array
        Check if P9 acceleration on Sun exceeds 10^-9 m/s²
        Reference: Vallisneri et al. (2020), NANOGrav 12.5yr
        """
        G = 6.67430e-11
        M_p9_kg = p9_params['m'] * 1.989e30
        M_sun = 1.989e30  # kg
        
        # Distance Sun-P9
        a_p9_m = p9_params['a'] * 1.496e11
        
        # Gravitational acceleration on Sun due to P9
        # a = G * M_p9 / r²
        acc_ssb = G * M_p9_kg / (a_p9_m ** 2)
        
        if acc_ssb > self.nanograv_accel_limit:
            logging.warning(f"NANOGrav Veto: SSB accel {acc_ssb:.2e} > {self.nanograv_accel_limit:.2e} m/s²")
            return False
        
        return True
    
    def check_mars_barycenter(self, p9_params):
        """
        Tier 5B: Mars Reconnaissance Orbiter
        Check if P9 shifts solar system barycenter by >10m over 10 years
        """
        # Barycenter shift = M_p9 * r_p9 / (M_sun + M_p9)
        # For M_p9 << M_sun: shift ≈ M_p9 * r_p9 / M_sun
        
        M_p9_solar = p9_params['m']
        r_p9_au = p9_params['a']
        
        # Barycenter shift in AU
        bary_shift_au = M_p9_solar * r_p9_au
        bary_shift_m = bary_shift_au * 1.496e11
        
        if bary_shift_m > self.mars_bary_shift_limit:
            logging.warning(f"Mars MRO Veto: Barycenter shift {bary_shift_m:.1f}m > {self.mars_bary_shift_limit}m")
            return False
        
        return True 

    def check_cassini(self, p9_params):
        """
        Tier 1: Cassini Ranging Residuals.
        If P9 acceleration on Saturn > Limit, REJECT.
        """
        # Calculate distance P9-Saturn (Approximate, assuming worst case alignment)
        # a_p9 = p9_params['a']
        # a_saturn = 9.58 AU
        # min_dist = a_p9 - a_saturn
        
        # Acceleration = G * M_p9 / r^2
        # G in SI units: 6.674e-11
        # M_p9 in kg (Mass=10 Earths ~ 6e25 kg)
        # r in meters
        
        G = 6.67430e-11
        M_p9 = p9_params['m'] * 5.972e24 # Convert Earth masses (if input is M_earth) or M_sun?
        # Input 'm' is usually M_sun in REBOUND.
        # Let's assume input is M_sun.
        M_p9_kg = p9_params['m'] * 1.989e30
        
        r_au = p9_params['a'] - 9.58 # Closest approach
        r_m = r_au * 1.496e11
        
        acc = G * M_p9_kg / (r_m**2)
        
        if acc > self.cassini_limit:
            logging.warning(f"Cassini Veto: Acc {acc:.2e} > Limit {self.cassini_limit:.2e}")
            return False # REJECT
            
        return True # PASS

    def check_optical_infrared(self, p9_params):
        """
        Tier 2 & 3: Optical (ZTF/DES) and Infrared (WISE).
        Calculates predicted RA/Dec/Mag and checks maps.
        """
        # 1. Calculate Position (RA/Dec) from Orbital Elements
        # This requires solving Kepler's equation for Mean Anomaly -> True Anomaly -> Cartesian -> Spherical.
        # For optimization loop, we might check the *entire orbit path*?
        # Or just the current position?
        # "Where is it NOW?" is the question for surveys.
        # But we are optimizing for "Where is it?" parameters.
        # The parameters include Mean Anomaly (M) or Time of Perihelion (T).
        # If M is not optimized, we check the whole orbit track.
        # If the whole track is in a "Clear Zone", it's risky.
        # But usually P9 is far (faint).
        
        # For V1, let's implement a placeholder "Galactic Plane" preference.
        # If P9 is in Galactic Plane, it's safer (Camouflage).
        # Galactic Latitude (b).
        
        # Calculate Galactic Latitude 'b' from Inclination/Omega/omega?
        # Complex coordinate transform.
        
        return True # Placeholder

    def get_penalty(self, p9_params):
        """
        Returns a cost penalty if constraints are violated.
        Tiers 1, 5, 6 implemented.
        """
        penalty = 0.0
        
        # Tier 1: Basic Cassini (acceleration)
        if not self.check_cassini(p9_params):
            penalty += 1e6
            
        # Tier 5A: Cassini Range Residuals
        if not self.check_cassini_range(p9_params):
            penalty += 1e6
            
        # Tier 5B: Mars Barycenter
        if not self.check_mars_barycenter(p9_params):
            penalty += 1e6
            
        # Tier 6: NANOGrav Pulsar Timing
        if not self.check_nanograv(p9_params):
            penalty += 1e6
        
        return penalty
