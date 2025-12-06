"""
MCMC Uncertainty Quantification
Category I4: Statistical Validation [HIGH]

Uses Markov Chain Monte Carlo (MCMC) to explore parameter space and
quantify uncertainties in Planet 9's properties.

Output: Not a single answer, but a probability distribution (corner plot).

Uses emcee (affine-invariant ensemble sampler).
Reference: Foreman-Mackey et al. (2013) "emcee: The MCMC Hammer"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MCMC - %(message)s')

class MCMCUncertaintyQuantifier:
    """
    Quantifies uncertainties using Markov Chain Monte Carlo.
    
    Produces posterior probability distributions for all parameters.
    """
    
    def __init__(self, n_walkers=32, n_steps=1000):
        """
        Args:
            n_walkers: Number of MCMC walkers
            n_steps: Number of MCMC steps per walker
        """
        self.n_walkers = n_walkers
        self.n_steps = n_steps
        
        logging.info(f"MCMC Uncertainty Quantifier initialized")
        logging.info(f"  Walkers: {n_walkers}")
        logging.info(f"  Steps: {n_steps}")
    
    def log_likelihood(self, params, cost_function):
        """
        Log likelihood function for MCMC.
        
        Assumes chi-squared likelihood:
        log L = -cost/2
        
        Args:
            params: Planet 9 parameters [a, e, inc, Omega, omega, m]
            cost_function: Function that returns cost for given params
        
        Returns:
            float: Log likelihood
        """
        cost = cost_function(params)
        
        # Penalize if cost is infinite (invalid params)
        if not np.isfinite(cost):
            return -np.inf
        
        # Chi-squared likelihood
        log_L = -cost / 2.0
        return log_L
    
    def log_prior(self, params):
        """
        Log prior probability.
        
        Implements physical constraints:
        - a: 300-800 AU (Planet 9 search region)
        - e: 0.2-0.8 (eccentric but bound)
        - inc: 0-90° (prograde)
        - Omega, omega: 0-360° (angles)
        - m: 3-30 Earth masses
        
        Args:
            params: [a, e, inc, Omega, omega, m]
        
        Returns:
            float: Log prior
        """
        a, e, inc, Omega, omega, m = params
        
        # Hard bounds (uniform prior within)
        if not (300 < a < 800):
            return -np.inf
        if not (0.2 < e < 0.8):
            return -np.inf
        if not (0 < inc < np.pi/2):
            return -np.inf
        if not (0 < Omega < 2*np.pi):
            return -np.inf
        if not (0 < omega < 2*np.pi):
            return -np.inf
        if not (3 < m*333000 < 30):  # Convert to Earth masses
            return -np.inf
        
        # Uniform prior (log P = 0)
        return 0.0
    
    def log_probability(self, params, cost_function):
        """
        Log posterior probability.
        
        log P(params | data) = log P(data | params) + log P(params)
                             = log_likelihood + log_prior
        
        Args:
            params: Planet 9 parameters
            cost_function: Cost evaluation function
        
        Returns:
            float: Log probability
        """
        lp = self.log_prior(params)
        
        if not np.isfinite(lp):
            return -np.inf
        
        ll = self.log_likelihood(params, cost_function)
        
        return lp + ll
    
    def run_mcmc(self, initial_guess, cost_function):
        """
        Run MCMC sampling.
        
        Args:
            initial_guess: Initial Planet 9 parameters [a, e, inc, Omega, omega, m]
            cost_function: Function that evaluates cost
        
        Returns:
            dict: MCMC results
        """
        try:
            import emcee
        except ImportError:
            logging.error("emcee not installed. Install: pip install emcee")
            return None
        
        logging.info("="*70)
        logging.info("MCMC UNCERTAINTY QUANTIFICATION")
        logging.info("="*70)
        logging.info(f"Initial guess: a={initial_guess[0]:.1f}, e={initial_guess[1]:.3f}, m={initial_guess[5]*333000:.1f} M_Earth")
        
        # Initialize walkers around initial guess
        n_dim = len(initial_guess)
        pos = initial_guess + 1e-2 * np.random.randn(self.n_walkers, n_dim)
        
        # Create sampler
        sampler = emcee.EnsembleSampler(
            self.n_walkers,
            n_dim,
            self.log_probability,
            args=(cost_function,)
        )
        
        # Run MCMC
        logging.info(f"\nRunning MCMC ({self.n_steps} steps)...")
        sampler.run_mcmc(pos, self.n_steps, progress=True)
        
        # Extract results
        samples = sampler.get_chain(discard=100, thin=10, flat=True)  # Burn-in and thinning
        
        # Calculate statistics
        param_names = ['a', 'e', 'inc', 'Omega', 'omega', 'm']
        results = {
            'samples': samples,
            'param_names': param_names,
            'statistics': {}
        }
        
        for i, name in enumerate(param_names):
            median = np.median(samples[:, i])
            std = np.std(samples[:, i])
            p16, p84 = np.percentile(samples[:, i], [16, 84])
            
            results['statistics'][name] = {
                'median': median,
                'std': std,
                'p16': p16,
                'p84': p84
            }
            
            # Convert to Earth masses for m
            if name == 'm':
                logging.info(f"\n{name}: {median*333000:.1f} ± {std*333000:.1f} M_Earth")
                logging.info(f"  68% CI: [{p16*333000:.1f}, {p84*333000:.1f}] M_Earth")
            elif name in ['inc', 'Omega', 'omega']:
                logging.info(f"\n{name}: {np.degrees(median):.1f} ± {np.degrees(std):.1f}°")
            else:
                logging.info(f"\n{name}: {median:.1f} ± {std:.1f}")
        
        return results
    
    def generate_corner_plot(self, results, output_file='corner_plot.png'):
        """
        Generate corner plot showing parameter correlations.
        """
        try:
            import corner
            import matplotlib.pyplot as plt
            
            samples = results['samples']
            param_names = results['param_names']
            
            # Convert angles to degrees for plotting
            samples_plot = samples.copy()
            samples_plot[:, 2:5] = np.degrees(samples_plot[:, 2:5])
            samples_plot[:, 5] *= 333000  # Convert mass to Earth masses
            
            labels = ['$a$ (AU)', '$e$', '$i$ (°)', '$\Omega$ (°)', '$\omega$ (°)', '$M$ ($M_\oplus$)']
            
            fig = corner.corner(
                samples_plot,
                labels=labels,
                quantiles=[0.16, 0.5, 0.84],
                show_titles=True,
                title_fmt='.2f'
            )
            
            plt.savefig(output_file, dpi=150)
            logging.info(f"\nCorner plot saved: {output_file}")
            
        except ImportError:
            logging.warning("corner package not available for plotting")


if __name__ == "__main__":
    # Test module
    print("=== Testing MCMC Uncertainty Quantifier ===\n")
    
    # Mock cost function (simple quadratic)
    def mock_cost(params):
        a, e, inc, Omega, omega, m = params
        # Minimum at a=500, e=0.6, m=5e-5
        cost = ((a - 500)/100)**2 + ((e - 0.6)/0.1)**2 + (m - 5e-5)**2 * 1e10
        return cost
    
    quantifier = MCMCUncertaintyQuantifier(n_walkers=16, n_steps=100)
    
    initial_guess = [500, 0.6, np.radians(20), np.radians(100), np.radians(150), 5e-5]
    
    print("\nNOTE: Full MCMC run takes ~hours. Running short test...")
    results = quantifier.run_mcmc(initial_guess, mock_cost)
    
    if results:
        print("\n✓ MCMC completed successfully")
        print("In production, run with n_steps=10000+ for publication quality")
