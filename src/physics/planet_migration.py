"""
Giant Planet Migration Module
Category B1: Giant Planet Evolution [CRITICAL]

Implements the "Nice Model" - Jupiter and Saturn migrated dramatically
4 billion years ago due to planetesimal scattering.

Reference: Tsiganis et al. (2005) "Origin of the orbital architecture of the giant planets"

Key events:
- Jupiter migrated inward ~0.2 AU
- Saturn migrated outward ~1.5 AU
- They crossed the 2:1 resonance → "jumping Jupiter"
- This triggered the Late Heavy Bombardment

Constraint: Must preserve Jupiter's Trojan asteroids (L4/L5 points)
"""
import numpy as np
import rebound
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MIGRATION - %(message)s')

class GiantPlanetMigration:
    """
    Implements smooth or impulsive migration of Jupiter and Saturn.
    
    Two models supported:
    1. "Nice Model" (Tsiganis 2005) - Smooth then jump
    2. "Grand Tack" (Walsh 2011) - Jupiter goes in then out
    """
    
    def __init__(self, model='nice', enabled=True):
        """
        Args:
            model: 'nice' or 'grand_tack'
            enabled: Enable migration
        """
        self.model = model
        self.enabled = enabled
        
        # Nice Model parameters
        if model == 'nice':
            self.t_start = 500e6 * 2 * np.pi  # Start at 500 Myr
            self.t_duration = 100e6 * 2 * np.pi  # Duration 100 Myr
            self.jupiter_da = -0.2  # AU (inward)
            self.saturn_da = +1.5   # AU (outward)
        elif model == 'grand_tack':
            self.t_start = 10e6 * 2 * np.pi  # Early (10 Myr)
            self.t_duration = 500e3 * 2 * np.pi  # Fast (0.5 Myr)
            self.jupiter_da = -1.5  # Goes to ~3.5 AU
            self.saturn_da = -0.5
        
        logging.info(f"Giant Planet Migration: {model.upper()}")
        logging.info(f"  Enabled: {enabled}")
        if enabled:
            logging.info(f"  Start: {self.t_start/(2*np.pi*1e6):.1f} Myr")
            logging.info(f"  Duration: {self.t_duration/(2*np.pi*1e6):.1f} Myr")
            logging.info(f"  Jupiter Δa: {self.jupiter_da:.2f} AU")
            logging.info(f"  Saturn Δa: {self.saturn_da:.2f} AU")
    
    def migration_timescale(self, t):
        """
        Calculate migration rate at time t (smooth damping).
        
        Uses exponential damping: da/dt ∝ (a - a_final)/τ
        
        Args:
            t: Current time (REBOUND units)
        
        Returns:
            float: Migration strength (0 to 1)
        """
        if not self.enabled:
            return 0.0
        
        if t < self.t_start:
            return 0.0  # Not started
        elif t > self.t_start + self.t_duration:
            return 0.0  # Finished
        else:
            # Smooth ramp-up and ramp-down
            phase = (t - self.t_start) / self.t_duration
            strength = np.sin(np.pi * phase)  # Smooth curve
            return strength
    
    def apply_migration_force(self, sim, t, jupiter_index=1, saturn_index=2):
        """
        Apply migration damping force to giants.
        
        This modifies velocities to slowly change semi-major axis.
        
        Args:
            sim: REBOUND simulation
            t: Current time
            jupiter_index: Index of Jupiter particle
            saturn_index: Index of Saturn particle
        """
        if not self.enabled:
            return
        
        strength = self.migration_timescale(t)
        
        if strength == 0.0:
            return
        
        # Jupiter migration
        try:
            jupiter = sim.particles[jupiter_index]
            orbit_j = jupiter.calculate_orbit(primary=sim.particles[0])
            
            # Target semi-major axis
            a_current = orbit_j.a
            a_target = orbit_j.a + self.jupiter_da * strength
            
            # Damping force (velocity modification)
            # da/dt = 2a v/r (tangential)
            damping_factor = (a_target - a_current) / a_current
            
            jupiter.vx *= (1 + damping_factor * 0.01)
            jupiter.vy *= (1 + damping_factor * 0.01)
            
        except Exception as e:
            logging.warning(f"Jupiter migration failed: {e}")
        
        # Saturn migration
        try:
            saturn = sim.particles[saturn_index]
            orbit_s = saturn.calculate_orbit(primary=sim.particles[0])
            
            a_current = orbit_s.a
            a_target = orbit_s.a + self.saturn_da * strength
            
            damping_factor = (a_target - a_current) / a_current
            
            saturn.vx *= (1 + damping_factor * 0.01)
            saturn.vy *= (1 + damping_factor * 0.01)
            
        except Exception as e:
            logging.warning(f"Saturn migration failed: {e}")
    
    def check_trojan_stability(self, sim, jupiter_index=1, trojan_indices=None):
        """
        Check if Jupiter's Trojans survived migration.
        
        Trojans live at L4 (60° ahead) and L5 (60° behind) Jupiter.
        Migration must preserve them.
        
        Args:
            sim: Simulation
            jupiter_index: Jupiter particle index
            trojan_indices: List of Trojan particle indices
        
        Returns:
            float: Survival rate (0 to 1)
        """
        if trojan_indices is None or len(trojan_indices) == 0:
            return 1.0  # No Trojans to check
        
        survived = 0
        total = len(trojan_indices)
        
        jupiter_orbit = sim.particles[jupiter_index].calculate_orbit(primary=sim.particles[0])
        
        for idx in trojan_indices:
            try:
                trojan = sim.particles[idx]
                orbit = trojan.calculate_orbit(primary=sim.particles[0])
                
                # Check if still near Jupiter's orbit
                a_diff = abs(orbit.a - jupiter_orbit.a) / jupiter_orbit.a
                
                # Check libration angle (Δλ should be ~60° or ~300°)
                # This is a simplified check
                
                if a_diff < 0.1:  # Within 10% of Jupiter's a
                    survived += 1
                    
            except:
                pass  # Ejected
        
        survival_rate = survived / total if total > 0 else 1.0
        
        logging.info(f"Trojan stability: {survived}/{total} survived ({survival_rate*100:.1f}%)")
        
        return survival_rate


