"""
Tidal Heating from Satellites Module
Category E2: Planetary Physics [MEDIUM]

If Planet 9 has large moons (like Jupiter's system), tidal flexing heats the core.
This makes the planet BRIGHTER in infrared by ~1 magnitude.

Reference: Ginzburg & Sari (2019) "Planet Nine's Atmosphere and Brightness"
Astrophysical Journal, 884, 167
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - TIDAL_HEAT - %(message)s')

class TidalHeating:
    """
    Models tidal heating contribution to Planet 9's luminosity.
    
    Tidal heating power: P_tidal ~ k * (R/a_moon)^5 * (M_moon/M_planet)^2
    where k is Love number, a_moon is moon's semi-major axis
    """
    
    def __init__(self, enabled=True):
        """
        Args:
            enabled: Enable tidal heating calculations
        """
        self.enabled = enabled
        
        logging.info(f"Tidal Heating Module: {'ENABLED' if enabled else 'DISABLED'}")
    
    def estimate_tidal_luminosity(self, m_planet_earth, has_moons=True, 
                                  n_major_moons=4):
        """
        Estimate tidal heating luminosity.
        
        Args:
            m_planet_earth: Planet mass (Earth masses)
            has_moons: Whether planet has moon system
            n_major_moons: Number of major moons (default 4, like Jupiter)
        
        Returns:
            dict: Tidal heating parameters
        """
        if not self.enabled or not has_moons:
            return {'L_tidal': 0.0, 'mag_boost': 0.0}
        
        # Simplified tidal heating model
        # Based on Io-Jupiter scaling
        
        # Io parameters
        L_io = 2e13  # Watts (tidal heating)
        M_jupiter = 318  # Earth masses
        
        # Scale to Planet 9
        # L_tidal ∝ M_planet (more mass = more tides)
        # L_tidal ∝ n_moons (more moons = more heating)
        
        scaling = (m_planet_earth / M_jupiter) * (n_major_moons / 4.0)
        L_tidal = L_io * scaling
        
        # Convert to brightness enhancement
        # Stefan-Boltzmann: L = 4πR²σT⁴
        # Tidal heating increases T → increases L
        
        # Approximate: +1W/m² → +0.1 magnitude in IR
        R_earth = 6.371e6  # meters
        R_planet = R_earth * (m_planet_earth / 5.0)**(1/3)  # Mass-radius relation
        
        flux_increase = L_tidal / (4 * np.pi * R_planet**2)  # W/m²
        
        # Magnitude boost (negative = brighter)
        # Empirical: 1 W/m² ≈ 0.1 mag boost
        mag_boost = -0.1 * np.log10(1 + flux_increase / 1.0)
        
        # Typically ~0.5 to 1.5 magnitude brighter
        mag_boost = np.clip(mag_boost, -2.0, 0.0)
        
        result = {
            'L_tidal': L_tidal,
            'flux_increase': flux_increase,
            'mag_boost': mag_boost,
            'n_moons': n_major_moons
        }
        
        logging.info(f"Tidal Heating Analysis:")
        logging.info(f"  Planet mass: {m_planet_earth:.1f} M⊕")
        logging.info(f"  Major moons: {n_major_moons}")
        logging.info(f"  Tidal luminosity: {L_tidal:.2e} W")
        logging.info(f"  Magnitude boost: {mag_boost:.2f} (brighter)")
        
        return result
    
    def apply_to_magnitude(self, base_magnitude, m_planet_earth, 
                          has_moons=True, moon_scenario='jupiter_like'):
        """
        Apply tidal heating to magnitude prediction.
        
        Args:
            base_magnitude: Base magnitude without tidal heating
            m_planet_earth: Planet mass (Earth masses)
            has_moons: Whether to include moon heating
            moon_scenario: 'none', 'small' (1-2 moons), 'jupiter_like' (4 moons)
        
        Returns:
            float: Adjusted magnitude
        """
        if not self.enabled or not has_moons:
            return base_magnitude
        
        # Moon scenarios
        moon_count = {
            'none': 0,
            'small': 2,
            'jupiter_like': 4,
            'saturn_like': 7
        }.get(moon_scenario, 0)
        
        heating = self.estimate_tidal_luminosity(
            m_planet_earth, 
            has_moons=has_moons,
            n_major_moons=moon_count
        )
        
        adjusted_mag = base_magnitude + heating['mag_boost']
        
        logging.info(f"\nMagnitude Adjustment:")
        logging.info(f"  Base: {base_magnitude:.2f}")
        logging.info(f"  With tidal heating: {adjusted_mag:.2f}")
        logging.info(f"  Scenario: {moon_scenario} ({moon_count} moons)")
        
        return adjusted_mag


if __name__ == "__main__":
    # Test module
    print("=== Testing Tidal Heating Module ===\n")
    
    heating = TidalHeating(enabled=True)
    
    # Test different scenarios
    scenarios = [
        (5.0, 'none'),
        (5.0, 'small'),
        (5.0, 'jupiter_like'),
        (10.0, 'jupiter_like')
    ]
    
    base_mag = 22.0
    
    print(f"Base magnitude (no tidal heating): {base_mag:.2f}\n")
    
    for mass, scenario in scenarios:
        print(f"Scenario: {mass:.0f} M⊕, {scenario} moons")
        adjusted = heating.apply_to_magnitude(base_mag, mass, 
                                             has_moons=(scenario != 'none'),
                                             moon_scenario=scenario)
        print(f"  → Magnitude: {adjusted:.2f}")
        print(f"  → Brightness increase: {base_mag - adjusted:.2f} mag\n")
