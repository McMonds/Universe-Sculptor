"""
Trojan Stability Constraint
Category B3: Giant Planet Evolution [MEDIUM]

Jupiter's Trojan asteroids live at L4 (60° ahead) and L5 (60° behind).
They are incredibly sensitive to gravitational perturbations.

If Planet 9 destabilizes them during migration, we'd see evidence today.
Since ~9000 Trojans still exist → constraint on Planet 9's history.

Reference: Morbidelli et al. (2005) "Chaotic capture of Jupiter's Trojans"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - TROJANS - %(message)s')

class TrojanStabilityConstraint:
    """
    Ensures Jupiter's Trojans survive Planet 9 interactions.
    
    Places test particles at L4/L5, checks survival rate.
    """
    
    def __init__(self, enabled=True, min_survival_rate=0.5):
        """
        Args:
            enabled: Enable Trojan stability check
            min_survival_rate: Minimum fraction that must survive (default 50%)
        """
        self.enabled = enabled
        self.min_survival_rate = min_survival_rate
        
        logging.info(f"Trojan Stability Constraint: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Minimum survival rate: {min_survival_rate*100:.0f}%")
    
    def place_test_trojans(self, sim, jupiter_index=1, n_trojans=20):
        """
        Place test particles at Jupiter's L4 and L5 Lagrange points.
        
        Args:
            sim: REBOUND simulation
            jupiter_index: Index of Jupiter
            n_trojans: Number of test Trojans (half at L4, half at L5)
        
        Returns:
            list: Indices of Trojan particles
        """
        if not self.enabled:
            return []
        
        jupiter = sim.particles[jupiter_index]
        orbit_j = jupiter.calculate_orbit(primary=sim.particles[0])
        
        a_j = orbit_j.a
        e_j = orbit_j.e
        
        trojan_indices = []
        
        # L4 Trojans (60° ahead)
        for i in range(n_trojans // 2):
            # Small random perturbations around L4
            delta_lambda = np.radians(60) + np.random.uniform(-0.1, 0.1)
            delta_a = np.random.uniform(-0.05, 0.05)
            delta_e = np.random.uniform(-0.01, 0.01)
            
            sim.add(
                m=0,
                a=a_j + delta_a,
                e=e_j + delta_e,
                inc=orbit_j.inc,
                Omega=orbit_j.Omega,
                omega=orbit_j.omega,
                M=orbit_j.M + delta_lambda,
                hash=10000 + i  # Unique identifier for Trojans
            )
            trojan_indices.append(len(sim.particles) - 1)
        
        # L5 Trojans (60° behind)
        for i in range(n_trojans // 2):
            delta_lambda = np.radians(-60) + np.random.uniform(-0.1, 0.1)
            delta_a = np.random.uniform(-0.05, 0.05)
            delta_e = np.random.uniform(-0.01, 0.01)
            
            sim.add(
                m=0,
                a=a_j + delta_a,
                e=e_j + delta_e,
                inc=orbit_j.inc,
                Omega=orbit_j.Omega,
                omega=orbit_j.omega,
                M=orbit_j.M + delta_lambda,
                hash=10000 + n_trojans//2 + i
            )
            trojan_indices.append(len(sim.particles) - 1)
        
        logging.info(f"Placed {n_trojans} test Trojans at L4/L5")
        
        return trojan_indices
    
    def check_survival(self, sim, trojan_indices, jupiter_index=1):
        """
        Check how many Trojans survived.
        
        Criteria: Still near Jupiter's orbit, low eccentricity
        
        Args:
            sim: Final simulation state
            trojan_indices: List of Trojan particle indices
            jupiter_index: Jupiter index
        
        Returns:
            dict: Survival statistics
        """
        if not self.enabled or len(trojan_indices) == 0:
            return {'survival_rate': 1.0, 'passes': True}
        
        jupiter = sim.particles[jupiter_index]
        orbit_j = jupiter.calculate_orbit(primary=sim.particles[0])
        a_j = orbit_j.a
        
        survived = 0
        ejected = 0
        
        for idx in trojan_indices:
            try:
                trojan = sim.particles[idx]
                orbit_t = trojan.calculate_orbit(primary=sim.particles[0])
                
                # Survival criteria:
                # 1. Still near Jupiter's semi-major axis (±20%)
                # 2. Eccentricity not too high (< 0.3)
                
                a_diff = abs(orbit_t.a - a_j) / a_j
                
                if a_diff < 0.2 and orbit_t.e < 0.3:
                    survived += 1
                else:
                    ejected += 1
                    
            except:
                ejected += 1  # Particle removed/ejected
        
        total = len(trojan_indices)
        survival_rate = survived / total if total > 0 else 1.0
        passes = survival_rate >= self.min_survival_rate
        
        result = {
            'survived': survived,
            'ejected': ejected,
            'total': total,
            'survival_rate': survival_rate,
            'passes': passes
        }
        
        logging.info(f"Trojan Survival Check:")
        logging.info(f"  Survived: {survived}/{total} ({survival_rate*100:.1f}%)")
        logging.info(f"  Status: {'PASS ✓' if passes else 'FAIL ✗'}")
        
        return result
    
    def get_penalty(self, survival_rate):
        """
        Calculate penalty for Trojan loss.
        
        Args:
            survival_rate: Fraction that survived
        
        Returns:
            float: Penalty score
        """
        if survival_rate >= self.min_survival_rate:
            return 0.0
        else:
            # Heavy penalty for destroying Trojans
            deficit = self.min_survival_rate - survival_rate
            return deficit * 5000


if __name__ == "__main__":
    # Test module
    print("=== Testing Trojan Stability Constraint ===\n")
    
    constraint = TrojanStabilityConstraint(enabled=True, min_survival_rate=0.5)
    
    # Create simulation
    import rebound
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    sim.add(m=1.0)  # Sun
    sim.add(m=9.5458e-4, a=5.2, e=0.048)  # Jupiter
    
    # Place Trojans
    trojan_indices = constraint.place_test_trojans(sim, jupiter_index=1, n_trojans=20)
    
    # Integrate for 1000 years (short test)
    print("\nIntegrating for 1000 years...")
    sim.integrate(1000 * 2 * np.pi)
    
    # Check survival
    result = constraint.check_survival(sim, trojan_indices)
    
    print(f"\nPenalty: {constraint.get_penalty(result['survival_rate']):.0f}")
