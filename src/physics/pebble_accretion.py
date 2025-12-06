"""
Pebble Accretion Density Module
Category E3: Planetary Physics [LOW]

Planet formation location determines density:
- Formed near Neptune (ice-poor): ρ ≈ 2.0 g/cm³
- Formed far out/rogue (ice-rich): ρ ≈ 1.2 g/cm³

This affects radius for given mass → affects brightness.

Reference: Lambrechts & Johansen (2012) "Rapid growth of gas-giant cores"
Astronomy & Astrophysics, 544, A32
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PEBBLE - %(message)s')

class PebbleAccretionDensity:
    """
    Determines planet density based on formation scenario.
    
    Uses pebble accretion theory to predict bulk composition.
    """
    
    def __init__(self, enabled=True):
        """
        Args:
            enabled: Enable pebble accretion density calculations
        """
        self.enabled = enabled
        
        # Density scenarios (g/cm³)
        self.densities = {
            'native_ejection': 2.0,   # Formed near Neptune, rock-rich
            'rogue_capture': 1.2,      # Formed in outer disk, ice-rich
            'ice_giant': 1.6,          # Uranus/Neptune-like
            'super_earth': 2.5         # Rocky composition
        }
        
        logging.info(f"Pebble Accretion Density: {'ENABLED' if enabled else 'DISABLED'}")
    
    def calculate_density(self, formation_scenario='rogue_capture'):
        """
        Get bulk density for formation scenario.
        
        Args:
            formation_scenario: 'native_ejection', 'rogue_capture', 
                               'ice_giant', 'super_earth'
        
        Returns:
            float: Density (g/cm³)
        """
        if not self.enabled:
            return 1.5  # Default mid-range
        
        density = self.densities.get(formation_scenario, 1.5)
        
        logging.info(f"Formation scenario: {formation_scenario}")
        logging.info(f"  Predicted density: {density:.2f} g/cm³")
        
        return density
    
    def mass_to_radius(self, m_earth, density_gcm3):
        """
        Convert mass to radius given density.
        
        M = (4/3)πR³ρ
        R = (3M / 4πρ)^(1/3)
        
        Args:
            m_earth: Mass (Earth masses)
            density_gcm3: Density (g/cm³)
        
        Returns:
            float: Radius (Earth radii)
        """
        # Earth parameters
        M_earth_kg = 5.972e24
        R_earth_m = 6.371e6
        rho_earth_gcm3 = 5.52
        
        # Scale radius
        # R ∝ M^(1/3) / ρ^(1/3)
        R_earth = (m_earth / (density_gcm3 / rho_earth_gcm3))**(1/3)
        
        return R_earth
    
    def calculate_brightness_impact(self, m_earth, scenario='rogue_capture'):
        """
        Calculate how density affects brightness.
        
        Lower density → larger radius → more surface area → brighter
        
        Args:
            m_earth: Mass (Earth masses)
            scenario: Formation scenario
        
        Returns:
            dict: Radius and brightness parameters
        """
        if not self.enabled:
            density = 1.5
        else:
            density = self.calculate_density(scenario)
        
        # Calculate radius
        R_earth = self.mass_to_radius(m_earth, density)
        
        # Brightness scales with R²
        # Magnitude difference: Δm = -2.5 log₁₀(R₂²/R₁²)
        
        # Compare to baseline (ρ = 1.5)
        R_baseline = self.mass_to_radius(m_earth, 1.5)
        
        flux_ratio = (R_earth / R_baseline)**2
        mag_diff = -2.5 * np.log10(flux_ratio)
        
        result = {
            'density': density,
            'radius_earth': R_earth,
            'radius_baseline': R_baseline,
            'mag_diff': mag_diff,
            'scenario': scenario
        }
        
        logging.info(f"\nDensity Impact on Brightness:")
        logging.info(f"  Mass: {m_earth:.1f} M⊕")
        logging.info(f"  Density: {density:.2f} g/cm³")
        logging.info(f"  Radius: {R_earth:.2f} R⊕")
        logging.info(f"  Magnitude shift: {mag_diff:+.2f}")
        
        return result
    
    def compare_scenarios(self, m_earth):
        """
        Compare all formation scenarios.
        
        Args:
            m_earth: Planet mass (Earth masses)
        
        Returns:
            dict: Comparison of all scenarios
        """
        print(f"\n{'='*60}")
        print(f"Pebble Accretion Comparison: {m_earth:.0f} M⊕")
        print(f"{'='*60}")
        
        results = {}
        
        for scenario in self.densities.keys():
            result = self.calculate_brightness_impact(m_earth, scenario)
            results[scenario] = result
            
            print(f"\n{scenario.upper()}:")
            print(f"  Density: {result['density']:.2f} g/cm³")
            print(f"  Radius: {result['radius_earth']:.2f} R⊕")
            print(f"  Magnitude: {result['mag_diff']:+.2f} (vs baseline)")
        
        return results


if __name__ == "__main__":
    # Test module
    print("=== Testing Pebble Accretion Density ===")
    
    pebble = PebbleAccretionDensity(enabled=True)
    
    # Test for 5 Earth mass planet
    results = pebble.compare_scenarios(m_earth=5.0)
    
    # Test for 10 Earth mass planet
    results2 = pebble.compare_scenarios(m_earth=10.0)
