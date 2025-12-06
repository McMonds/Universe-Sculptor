"""
General Relativity Precession Module
Category D1: Relativistic Effects [HIGH]

Implements Schwarzschild metric corrections for perihelion precession.
Effect: Tiny but measurable precession accumulates over 4.5 Gyr.

For Planet 9 at 500 AU with high eccentricity, GR precession is small
but non-negligible for "NASA-grade" precision.
"""
import rebound
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - GR - %(message)s')

class GeneralRelativityPrecession:
    """
    Applies post-Newtonian corrections to orbital dynamics.
    
    Uses reboundx gr module for automatic GR force calculation.
    """
    
    def __init__(self, enabled=True, c_light=10065.32):
        """
        Args:
            enabled: Enable GR precession
            c_light: Speed of light in REBOUND units (AU/yr)
                    Default: 63,241 AU/yr ≈ 10065.32 (2π × speed of light)
        """
        self.enabled = enabled
        self.c_light = c_light
        
        logging.info(f"GR Precession Module: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Speed of light: {c_light/(2*np.pi):.1f} AU/yr")
    
    def apply_to_simulation(self, sim):
        """
        Apply GR corrections to simulation.
        
        Args:
            sim: rebound.Simulation object
        
        Returns:
            reboundx instance
        """
        if not self.enabled:
            return None
        
        try:
            import reboundx
            
            # Initialize reboundx
            rebx = reboundx.Extras(sim)
            
            # Set speed of light
            rebx.c = self.c_light
            
            # Add GR force
            gr = rebx.load_force("gr")
            rebx.add_force(gr)
            
            # Optionally set which particles to apply GR to
            # (Apply to all massive bodies by default)
            for p in sim.particles:
                if p.m > 1e-10:  # Massive particles
                    p.params["gr_source"] = 1
            
            logging.info("✓ GR precession applied to simulation")
            logging.info(f"  Applied to {sum(1 for p in sim.particles if p.m > 1e-10)} massive bodies")
            
            return rebx
            
        except ImportError:
            logging.error("reboundx not installed. Install: pip install reboundx")
            return None
        except Exception as e:
            logging.error(f"Failed to apply GR: {e}")
            return None
    
    def calculate_perihelion_precession(self, a, e, M_central=1.0):
        """
        Calculate GR perihelion precession rate (rad/orbit).
        
        Classical formula: dω/orbit = 6πGM / (ac²(1-e²))
        
        Args:
            a: Semi-major axis (AU)
            e: Eccentricity
            M_central: Central mass (solar masses)
        
        Returns:
            float: Precession per orbit (radians)
        """
        if not self.enabled:
            return 0.0
        
        G = 1.0  # In REBOUND units with solar mass
        c = self.c_light / (2 * np.pi)  # Convert to AU/yr
        
        # GR precession formula
        precession_per_orbit = (6 * np.pi * G * M_central) / (a * c**2 * (1 - e**2))
        
        return precession_per_orbit
    
    def estimate_total_precession(self, a, e, t_years, M_central=1.0):
        """
        Estimate total precession over a time period.
        
        Args:
            a: Semi-major axis (AU)
            e: Eccentricity
            t_years: Time period (years)
            M_central: Central mass (solar masses)
        
        Returns:
            float: Total precession (degrees)
        """
        # Orbital period (Kepler's 3rd law)
        T_years = 2 * np.pi * np.sqrt(a**3 / M_central)
        
        # Number of orbits
        n_orbits = t_years / T_years
        
        # Precession per orbit
        precession_per_orbit = self.calculate_perihelion_precession(a, e, M_central)
        
        # Total precession
        total_precession_rad = precession_per_orbit * n_orbits
        total_precession_deg = np.degrees(total_precession_rad)
        
        logging.info(f"GR Precession Estimate:")
        logging.info(f"  Orbit: a={a:.1f} AU, e={e:.3f}")
        logging.info(f"  Time: {t_years/1e9:.2f} Gyr ({n_orbits:.0f} orbits)")
        logging.info(f"  Precession: {total_precession_deg:.4f}° total")
        logging.info(f"  Rate: {precession_per_orbit*206265:.2e} arcsec/orbit")
        
        return total_precession_deg


if __name__ == "__main__":
    # Test module
    print("=== Testing GR Precession Module ===\n")
    
    module = GeneralRelativityPrecession(enabled=True)
    
    # Test Mercury (famous precession)
    print("Mercury Test (validation):")
    mercury_precession = module.estimate_total_precession(
        a=0.387,  # AU
        e=0.206,
        t_years=100 * 365.25,  # 100 Earth years
        M_central=1.0
    )
    print(f"  Observed: ~43 arcsec/century")
    print(f"  Calculated: {mercury_precession * 3600:.2f} arcsec/century\n")
    
    # Test Planet 9
    print("Planet 9 Estimate:")
    p9_precession = module.estimate_total_precession(
        a=500,  # AU
        e=0.6,
        t_years=4.5e9,  # 4.5 Gyr
        M_central=1.0
    )
    
    # Apply to simulation
    print("\nApplying to REBOUND:")
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    sim.add(m=1.0)  # Sun
    sim.add(m=5e-5, a=500, e=0.6, inc=0.3)  # Planet 9
    
    rebx = module.apply_to_simulation(sim)
    if rebx:
        print("✓ Successfully applied GR to simulation")
