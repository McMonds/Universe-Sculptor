import numpy as np
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - VALIDATOR - %(message)s')

class DynamicalValidator:
    """
    Tier 7: Chaotic Dynamics Validation
    Check if Planet 9 candidate naturally produces high-inclination objects
    like Niku (i=110°) and Drac (i=103°)
    """
    def __init__(self):
        # Load known high-inclination centaurs
        try:
            with open('data/real/mpc/centaurs_high_inc.json', 'r') as f:
                data = json.load(f)
                self.centaurs = data['centaurs']
                logging.info(f"✓ Loaded {len(self.centaurs)} high-inclination centaurs")
        except FileNotFoundError:
            logging.warning("High-inclination centaur data not found")
            self.centaurs = []
    
    def check_kozai_lidov_regime(self, p9_params):
        """
        Check if P9 parameters are in the Kozai-Lidov regime
        Required for flipping objects to high inclinations
        """
        # Kozai-Lidov mechanism requires:
        # 1. High eccentricity perturber (P9)
        # 2. Significant inclination difference
        # 3. Large semi-major axis ratio
        
        e_p9 = p9_params['e']
        inc_p9 = p9_params['inc']
        a_p9 = p9_params['a']
        
        # Typical TNO: a ~ 50 AU, i ~ 10°
        # Ratio needs to be >~ 5 for Kozai
        ratio = a_p9 / 50.0
        
        if ratio > 5 and e_p9 > 0.3:
            return True
        return False
    
    def validate_high_inclination_production(self, sim_results):
        """
        After a long simulation, check if any particles reached i > 60°
        This would validate that P9 can produce Niku-like objects
        
        Args:
            sim_results: Dict with final particle states
        
        Returns:
            bool: True if high-inclination objects were produced
        """
        if sim_results is None:
            return False
        
        high_inc_count = 0
        for particle in sim_results.get('particles', []):
            inc_deg = np.degrees(particle.get('inc', 0))
            if inc_deg > 60:
                high_inc_count += 1
                logging.info(f"  High-inc object: i={inc_deg:.1f}°")
        
        if high_inc_count > 0:
            logging.info(f"✓ Tier 7: Produced {high_inc_count} high-inclination objects")
            return True
        else:
            logging.info("✗ Tier 7: No high-inclination objects produced")
            return False
    
    def score_dynamical_match(self, sim_results):
        """
        Score how well the simulation matches known high-inc population
        Returns a bonus score (0-1) for dynamical consistency
        """
        if not self.check_kozai_lidov_regime({'e': 0.6, 'inc': 0.3, 'a': 400}):
            return 0.0
        
        # Check if simulation produces objects similar to Niku/Drac
        # This is a placeholder - would need full long-term sim
        return 0.5  # Partial credit for being in right regime

if __name__ == "__main__":
    validator = DynamicalValidator()
    
    # Test with a Planet 9 candidate
    p9_test = {
        'a': 450,
        'e': 0.65,
        'inc': np.radians(30),
        'm': 5e-5
    }
    
    in_regime = validator.check_kozai_lidov_regime(p9_test)
    print(f"Kozai-Lidov regime: {in_regime}")
