import numpy as np
import rebound
from src.constraints import Constraints

class Judge:
    """
    The Judge: Cost Function Evaluator.
    Metric: Standard Deviation of Longitude of Perihelion.
    Constraints: Cassini, Optical, Infrared.
    """
    @staticmethod
    def evaluate(sim: rebound.Simulation, p9_params: dict = None) -> float:
        """
        Returns the Cost (lower is better).
        Cost = Sigma_varpi + Penalties
        """
        if sim is None:
            return float('inf') # Collision or failure

        # 1. Check Constraints (Veto Power)
        constraints = Constraints()
        penalty = 0.0
        if p9_params:
            penalty = constraints.get_penalty(p9_params)
            if penalty > 1e5:
                return penalty # Early rejection

        # Particles: Sun + 4 Giants (indices 0-4) + 4 eTNOs (indices 5-8) + Planet 9 (index 9)
        # Actually: The order in Worker is: Sun, Jupiter, Saturn, Uranus, Neptune, Sedna, Biden, Goblin, 2004VN112, Planet9
        # So TNOs are at indices 5-8, Planet 9 is at index 9
        
        # Count particles
        n_particles = sim.N
        if n_particles < 7:  # Need at least Sun + Giants + 1 eTNO + P9
            return float('inf')
        
        # TNOs are the test particles (m=0) that are NOT Planet 9
        # Planet 9 is the LAST particle
        tnos = sim.particles[5:n_particles-1]  # Everything after Giants,  before Planet 9
        
        if len(tnos) == 0:
            return float('inf')

        longitudes = []
        valid_count = 0
        
        for i, p in enumerate(tnos):
            try:
                # Check for ejection (a > 2000 AU or unbound)
                orbit = p.calculate_orbit(primary=sim.particles[0])
                if orbit.a > 2000 or orbit.e >= 1:
                    continue # Ejected / Unbound
                
                # Longitude of Perihelion (varpi) = Omega + omega
                varpi = orbit.Omega + orbit.omega
                longitudes.append(varpi)
                valid_count += 1
            except Exception as e:
                # Skip particles that fail orbit calculation
                continue

        if valid_count < 3:
            return 1000.0 # Not enough data to cluster

        # User-Specified Metric: Minimize Standard Deviation of Perihelions
        angles = np.array(longitudes)
        sin_sum = np.sum(np.sin(angles))
        cos_sum = np.sum(np.cos(angles))
        R = np.sqrt(sin_sum**2 + cos_sum**2) / valid_count
        
        # Circular Standard Deviation
        sigma = np.sqrt(-2 * np.log(R)) if R < 1 else 0
        
        return sigma + penalty

if __name__ == "__main__":
    # Mock Simulation
    sim = rebound.Simulation()
    sim.add(m=1)
    sim.add(a=100, e=0.1) # P1
    sim.add(a=100, e=0.1, Omega=0.1) # P2 (Clustered)
    sim.add(a=100, e=0.1, Omega=0.2) # P3 (Clustered)
    
    score = Judge.evaluate(sim)
    print(f"Clustering Score: {score}")
