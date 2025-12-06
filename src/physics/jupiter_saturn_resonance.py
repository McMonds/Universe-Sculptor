"""
Jupiter-Saturn Great Inequality
Category B2: Giant Planet Evolution [HIGH]

Jupiter and Saturn are near a 5:2 mean motion resonance.
This delicate balance must be preserved - if Planet 9 disrupts it,
the inner solar system (including Earth) becomes unstable.

Constraint: Period ratio P_saturn/P_jupiter must stay within 1% of 2.5

Reference: Murray & Dermott (1999) "Solar System Dynamics"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - RESONANCE - %(message)s')

class JupiterSaturnInequality:
    """
    Monitors the Jupiter-Saturn 5:2 resonance stability.
    
    The "Great Inequality" is a historical term for their near-resonance.
    """
    
    def __init__(self, enabled=True, tolerance=0.01):
        """
        Args:
            enabled: Enable resonance checking
            tolerance: Maximum allowed deviation (1% default)
        """
        self.enabled = enabled
        self.tolerance = tolerance
        
        # Nominal values
        self.nominal_ratio = 2.5  # P_saturn / P_jupiter ≈ 2.5
        self.min_ratio = self.nominal_ratio * (1 - tolerance)
        self.max_ratio = self.nominal_ratio * (1 + tolerance)
        
        logging.info(f"Jupiter-Saturn Inequality Monitor: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Nominal ratio: {self.nominal_ratio}")
            logging.info(f"  Allowed range: {self.min_ratio:.3f} - {self.max_ratio:.3f}")
    
    def check_resonance(self, sim, jupiter_index=1, saturn_index=2):
        """
        Check if Jupiter-Saturn resonance is preserved.
        
        Args:
            sim: REBOUND simulation
            jupiter_index: Index of Jupiter particle
            saturn_index: Index of Saturn particle
        
        Returns:
            dict: Resonance status
        """
        if not self.enabled:
            return {'passes': True, 'ratio': self.nominal_ratio, 'deviation': 0.0}
        
        try:
            # Calculate orbital periods
            jupiter = sim.particles[jupiter_index]
            saturn = sim.particles[saturn_index]
            
            orbit_j = jupiter.calculate_orbit(primary=sim.particles[0])
            orbit_s = saturn.calculate_orbit(primary=sim.particles[0])
            
            P_jupiter = orbit_j.P
            P_saturn = orbit_s.P
            
            # Period ratio
            ratio = P_saturn / P_jupiter
            
            # Deviation from nominal
            deviation = abs(ratio - self.nominal_ratio) / self.nominal_ratio
            
            # Check constraint
            passes = (self.min_ratio <= ratio <= self.max_ratio)
            
            result = {
                'passes': passes,
                'ratio': ratio,
                'deviation': deviation,
                'P_jupiter': P_jupiter,
                'P_saturn': P_saturn
            }
            
            if not passes:
                logging.warning(f"Resonance violation!")
                logging.warning(f"  Ratio: {ratio:.4f} (should be {self.nominal_ratio:.4f})")
                logging.warning(f"  Deviation: {deviation*100:.2f}%")
            else:
                logging.info(f"Resonance preserved: ratio = {ratio:.4f}")
            
            return result
            
        except Exception as e:
            logging.error(f"Failed to check resonance: {e}")
            return {'passes': False, 'error': str(e)}
    
    def get_penalty(self, sim, jupiter_index=1, saturn_index=2):
        """
        Calculate penalty score for resonance violation.
        
        Args:
            sim: Simulation
            jupiter_index: Jupiter index
            saturn_index: Saturn index
        
        Returns:
            float: Penalty (0 if passes, infinite if fails)
        """
        result = self.check_resonance(sim, jupiter_index, saturn_index)
        
        if result['passes']:
            return 0.0
        else:
            return 1e9  # Infinite penalty - instant veto


if __name__ == "__main__":
    # Test module
    print("=== Testing Jupiter-Saturn Inequality ===\n")
    
    monitor = JupiterSaturnInequality(enabled=True, tolerance=0.01)
    
    # Create test simulation
    import rebound
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    
    sim.add(m=1.0)  # Sun
    sim.add(m=9.5458e-4, a=5.2, e=0.048)  # Jupiter
    sim.add(m=2.8588e-4, a=9.58, e=0.056)  # Saturn
    
    sim.move_to_com()
    
    # Check resonance
    print("Testing with normal configuration:")
    result = monitor.check_resonance(sim)
    print(f"  Period ratio: {result['ratio']:.4f}")
    print(f"  Deviation: {result['deviation']*100:.2f}%")
    print(f"  Status: {'PASS ✓' if result['passes'] else 'FAIL ✗'}\n")
    
    # Test with perturbed Saturn
    print("Testing with perturbed Saturn (a=10.5 AU):")
    sim.particles[2].a = 10.5
    result2 = monitor.check_resonance(sim)
    print(f"  Period ratio: {result2['ratio']:.4f}")
    print(f"  Deviation: {result2['deviation']*100:.2f}%")
    print(f"  Status: {'PASS ✓' if result2['passes'] else 'FAIL ✗'}")
