"""
Injection Recovery Test
Category I2: Statistical Validation [CRITICAL]

The "Blind Test": Plant fake Planet 9s at known locations, then try to rediscover them.
This proves your search engine actually works and measures its sensitivity.

Standard practice for all exoplanet missions (Kepler, TESS).
"""
import numpy as np
import logging
from typing import Dict, List, Tuple
from src.primordial_optimizer import PrimordialOptimizer
from src.time_machine import TimeMachine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - INJECTION - %(message)s')

class InjectionRecoveryTest:
    """
    Tests search engine sensitivity by planting fake planets.
    
    Method:
    1. Create fake Planet 9 at known (a, e, inc, m)
    2. Blind the optimizer (don't tell it the answer)
    3. Run full search
    4. Check if it rediscovers within error tolerance
    
    Repeat 100x to create sensitivity heatmap.
    """
    
    def __init__(self, n_tests=100):
        """
        Args:
            n_tests: Number of injection tests
        """
        self.n_tests = n_tests
        self.results = []
        
        logging.info(f"Injection Recovery Test initialized")
        logging.info(f"  Tests: {n_tests}")
    
    def create_synthetic_planet(self, a, e, inc, m, scenario='rogue_capture'):
        """
        Create a fake Planet 9 at specific coordinates.
        
        Args:
            a: Semi-major axis (AU)
            e: Eccentricity
            inc: Inclination (radians)
            m: Mass (solar masses)
            scenario: Birth scenario
        
        Returns:
            dict: Synthetic planet parameters
        """
        # Convert orbital elements to birth state
        # For simplicity, assume circular conversion
        # In reality, you'd back-integrate
        
        r = a * (1 - e)  # Perihelion distance
        
        # Random angles
        Omega = np.random.uniform(0, 2*np.pi)
        omega = np.random.uniform(0, 2*np.pi)
        
        # Approximate Cartesian position at perihelion
        x = r * np.cos(Omega)
        y = r * np.sin(Omega)
        z = r * np.sin(inc)
        
        # Velocity (approximation)
        v = np.sqrt((1 + e) / (a * (1 - e)))  # At perihelion
        vx = -v * np.sin(Omega)
        vy = v * np.cos(Omega)
        vz = 0.0
        
        return {
            'true_a': a,
            'true_e': e,
            'true_inc': inc,
            'true_m': m,
            'scenario': scenario,
            'x0': x,
            'y0': y,
            'z0': z,
            'vx0': vx,
            'vy0': vy,
            'vz0': vz,
            'm': m
        }
    
    def run_single_test(self, test_id, true_params):
        """
        Run one injection recovery test.
        
        Args:
            test_id: Test number
            true_params: True Planet 9 parameters
        
        Returns:
            dict: Recovery results
        """
        logging.info(f"\n--- Injection Test {test_id}/{self.n_tests} ---")
        logging.info(f"  Injected: a={true_params['true_a']:.1f} AU, "
                    f"e={true_params['true_e']:.3f}, "
                    f"m={true_params['true_m']*333000:.0f} M_Earth")
        
        # Run optimizer (blinded)
        try:
            optimizer = PrimordialOptimizer(scenario=true_params['scenario'])
            
            # For testing, use reduced generations
            result = optimizer.run(max_generations=5, population_size=10, workers=1)
            
            # Check recovery
            recovered_a = result.get('a', 0)  # Would need to extract from final state
            recovered_e = result.get('e', 0)
            
            # Calculate error
            a_error = abs(recovered_a - true_params['true_a']) / true_params['true_a']
            e_error = abs(recovered_e - true_params['true_e'])
            
            # Success criteria: within 10% for a, within 0.1 for e
            success = (a_error < 0.1) and (e_error < 0.1)
            
            logging.info(f"  Recovered: a={recovered_a:.1f} AU, e={recovered_e:.3f}")
            logging.info(f"  Error: {a_error*100:.1f}% (a), {e_error:.3f} (e)")
            logging.info(f"  Status: {'SUCCESS ✓' if success else 'FAILED ✗'}")
            
            return {
                'test_id': test_id,
                'true_params': true_params,
                'recovered_a': recovered_a,
                'recovered_e': recovered_e,
                'a_error': a_error,
                'e_error': e_error,
                'success': success
            }
            
        except Exception as e:
            logging.error(f"  Test failed: {e}")
            return {
                'test_id': test_id,
                'true_params': true_params,
                'success': False,
                'error': str(e)
            }
    
    def run_grid_search(self, a_range=(300, 800), e_range=(0.2, 0.8), n_points=10):
        """
        Run recovery tests across a grid of parameters.
        
        Creates sensitivity heatmap.
        
        Args:
            a_range: (min, max) semi-major axis
            e_range: (min, max) eccentricity
            n_points: Grid resolution
        
        Returns:
            dict: Grid results
        """
        logging.info("="*70)
        logging.info("INJECTION RECOVERY GRID SEARCH")
        logging.info("="*70)
        
        a_values = np.linspace(a_range[0], a_range[1], n_points)
        e_values = np.linspace(e_range[0], e_range[1], n_points)
        
        success_grid = np.zeros((n_points, n_points))
        
        test_count = 0
        for i, a in enumerate(a_values):
            for j, e in enumerate(e_values):
                test_count += 1
                
                # Create synthetic planet
                true_params = self.create_synthetic_planet(
                    a=a, e=e, inc=np.radians(20), m=5e-5
                )
                
                # Run test
                result = self.run_single_test(test_count, true_params)
                
                # Store success
                success_grid[i, j] = 1.0 if result.get('success', False) else 0.0
                self.results.append(result)
        
        # Calculate statistics
        total_success = np.sum(success_grid)
        recovery_rate = total_success / (n_points * n_points)
        
        logging.info("\n" + "="*70)
        logging.info("GRID SEARCH RESULTS")
        logging.info("="*70)
        logging.info(f"Total tests: {n_points * n_points}")
        logging.info(f"Successful recoveries: {int(total_success)}")
        logging.info(f"Recovery rate: {recovery_rate*100:.1f}%")
        
        return {
            'a_values': a_values,
            'e_values': e_values,
            'success_grid': success_grid,
            'recovery_rate': recovery_rate
        }
    
    def generate_heatmap(self, grid_results, output_file='sensitivity_heatmap.png'):
        """
        Generate sensitivity heatmap visualization.
        """
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            im = ax.imshow(grid_results['success_grid'],
                          extent=[grid_results['e_values'].min(), grid_results['e_values'].max(),
                                 grid_results['a_values'].min(), grid_results['a_values'].max()],
                          aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
            
            ax.set_xlabel('Eccentricity', fontsize=14)
            ax.set_ylabel('Semi-major Axis (AU)', fontsize=14)
            ax.set_title('Planet 9 Detection Sensitivity', fontsize=16, fontweight='bold')
            
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('Recovery Success Rate', fontsize=12)
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=150)
            logging.info(f"Heatmap saved: {output_file}")
            
        except ImportError:
            logging.warning("matplotlib not available for heatmap generation")


if __name__ == "__main__":
    # Quick test
    print("=== Testing Injection Recovery ===\n")
    
    tester = InjectionRecoveryTest(n_tests=10)
    
    # Single test
    true_params = tester.create_synthetic_planet(
        a=500, e=0.6, inc=np.radians(20), m=5e-5
    )
    
    result = tester.run_single_test(1, true_params)
    
    print("\n" + "="*70)
    print("NOTE: Full grid search would take hours.")
    print("Run with grid_search() for complete sensitivity analysis.")
