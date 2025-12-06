"""
AIC/BIC Model Selection
Category I3: Statistical Validation [HIGH]

Prevents overfitting: With enough parameters, you can fit an elephant.
Uses Information Criteria to penalize model complexity.

AIC (Akaike) = 2k - 2ln(L)
BIC (Bayesian) = k*ln(n) - 2ln(L)

where k = number of parameters, n = data points, L = likelihood

Lower is better. If BIC(Planet9) > BIC(NullModel), you're overfitting.
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MODEL_SEL - %(message)s')

class ModelSelector:
    """
    Compares Planet 9 model against null hypothesis using information criteria.
    
    Reference: Liddle, A. R. (2007) "Information criteria for astrophysical model selection." MNRAS.
    """
    
    def __init__(self):
        logging.info("Model Selector initialized")
    
    def calculate_aic(self, log_likelihood, n_params):
        """
        Calculate Akaike Information Criterion.
        
        AIC = 2k - 2ln(L)
        
        Args:
            log_likelihood: Log likelihood of model
            n_params: Number of free parameters
        
        Returns:
            float: AIC value
        """
        aic = 2 * n_params - 2 * log_likelihood
        return aic
    
    def calculate_bic(self, log_likelihood, n_params, n_data):
        """
        Calculate Bayesian Information Criterion.
        
        BIC = k*ln(n) - 2ln(L)
        
        Args:
            log_likelihood: Log likelihood of model
            n_params: Number of free parameters
            n_data: Number of data points
        
        Returns:
            float: BIC value
        """
        bic = n_params * np.log(n_data) - 2 * log_likelihood
        return bic
    
    def cost_to_log_likelihood(self, cost, n_data):
        """
        Convert cost function to log likelihood.
        
        Assumes cost is chi-squared-like:
        cost = sum((observed - predicted)^2 / sigma^2)
        
        Then: log L = -cost/2 - n/2*log(2π) - sum(log(sigma))
        
        Args:
            cost: Total cost from judge
            n_data: Number of data points
        
        Returns:
            float: Log likelihood
        """
        # Simplified: assume uniform uncertainties
        log_likelihood = -cost / 2.0
        return log_likelihood
    
    def compare_models(self, cost_p9, cost_null, n_params_p9=6, n_params_null=0, n_data=10):
        """
        Compare Planet 9 model vs null hypothesis.
        
        Args:
            cost_p9: Cost with Planet 9
            cost_null: Cost without Planet 9
            n_params_p9: Parameters for P9 (a, e, i, Ω, ω, m)
            n_params_null: Parameters for null (0)
            n_data: Number of eTNOs used
        
        Returns:
            dict: Comparison results
        """
        logging.info("="*70)
        logging.info("MODEL SELECTION: Planet 9 vs Null Hypothesis")
        logging.info("="*70)
        
        # Convert costs to log likelihoods
        log_L_p9 = self.cost_to_log_likelihood(cost_p9, n_data)
        log_L_null = self.cost_to_log_likelihood(cost_null, n_data)
        
        # Calculate AIC
        aic_p9 = self.calculate_aic(log_L_p9, n_params_p9)
        aic_null = self.calculate_aic(log_L_null, n_params_null)
        delta_aic = aic_p9 - aic_null
        
        # Calculate BIC
        bic_p9 = self.calculate_bic(log_L_p9, n_params_p9, n_data)
        bic_null = self.calculate_bic(log_L_null, n_params_null, n_data)
        delta_bic = bic_p9 - bic_null
        
        # Interpretation
        # Δ < -10: Decisive evidence for P9
        # -10 < Δ < -2: Strong evidence for P9
        # -2 < Δ < 2: Weak/no preference
        # Δ > 2: Evidence against P9 (overfitting)
        
        if delta_bic < -10:
            verdict = "DECISIVE evidence for Planet 9"
        elif delta_bic < -2:
            verdict = "STRONG evidence for Planet 9"
        elif delta_bic < 2:
            verdict = "Weak evidence (inconclusive)"
        else:
            verdict = "OVERFITTING - Planet 9 model too complex"
        
        results = {
            'cost_p9': cost_p9,
            'cost_null': cost_null,
            'log_L_p9': log_L_p9,
            'log_L_null': log_L_null,
            'aic_p9': aic_p9,
            'aic_null': aic_null,
            'delta_aic': delta_aic,
            'bic_p9': bic_p9,
            'bic_null': bic_null,
            'delta_bic': delta_bic,
            'verdict': verdict
        }
        
        # Report
        logging.info(f"\nModel: Planet 9")
        logging.info(f"  Cost: {cost_p9:.2f}")
        logging.info(f"  Parameters: {n_params_p9}")
        logging.info(f"  AIC: {aic_p9:.2f}")
        logging.info(f"  BIC: {bic_p9:.2f}")
        
        logging.info(f"\nModel: Null Hypothesis")
        logging.info(f"  Cost: {cost_null:.2f}")
        logging.info(f"  Parameters: {n_params_null}")
        logging.info(f"  AIC: {aic_null:.2f}")
        logging.info(f"  BIC: {bic_null:.2f}")
        
        logging.info(f"\nComparison:")
        logging.info(f"  ΔAIC: {delta_aic:.2f}")
        logging.info(f"  ΔBIC: {delta_bic:.2f}")
        logging.info(f"  Verdict: {verdict}")
        
        return results


if __name__ == "__main__":
    # Test module
    print("=== Testing Model Selector ===\n")
    
    selector = ModelSelector()
    
    # Example: Good Planet 9 model
    results = selector.compare_models(
        cost_p9=25.0,      # Good fit with P9
        cost_null=1000.0,  # Bad fit without P9
        n_params_p9=6,
        n_params_null=0,
        n_data=10
    )
    
    print(f"\n✓ {results['verdict']}")
    
    # Example: Overfitting
    print("\n\n=== Overfitting Test ===\n")
    results2 = selector.compare_models(
        cost_p9=24.0,      # Slightly better fit
        cost_null=25.0,    # But null is almost as good
        n_params_p9=6,
        n_params_null=0,
        n_data=10
    )
    
    print(f"\n{results2['verdict']}")