if __name__ == "__main__":
    # Test module
    print("=== Testing Giant Planet Migration ===\n")
    
    migration = GiantPlanetMigration(model='nice', enabled=True)
    
    # Test migration timescale
    print("\nMigration strength over time:")
    times_myr = [0, 400, 500, 550, 600, 700]
    for t_myr in times_myr:
        t = t_myr * 1e6 * 2 * np.pi
        strength = migration.migration_timescale(t)
        print(f"  T = {t_myr} Myr: strength = {strength:.3f}")
    
    # Test with REBOUND
    print("\nApplying to simulation:")
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    sim.add(m=1.0)  # Sun
    sim.add(m=9.5458e-4, a=5.4, e=0.048)  # Jupiter (slightly farther)
    sim.add(m=2.8588e-4, a=8.5, e=0.056)  # Saturn (slightly closer)
    
    
    initial_a_j = sim.particles[1].calculate_orbit(primary=sim.particles[0]).a
    initial_a_s = sim.particles[2].calculate_orbit(primary=sim.particles[0]).a
    
    print(f"  Initial: Jupiter a={initial_a_j:.2f} AU, Saturn a={initial_a_s:.2f} AU")
    
    # Simulate migration period
    t_mid = 550e6 * 2 * np.pi  # Middle of migration
    migration.apply_migration_force(sim, t_mid, jupiter_index=1, saturn_index=2)
    sim.integrate(t_mid + 1000 * 2 * np.pi)  # Short integration
    
    final_a_j = sim.particles[1].calculate_orbit(primary=sim.particles[0]).a
    final_a_s = sim.particles[2].calculate_orbit(primary=sim.particles[0]).a
    
    print(f"  After 1000yr: Jupiter a={final_a_j:.2f} AU, Saturn a={final_a_s:.2f} AU")
    print(f"  Changes: ΔJ={final_a_j-initial_a_j:.3f} AU, ΔS={final_a_s-initial_a_s:.3f} AU")
