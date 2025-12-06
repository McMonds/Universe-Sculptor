"""
Null Hypothesis Monte Carlo Validation
Category I1: Statistical Validation [CRITICAL]

The "5-Sigma" Test: Generate thousands of random solar systems WITHOUT Planet 9
and measure how often clustering happens by pure luck.

If clustering occurs <0.3% of the time randomly, our P9 detection is statistically significant.
"""
import numpy as np
import rebound
import logging
from typing import Dict, List
from src.judge import Judge
from src.oracle import Oracle

logging.basicConfig(level=logging.INFO, format='%(asctime)s - NULL_TEST - %(message)s')

class NullHypothesisValidator:
    """
    Tests whether observed clustering could occur by random chance.
    
    Method: Generate N random universes without Planet 9, measure clustering.
    If real universe is in the top 0.3%, it's a 3-sigma detection.
    If real universe is in the top 0.003%, it's a 5-sigma detection (Nobel-worthy).
    """
    
    def __init__(self, n_trials=10000, target_significance=5.0):
        """
        Args:
            n_trials: Number of random universes to generate
            target_significance: Target sigma (5.0 = 5-sigma)
        """
        self.n_trials = n_trials
        self.target_significance = target_significance
        self.oracle = Oracle()
        self.judge = Judge()
        
        # Significance thresholds
        self.sigma_to_percentile = {
            1.0: 84.1,  # 1-sigma = top 15.9%
            2.0: 97.7,  # 2-sigma = top 2.3%
            3.0: 99.7,  # 3-sigma = top 0.3%
            4.0: 99.99, # 4-sigma = top 0.01%
            5.0: 99.9997  # 5-sigma = top 0.0003%
        }
        
        logging.info(f"Null Hypothesis Validator initialized")
        logging.info(f"  Trials: {n_trials}")
        logging.info(f"  Target: {target_significance}-sigma")
    
    def generate_random_universe(self, seed=None):
        """
        Create a random solar system without Planet 9.
        
        Randomizes:
        - eTNO orbital elements (but keeps them distant)
        - Initial phases
        
        Args:
            seed: Random seed for reproducibility
        
        Returns:
            rebound.Simulation
        """
        if seed is not None:
            np.random.seed(seed)
        
        sim = rebound.Simulation()
        sim.units = ('AU', 'yr', 'Msun')
        sim.integrator = "whfast"
        sim.dt = 0.5
        
        # Add Sun and Giants (same as real universe)
        data = self.oracle.fetch_data()
        
        for obj in data:
            if obj['is_planet']:
                if obj['name'] == 'Sun':
                    sim.add(m=1.0)
                else:
                    mass = {'Jupiter': 9.5458e-4, 'Saturn': 2.8588e-4,
                           'Uranus': 4.366e-5, 'Neptune': 5.151e-5}.get(obj['name'], 0)
                    sim.add(m=mass, x=obj['x'], y=obj['y'], z=obj['z'],
                          vx=obj['vx'], vy=obj['vy'], vz=obj['vz'])
        
        # Add randomized eTNOs (NO Planet 9)
        # Keep similar orbital characteristics but randomize angles
        for obj in data:
            if not obj['is_planet'] and 'a' in obj:
                # Randomize orbital angles
                random_Omega = np.random.uniform(0, 2*np.pi)
                random_omega = np.random.uniform(0, 2*np.pi)
                random_M = np.random.uniform(0, 2*np.pi)
                
                # Keep a, e, inc similar to observed (but randomize phases)
                sim.add(m=0, 
                       a=obj['a'],
                       e=obj['e'],
                       inc=obj['inc'],
                       Omega=random_Omega,
                       omega=random_omega,
                       M=random_M)
        
        sim.move_to_com()
        return sim
    
    def run_monte_carlo(self, observed_cost):
        """
        Run the Monte Carlo null hypothesis test.
        
        Args:
            observed_cost: The clustering cost from the REAL universe
        
        Returns:
            dict: Results including p-value and sigma
        """
        logging.info("="*70)
        logging.info("MONTE CARLO NULL HYPOTHESIS TEST")
        logging.info("="*70)
        logging.info(f"Observed clustering cost: {observed_cost:.2f}")
        logging.info(f"Running {self.n_trials} random trials...\n")
        
        random_costs = []
        
        for i in range(self.n_trials):
            try:
                # Generate random universe
                sim = self.generate_random_universe(seed=i)
                
                # Integrate forward a bit (optional, for testing)
                # sim.integrate(100 * 2 * np.pi)
                
                # Measure clustering
                cost = self.judge.evaluate(sim, p9_params={})
                random_costs.append(cost)
                
                if (i + 1) % 1000 == 0:
                    logging.info(f"  Progress: {i+1}/{self.n_trials} ({(i+1)/self.n_trials*100:.1f}%)")
                
            except Exception as e:
                logging.warning(f"  Trial {i} failed: {e}")
                random_costs.append(1e9)  # Max penalty
        
        # Statistical analysis
        random_costs = np.array(random_costs)
        
        # How many random universes had BETTER clustering than observed?
        better_count = np.sum(random_costs <= observed_cost)
        p_value = better_count / len(random_costs)
        
        # Convert to sigma
        if p_value < 1e-7:
            sigma = 5.0  # Beyond 5-sigma
        elif p_value < 0.01:
            # Approximate sigma from percentile
            percentile = (1 - p_value) * 100
            for s, p in sorted(self.sigma_to_percentile.items(), reverse=True):
                if percentile >= p:
                    sigma = s
                    break
            else:
                sigma = 0.0
        else:
            sigma = 0.0  # Not significant
        
        # Results
        results = {
            'observed_cost': observed_cost,
            'random_costs': random_costs,
            'mean_random': np.mean(random_costs),
            'std_random': np.std(random_costs),
            'better_count': better_count,
            'p_value': p_value,
            'sigma': sigma,
            'significant': sigma >= 3.0
        }
        
        # Report
        logging.info("\n" + "="*70)
        logging.info("RESULTS")
        logging.info("="*70)
        logging.info(f"Random universes mean cost: {results['mean_random']:.2f} ± {results['std_random']:.2f}")
        logging.info(f"Observed cost: {observed_cost:.2f}")
        logging.info(f"Better than {better_count}/{len(random_costs)} random universes")
        logging.info(f"p-value: {p_value:.2e}")
        logging.info(f"Statistical significance: {sigma:.1f}-sigma")
        
        if results['significant']:
            logging.info("✓ NULL HYPOTHESIS REJECTED - Discovery is statistically significant!")
        else:
            logging.warning("✗ NULL HYPOTHESIS NOT REJECTED - Could be random chance")
        
        return results
    
    def generate_report(self, results, output_file='null_hypothesis_report.txt'):
        """
        Generate a publication-quality report.
        """
        with open(output_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("NULL HYPOTHESIS MONTE CARLO VALIDATION REPORT\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Trials: {self.n_trials}\n")
            f.write(f"Observed clustering cost: {results['observed_cost']:.2f}\n")
            f.write(f"Random universe mean: {results['mean_random']:.2f} ± {results['std_random']:.2f}\n\n")
            
            f.write(f"Statistical Analysis:\n")
            f.write(f"  p-value: {results['p_value']:.2e}\n")
            f.write(f"  Significance: {results['sigma']:.1f}-sigma\n")
            f.write(f"  Conclusion: {'SIGNIFICANT' if results['significant'] else 'NOT SIGNIFICANT'}\n\n")
            
            f.write("Interpretation:\n")
            if results['sigma'] >= 5.0:
                f.write("  5-sigma detection - Discovery-level significance (Nobel-worthy)\n")
            elif results['sigma'] >= 3.0:
                f.write("  3-sigma detection - Evidence-level significance (publishable)\n")
            else:
                f.write("  <3-sigma - Insufficient evidence for discovery claim\n")
        
        logging.info(f"Report saved: {output_file}")


if __name__ == "__main__":
    # Quick test
    print("=== Testing Null Hypothesis Validator ===\n")
    
    validator = NullHypothesisValidator(n_trials=100, target_significance=3.0)
    
    # Simulate an "observed" clustering cost
    # In reality, this comes from your real Planet 9 candidate
    observed_cost = 25.0  # Good clustering
    
    results = validator.run_monte_carlo(observed_cost)
    validator.generate_report(results, 'test_null_hypothesis.txt')
