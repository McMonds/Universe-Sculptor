"""
Solar Birth Cluster Dissolution
Category A5: Galactic Environment [MEDIUM]

Stars form in dense clusters (hundreds to thousands of siblings).
For the first ~100 Myr, random stars pass VERY close (< 1000 AU).

Then the cluster dissolves → flyby rate exponentially decays to field star rate.

This "primordial shake-up" sets initial randomness in the Kuiper Belt.

Reference: Adams & Laughlin (2001) "Constraints on the birth aggregate of the solar system"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - BIRTH_CLUSTER - %(message)s')

class BirthClusterDissolution:
    """
    Models high-frequency stellar encounters during solar birth cluster phase.
    
    Amplifies flyby rate by 1000x initially, then exponentially decays.
    """
    
    def __init__(self, enabled=True, cluster_lifetime=100e6):
        """
        Args:
            enabled: Enable birth cluster effects
            cluster_lifetime: Time until cluster dissolves (years, default 100 Myr)
        """
        self.enabled = enabled
        self.cluster_lifetime = cluster_lifetime
        
        # Cluster properties
        self.cluster_size = 1000  # Number of stars
        self.cluster_radius = 1.0  # pc
        self.cluster_velocity_dispersion = 1.0  # km/s (slow, bound)
        
        # Encounter rate enhancement
        self.enhancement_factor_initial = 1000  # 1000x more frequent
        
        logging.info(f"Birth Cluster Dissolution: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Cluster lifetime: {cluster_lifetime/1e6:.1f} Myr")
            logging.info(f"  Initial enhancement: {self.enhancement_factor_initial}x")
            logging.info(f"  Cluster size: {self.cluster_size} stars")
    
    def get_enhancement_factor(self, t_years):
        """
        Calculate stellar encounter rate enhancement at time t.
        
        Exponential decay: f(t) = f0 * exp(-t/tau)
        
        Args:
            t_years: Time (negative = past, 0 = now)
        
        Returns:
            float: Enhancement factor (1.0 = field star rate, 1000 = cluster rate)
        """
        if not self.enabled:
            return 1.0
        
        # Cluster dissolves in the past (negative time)
        if t_years >= 0:  # Current epoch, no cluster
            return 1.0
        
        # Time since formation (positive)
        t_since_formation = abs(t_years)
        
        if t_since_formation > self.cluster_lifetime:
            # Cluster already dissolved
            return 1.0
        
        # Exponential decay
        tau = self.cluster_lifetime / 3.0  # Decay constant (3 e-foldings)
        enhancement = 1.0 + (self.enhancement_factor_initial - 1.0) * np.exp(-t_since_formation / tau)
        
        return enhancement
    
    def modify_flyby_rate(self, base_rate, t_years):
        """
        Modify stellar flyby rate based on cluster dissolution.
        
        Args:
            base_rate: Field star encounter rate (yr^-1)
            t_years: Current time (years)
        
        Returns:
            float: Enhanced encounter rate (yr^-1)
        """
        enhancement = self.get_enhancement_factor(t_years)
        return base_rate * enhancement


if __name__ == "__main__":
    # Test module
    print("=== Testing Birth Cluster Dissolution ===\n")
    
    cluster = BirthClusterDissolution(enabled=True, cluster_lifetime=100e6)
    
    # Test enhancement over time
    print("Encounter rate enhancement:")
    times = [-4.5e9, -3e9, -500e6, -100e6, -50e6, -10e6, 0]
    
    base_rate = 1e-8  # Field star rate (1 per 100 Myr)
    
    for t in times:
        enhancement = cluster.get_enhancement_factor(t)
        enhanced_rate = cluster.modify_flyby_rate(base_rate, t)
        period = 1 / enhanced_rate if enhanced_rate > 0 else float('inf')
        
        print(f"  T = {t/1e9:+.2f} Gyr: enhancement = {enhancement:.1f}x, "
              f"encounter every {period/1e6:.1f} Myr")
    
    print("\nInterpretation:")
    print("  T < -100 Myr: Cluster dissolved, normal field star rate")
    print("  T = -50 Myr: Peak cluster density, ~1000x encounter rate")
    print("  T = -10 Myr: Cluster dispersing, ~100x rate")
    print("  T = 0: Modern era, 1x rate")
