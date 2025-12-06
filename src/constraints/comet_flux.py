"""
Comet Flux Constraint
Category H1: Dynamical Constraints [HIGH]

Planet 9 acts as a "comet machine gun" - it scatters Oort Cloud objects inward.
Constraint: The simulated comet flux must not exceed 2x the observed rate.

Data sources:
- Crater record on Earth/Moon
- Current long-period comet observations (JPL Small-Body Database)
- Observed rate: ~1-2 comets per year with q < 5 AU
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - COMET_FLUX - %(message)s')

class CometFluxConstraint:
    """
    Tracks how many comets Planet 9 sends toward Earth.
    
    Compares simulated flux to observed historical rate.
    """
    
    def __init__(self, observed_flux_per_year=1.5, max_multiplier=2.0):
        """
        Args:
            observed_flux_per_year: Observed comet rate (q < 5 AU)
            max_multiplier: Maximum allowed excess (2x = factor of 2)
        """
        self.observed_flux = observed_flux_per_year
        self.max_multiplier = max_multiplier
        self.max_allowed = observed_flux_per_year * max_multiplier
        
        logging.info(f"Comet Flux Constraint initialized")
        logging.info(f"  Observed flux: {observed_flux_per_year:.2f} comets/year")
        logging.info(f"  Max allowed: {self.max_allowed:.2f} comets/year ({max_multiplier}x)")
    
    def count_inner_penetrations(self, sim, q_threshold=5.0):
        """
        Count particles (test comets) that penetrate inner solar system.
        
        Args:
            sim: REBOUND simulation
            q_threshold: Perihelion threshold (AU) - inner system boundary
        
        Returns:
            int: Number of comets with q < threshold
        """
        count = 0
        
        for p in sim.particles[6:]:  # Skip Sun, Giants, P9
            try:
                orbit = p.calculate_orbit(primary=sim.particles[0])
                q = orbit.a * (1 - orbit.e)  # Perihelion
                
                if q < q_threshold:
                    count += 1
            except:
                pass  # Particle removed or ejected
        
        return count
    
    def calculate_flux(self, sim, integration_time_years, n_test_particles):
        """
        Calculate average comet flux rate.
        
        Args:
            sim: Final simulation state
            integration_time_years: Duration of simulation (years)
            n_test_particles: Number of test particles initially placed
        
        Returns:
            dict: Flux statistics
        """
        penetrations = self.count_inner_penetrations(sim)
        
        # Convert to rate per year
        # (penetrations / integration_time) * (real_population / test_particles)
        
        # Assume Oort Cloud has ~10^11 objects
        real_oort_population = 1e11
        scaling_factor = real_oort_population / n_test_particles if n_test_particles > 0 else 1.0
        
        flux_per_year = (penetrations / integration_time_years) * scaling_factor
        
        # Penalty if too high
        violation = max(0, flux_per_year - self.max_allowed)
        penalty = violation * 1000  # Large penalty
        
        results = {
            'penetrations': penetrations,
            'flux_per_year': flux_per_year,
            'observed_flux': self.observed_flux,
            'max_allowed': self.max_allowed,
            'violation': violation,
            'penalty': penalty,
            'passes': flux_per_year <= self.max_allowed
        }
        
        logging.info("Comet Flux Analysis:")
        logging.info(f"  Penetrations: {penetrations} (q < 5 AU)")
        logging.info(f"  Simulated flux: {flux_per_year:.2e} comets/year")
        logging.info(f"  Observed flux: {self.observed_flux:.2f} comets/year")
        logging.info(f"  Status: {'PASS ✓' if results['passes'] else 'FAIL ✗'}")
        
        if not results['passes']:
            logging.warning(f"  Excess flux: {violation:.2e} comets/year")
            logging.warning(f"  Penalty: {penalty:.2f}")
        
        return results
    
    def get_earth_impact_probability(self, flux_per_year, earth_cross_section_au2=1e-8):
        """
        Estimate probability of comet impacting Earth.
        
        Args:
            flux_per_year: Comet flux (comets/year)
            earth_cross_section_au2: Effective cross-section (AU²)
        
        Returns:
            float: Impacts per million years
        """
        # This is highly simplified
        # Real calculation needs velocity distributions, gravitational focusing
        
        total_sky_area = 4 * np.pi * 5**2  # AU² at 5 AU sphere
        impact_probability_per_comet = earth_cross_section_au2 / total_sky_area
        
        impacts_per_year = flux_per_year * impact_probability_per_comet
        impacts_per_myr = impacts_per_year * 1e6
        
        logging.info(f"\nEarth Impact Estimate:")
        logging.info(f"  ~{impacts_per_myr:.2e} impacts per million years")
        
        return impacts_per_myr


if __name__ == "__main__":
    # Test module
    print("=== Testing Comet Flux Constraint ===\n")
    
    constraint = CometFluxConstraint(
        observed_flux_per_year=1.5,
        max_multiplier=2.0
    )
    
    # Mock simulation
    import rebound
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    sim.add(m=1.0)  # Sun
    
    # Add Giants
    sim.add(m=9.5e-4, a=5.2, e=0.048)
    sim.add(m=2.86e-4, a=9.58, e=0.056)
    sim.add(m=4.37e-5, a=19.22, e=0.046)
    sim.add(m=5.15e-5, a=30.11, e=0.009)
    
    # Add Planet 9
    sim.add(m=5e-5, a=500, e=0.6)
    
    # Add test "comets" (some with q < 5)
    for i in range(100):
        a = np.random.uniform(100, 1000)
        e = np.random.uniform(0.7, 0.99)
        sim.add(m=0, a=a, e=e, inc=np.random.uniform(0, 0.5))
    
    sim.move_to_com()
    
    # Test flux calculation
    results = constraint.calculate_flux(
        sim,
        integration_time_years=1e6,  # 1 Myr simulation
        n_test_particles=100
    )
    
    constraint.get_earth_impact_probability(results['flux_per_year'])
