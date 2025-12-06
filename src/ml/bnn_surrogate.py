"""
Bayesian Neural Network Surrogate Model
Category K3: Software Engineering [MEDIUM]

Problem: REBOUND simulations take ~hours per parameter set.
Solution: Train fast neural network to predict cost in milliseconds.

Workflow:
1. Train BNN on 10,000 REBOUND runs
2. Use BNN to screen 1 million candidates → top 100
3. Run REBOUND on top 100 for precision

Speedup: 10,000x faster screening

Reference: Cranmer et al. (2020) "The frontier of simulation-based inference"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - BNN - %(message)s')

class BNNSurrogate:
    """
    Bayesian Neural Network for fast parameter screening.
    
    Uses TensorFlow Probability for uncertainty quantification.
    """
    
    def __init__(self, input_dim=6, hidden_units=[64, 32], enabled=True):
        """
        Args:
            input_dim: Number of input features (a, e, inc, Omega, omega, m)
            hidden_units: Hidden layer sizes
            enabled: Enable BNN (requires TensorFlow)
        """
        self.enabled = enabled
        self.input_dim = input_dim
        self.hidden_units = hidden_units
        self.model = None
        self.is_trained = False
        
        logging.info(f"BNN Surrogate: {'ENABLED' if enabled else 'DISABLED'}")
        
        if enabled:
            try:
                import tensorflow as tf
                import tensorflow_probability as tfp
                self.tf = tf
                self.tfp = tfp
                logging.info("  TensorFlow Probability available")
            except ImportError:
                logging.warning("  TensorFlow not available - BNN disabled")
                self.enabled = False
    
    def build_model(self):
        """
        Build Bayesian Neural Network with dropout.
        
        Architecture:
        - Input: 6 parameters (a, e, inc, Omega, omega, m)
        - Hidden: [64, 32] with dropout
        - Output: Cost prediction + uncertainty
        """
        if not self.enabled:
            return None
        
        from tensorflow import keras
        from tensorflow.keras import layers
        
        model = keras.Sequential([
            layers.Input(shape=(self.input_dim,)),
            layers.Dense(self.hidden_units[0], activation='relu'),
            layers.Dropout(0.2),  # Bayesian via dropout
            layers.Dense(self.hidden_units[1], activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(1, activation='softplus')  # Positive cost
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        logging.info(f"  Built BNN with architecture: {self.input_dim} → {self.hidden_units} → 1")
        
        return model
    
    def train(self, X_train, y_train, epochs=100, batch_size=32, validation_split=0.2):
        """
        Train BNN on REBOUND simulation data.
        
        Args:
            X_train: Training features (N, 6) [a, e, inc, Omega, omega, m]
            y_train: Training targets (N,) [cost]
            epochs: Training epochs
            batch_size: Batch size
            validation_split: Validation fraction
        
        Returns:
            dict: Training history
        """
        if not self.enabled or self.model is None:
            logging.error("BNN not initialized")
            return None
        
        logging.info(f"Training BNN on {len(X_train)} samples...")
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=0
        )
        
        self.is_trained = True
        
        final_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        
        logging.info(f"  Training complete:")
        logging.info(f"    Final loss: {final_loss:.4f}")
        logging.info(f"    Val loss: {final_val_loss:.4f}")
        
        return history.history
    
    def predict_with_uncertainty(self, X, n_samples=100):
        """
        Predict cost with uncertainty using Monte Carlo dropout.
        
        Args:
            X: Input parameters (N, 6)
            n_samples: MC samples for uncertainty
        
        Returns:
            tuple: (mean_predictions, std_predictions)
        """
        if not self.enabled or not self.is_trained:
            return None, None
        
        # MC dropout for uncertainty
        predictions = []
        for _ in range(n_samples):
            pred = self.model(X, training=True)  # Dropout active
            predictions.append(pred.numpy().flatten())
        
        predictions = np.array(predictions)
        
        mean = np.mean(predictions, axis=0)
        std = np.std(predictions, axis=0)
        
        return mean, std
    
    def screen_candidates(self, candidates, top_k=100):
        """
        Fast screening of candidate parameters.
        
        Args:
            candidates: Array of parameters (N, 6)
            top_k: Return top K candidates
        
        Returns:
            dict: Screening results
        """
        if not self.enabled or not self.is_trained:
            logging.error("BNN not trained")
            return None
        
        logging.info(f"Screening {len(candidates)} candidates...")
        
        # Predict cost + uncertainty
        mean_cost, std_cost = self.predict_with_uncertainty(candidates)
        
        # Acquisition function: minimize mean - 2*std (optimistic)
        acquisition = mean_cost - 2 * std_cost
        
        # Get top K
        top_indices = np.argsort(acquisition)[:top_k]
        
        result = {
            'top_indices': top_indices,
            'top_params': candidates[top_indices],
            'top_mean_cost': mean_cost[top_indices],
            'top_std_cost': std_cost[top_indices],
            'acquisition': acquisition[top_indices]
        }
        
        logging.info(f"  Selected top {top_k} candidates")
        logging.info(f"  Best acquisition: {acquisition[top_indices[0]]:.2f}")
        logging.info(f"  Mean cost: {mean_cost[top_indices[0]]:.2f} ± {std_cost[top_indices[0]]:.2f}")
        
        return result
    
    def save_model(self, filepath='bnn_surrogate.h5'):
        """Save trained model."""
        if self.enabled and self.is_trained:
            self.model.save(filepath)
            logging.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath='bnn_surrogate.h5'):
        """Load trained model."""
        if self.enabled:
            from tensorflow import keras
            self.model = keras.models.load_model(filepath)
            self.is_trained = True
            logging.info(f"Model loaded from {filepath}")


def generate_training_data(n_samples=1000):
    """
    Generate synthetic training data.
    
    In production, replace with actual REBOUND runs.
    """
    # Random parameters
    a = np.random.uniform(300, 800, n_samples)
    e = np.random.uniform(0.2, 0.8, n_samples)
    inc = np.random.uniform(0, np.pi/2, n_samples)
    Omega = np.random.uniform(0, 2*np.pi, n_samples)
    omega = np.random.uniform(0, 2*np.pi, n_samples)
    m = np.random.uniform(3e-5, 30e-5, n_samples)  # Solar masses
    
    X = np.column_stack([a, e, inc, Omega, omega, m])
    
    # Synthetic cost (replace with real REBOUND results)
    # Lower cost for: moderate eccentricity, high a, low inc
    cost = (
        100 * (e - 0.6)**2 +  # Prefer e~0.6
        10 * ((a - 500) / 100)**2 +  # Prefer a~500
        50 * (inc / np.pi)**2  # Prefer low inc
    )
    
    # Add noise
    cost += np.random.normal(0, 5, n_samples)
    cost = np.maximum(cost, 0)  # Positive only
    
    return X, cost


if __name__ == "__main__":
    print("=== Testing BNN Surrogate ===\n")
    
    # Generate training data
    print("Generating training data...")
    X_train, y_train = generate_training_data(n_samples=5000)
    
    # Build and train BNN
    bnn = BNNSurrogate(enabled=True)
    
    if bnn.enabled:
        bnn.build_model()
        history = bnn.train(X_train, y_train, epochs=50, batch_size=64)
        
        # Test screening
        print("\n\nTesting candidate screening...")
        X_test, _ = generate_training_data(n_samples=10000)
        results = bnn.screen_candidates(X_test, top_k=10)
        
        if results:
            print(f"\nTop 10 candidates:")
            for i in range(min(10, len(results['top_indices']))):
                params = results['top_params'][i]
                cost = results['top_mean_cost'][i]
                unc = results['top_std_cost'][i]
                print(f"  {i+1}. a={params[0]:.1f}, e={params[1]:.3f}, cost={cost:.2f}±{unc:.2f}")
    else:
        print("\nTensorFlow not available - install with:")
        print("  pip install tensorflow tensorflow-probability")
