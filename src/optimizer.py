import numpy as np
from scipy.optimize import differential_evolution, minimize
from src.worker import Worker
from src.judge import Judge
import logging
import multiprocessing

# Setup Logging
logging.basicConfig(filename='logs/optimizer.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Global Worker for Multiprocessing (must be picklable)
# We initialize it once per process if possible, but for simplicity we instantiate inside.
def evaluate_universe(params):
    """
    Worker function for Parallel Execution.
    params: [a, e, inc, Omega, omega, m]
    """
    # Map params to dict
    p9_params = {
        'a': params[0],
        'e': params[1],
        'inc': params[2],
        'Omega': params[3],
        'omega': params[4],
        'm': params[5]
    }
    
    # Determine precision based on context (passed via global? or just default)
    # For Differential Evolution, we use 'low' precision (shorter time)
    t_max = 1e4 # 10k years for Scout
    
    worker = Worker(t_max=t_max)
    sim = worker.run(p9_params)
    cost = Judge.evaluate(sim, p9_params)
    
    return cost

class Optimizer:
    def __init__(self):
        self.best_params = None
        self.best_cost = float('inf')

    def run_stage_1_scout(self):
        print(f"=== Stage 1: The Rough Scout (Parallel Genetic Algorithm) ===")
        print(f"Using {multiprocessing.cpu_count()} Cores.")
        
        # Bounds: a=[200, 800], e=[0, 0.9], inc=[0, 1], Omega=[0, 2pi], omega=[0, 2pi], m=[1e-6, 1e-4]
        bounds = [
            (200, 800), (0.1, 0.9), (0, 1.0), 
            (0, 2*np.pi), (0, 2*np.pi), (1e-6, 1e-4)
        ]
        
        # Differential Evolution with Parallel Workers
        result = differential_evolution(
            evaluate_universe,
            bounds,
            strategy='best1bin',
            maxiter=10,
            popsize=15, # Larger population for parallel
            workers=-1, # Use all cores!
            disp=True,
            polish=False
        )
        
        self.best_params = result.x
        self.best_cost = result.fun
        print(f"Stage 1 Best: {self.best_params} (Cost: {self.best_cost})")
        logging.info(f"Stage 1 Complete. Best: {self.best_params}")

    def run_stage_2_sharpshooter(self):
        print("=== Stage 2: The Tactical Sharpshooter (Nelder-Mead) ===")
        # Nelder-Mead is sequential, but we can run the simulation longer (higher precision)
        
        # We need a wrapper that uses higher precision
        def evaluate_high_precision(params):
            p9_params = {
                'a': params[0], 'e': params[1], 'inc': params[2],
                'Omega': params[3], 'omega': params[4], 'm': params[5]
            }
            worker = Worker(t_max=5e4) # 50k years
            sim = worker.run(p9_params)
            cost = Judge.evaluate(sim, p9_params)
            logging.info(f"Stage 2 Eval: {cost}")
            return cost

        result = minimize(
            evaluate_high_precision,
            self.best_params,
            method='Nelder-Mead',
            options={'maxiter': 50, 'disp': True}
        )
        self.best_params = result.x
        print(f"Stage 2 Best: {self.best_params}")

if __name__ == "__main__":
    opt = Optimizer()
    opt.run_stage_1_scout()
    opt.run_stage_2_sharpshooter()

