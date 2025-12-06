import numpy as np
from scipy.optimize import differential_evolution
import logging
from src.time_machine import TimeMachine
from src.historical_judge import HistoricalJudge

logging.basicConfig(level=logging.INFO, format='%(asctime)s - PRIMORDIAL - %(message)s')

class PrimordialOptimizer:
    """
    The Historical Solver: Find S_born that produces the modern solar system.
    
    Instead of optimizing P9's current position, we optimize its BIRTH STATE
    4.5 billion years ago, then simulate forward to validate against all 7 tiers.
    
    This is the "Arrow of Time Reversal" - we know the end, solve for the beginning.
    """
    
    def __init__(self, scenario='rogue_capture'):
        """
        Args:
            scenario: 'rogue_capture' or 'native_ejection'
        """
        self.scenario = scenario
        self.time_machine = TimeMachine()
        self.judge = HistoricalJudge()
        
        # Search bounds depend on scenario
        if scenario == 'rogue_capture':
            # Rogue planet approaching from Oort Cloud
            self.bounds = [
                (200, 1000),      # x0 (AU) - distance at capture
                (-50, 50),        # y0 (AU)
                (-50, 50),        # z0 (AU)
                (-2, 2),          # vx0 (AU/yr)
                (-2, 2),          # vy0 (AU/yr)
                (-5, -0.5),       # vz0 (AU/yr) - approaching
                (3e-5, 1e-4)      # mass (solar masses, ~10-30 Earth masses)
            ]
            logging.info("Scenario: ROGUE CAPTURE (from interstellar space)")
        else:
            # Native planet ejected by Jupiter
            self.bounds = [
                (10, 50),         # x0 (AU) - near Saturn
                (-10, 10),        # y0
                (-5, 5),          # z0
                (-5, 5),          # vx0 (fast ejection)
                (-5, 5),          # vy0
                (-5, 5),          # vz0
                (3e-5, 1e-4)      # mass
            ]
            logging.info("Scenario: NATIVE EJECTION (born near Saturn)")
    
    def objective_function(self, params):
        """
        The master evaluation function.
        
        1. Take initial state S_born = [x0, y0, z0, vx0, vy0, vz0, m]
        2. Run 4.5 Gyr forward integration
        3. Check if result matches modern solar system
        
        Args:
            params: [x0, y0, z0, vx0, vy0, vz0, m]
        
        Returns:
            float: Cost (historical likelihood)
        """
        x0, y0, z0, vx0, vy0, vz0, m = params
        
        # Convert to initial state dict
        initial_state = {
            'x': x0, 'y': y0, 'z': z0,
            'vx': vx0, 'vy': vy0, 'vz': vz0,
            'm': m
        }
        
        logging.info(f"\n=== Testing Birth State ===")
        logging.info(f"  Position: ({x0:.1f}, {y0:.1f}, {z0:.1f}) AU")
        logging.info(f"  Velocity: ({vx0:.2f}, {vy0:.2f}, {vz0:.2f}) AU/yr")
        logging.info(f"  Mass: {m:.2e} M_sun (~{m*333000:.0f} M_earth)")
        
        try:
            # Run the time machine
            result = self.time_machine.integrate_history(initial_state)
            
            if not result['hamiltonian_valid']:
                logging.error("  Physics violated during integration")
                return 1e10
            
            # Evaluate final state against modern solar system
            cost = self.judge.evaluate_history(
                result['sim_final'],
                result['p9_final_params'],
                hamiltonian_valid=True
            )
            
            logging.info(f"  Final Cost: {cost:.2f}")
            
            return cost
            
        except Exception as e:
            logging.error(f"  Integration failed: {e}")
            return 1e10
    
    def run(self, max_generations=50, population_size=15, workers=-1):
        """
        Search for the optimal birth state.
        
        Args:
            max_generations: DE iterations
            population_size: Number of parallel universes
            workers: CPU cores (-1 = all)
        
        Returns:
            dict: Best initial state found
        """
        logging.info("="*60)
        logging.info("PRIMORDIAL OPTIMIZER: Searching for Planet 9's Birth")
        logging.info(f"Scenario: {self.scenario}")
        logging.info(f"Generations: {max_generations}")
        logging.info(f"Population: {population_size}")
        logging.info("="*60)
        
        result = differential_evolution(
            self.objective_function,
            bounds=self.bounds,
            maxiter=max_generations,
            popsize=population_size,
            workers=workers,
            updating='deferred',  # Parallel mode
            disp=True,
            polish=False
        )
        
        # Reconstruct best solution
        x0, y0, z0, vx0, vy0, vz0, m = result.x
        
        best_state = {
            'x0': x0, 'y0': y0, 'z0': z0,
            'vx0': vx0, 'vy0': vy0, 'vz0': vz0,
            'm': m,
            'cost': result.fun,
            'scenario': self.scenario
        }
        
        logging.info("\n" + "="*60)
        logging.info("DISCOVERY: Optimal Birth State Found")
        logging.info("="*60)
        logging.info(f"  Initial Position: ({x0:.1f}, {y0:.1f}, {z0:.1f}) AU")
        logging.info(f"  Initial Velocity: ({vx0:.2f}, {vy0:.2f}, {vz0:.2f}) AU/yr")
        logging.info(f"  Mass: {m:.2e} M_sun ({m*333000:.0f} M_earth)")
        logging.info(f"  Final Cost: {result.fun:.2f}")
        logging.info("="*60)
        
        return best_state


if __name__ == "__main__":
    # Quick test (1 generation)
    print("Testing Primordial Optimizer (Demo Mode)\n")
    
    optimizer = PrimordialOptimizer(scenario='rogue_capture')
    
    # Single evaluation test
    test_params = [300, 0, 0, 0.5, 0, -1, 5e-5]
    cost = optimizer.objective_function(test_params)
    print(f"\nTest Cost: {cost:.2f}")
