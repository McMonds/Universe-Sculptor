"""
Solar Mass Loss Module
Category A1: Astrophysical Environment [CRITICAL]

The Sun loses ~0.05-0.1% of its mass over 4.5 Gyr due to:
- Nuclear fusion (burning hydrogen)
- Solar wind (charged particle ejection)

Effect: As M_sun decreases, all orbits expand (a ∝ 1/M)
Without modeling this, historical simulations place objects in orbits that are too tight.
"""
import rebound
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SOLAR_MASS - %(message)s')

class SolarMassLoss:
    """
    Implements adiabatic mass loss of the Sun.
    
    Uses reboundx tau_mass parameter for automatic handling.
    Formula: M(t) = M_now / (1 + t/tau_mass)
    """
    
    def __init__(self, enabled=True, total_loss_fraction=0.0007):
        """
        Args:
            enabled: Enable solar mass loss
            total_loss_fraction: Fraction of mass lost over 4.5 Gyr (default: 0.07%)
        """
        self.enabled = enabled
        self.total_loss_fraction = total_loss_fraction
        
        # Calculate tau_mass for reboundx
        # Over 4.5 Gyr, lose 0.07% mass
        # tau_mass = integration_time / ln(1 + fraction)
        self.tau_mass = (4.5e9 * 2 * np.pi) / np.log(1 + total_loss_fraction)
        
        logging.info(f"Solar Mass Loss Module: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Total loss: {total_loss_fraction*100:.3f}% over 4.5 Gyr")
            logging.info(f"  tau_mass: {self.tau_mass/(2*np.pi*1e9):.2f} Gyr")
    
    def apply_to_simulation(self, sim):
        """
        Apply mass loss to the simulation.
        
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
            
            # Apply mass loss to the Sun (particle 0)
            sun = sim.particles[0]
            sun.params['tau_mass'] = -self.tau_mass  # Negative for mass loss
            
            # Add modify_mass force
            mof = rebx.load_force("modify_mass")
            rebx.add_force(mof)
            
            logging.info("✓ Solar mass loss applied to Sun")
            
            return rebx
            
        except ImportError:
            logging.error("reboundx not installed. Install: pip install reboundx")
            return None
        except Exception as e:
            logging.error(f"Failed to apply solar mass loss: {e}")
            return None
    
    def get_mass_at_time(self, t_years):
        """
        Calculate Sun's mass at a given time in the past.
        
        Args:
            t_years: Time in years (negative = past)
        
        Returns:
            float: Mass relative to today (M_now = 1.0)
        """
        if not self.enabled:
            return 1.0
        
        t_rebound = t_years * 2 * np.pi
        M_ratio = 1.0 / (1 + t_rebound / self.tau_mass)
        
        return M_ratio
    
    def validate_orbit_expansion(self, a_initial, t_years):
        """
        Calculate expected orbital expansion due to mass loss.
        
        Args:
            a_initial: Initial semi-major axis (AU)
            t_years: Time elapsed (years)
        
        Returns:
            float: New semi-major axis (AU)
        """
        M_ratio = self.get_mass_at_time(-t_years)
        a_final = a_initial / M_ratio
        
        expansion = a_final - a_initial
        logging.info(f"Orbit expansion over {t_years/1e6:.1f} Myr: {expansion:.3f} AU")
        
        return a_final


if __name__ == "__main__":
    # Test module
    print("=== Testing Solar Mass Loss Module ===\n")
    
    module = SolarMassLoss(enabled=True, total_loss_fraction=0.0007)
    
    # Test mass at different times
    times = [-4.5e9, -3e9, -1e9, 0]
    print("\nMass History:")
    for t in times:
        M = module.get_mass_at_time(t)
        print(f"  T = {t/1e9:+.1f} Gyr: M_sun = {M:.6f} M_now ({(1-M)*100:.4f}% less)")
    
    # Test orbit expansion
    print("\nJupiter Orbit Expansion:")
    a_jupiter_initial = 5.2  # AU
    module.validate_orbit_expansion(a_jupiter_initial, 4.5e9)
    
    # Apply to simulation
    print("\nApplying to REBOUND:")
    sim = rebound.Simulation()
    sim.add(m=1.0)  # Sun
    sim.add(m=9.5e-4, a=5.2, e=0.048)  # Jupiter
    
    rebx = module.apply_to_simulation(sim)
    if rebx:
        print("✓ Successfully applied to simulation")
