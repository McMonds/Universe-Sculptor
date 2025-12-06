import numpy as np
import rebound
import logging
from src.judge import Judge
from src.constraints import Constraints

logging.basicConfig(level=logging.INFO, format='%(asctime)s - HISTORICAL - %(message)s')

class HistoricalJudge:
    """
    Evaluates historical likelihood: P(Current Solar System | Initial Conditions)
    
    This is the "Situation" definition - the exact list of "Truths" that
    the simulated history must produce at T=now.
    """
    
    def __init__(self):
        self.judge = Judge()
        self.constraints = Constraints()
        
        # Target values (modern solar system)
        self.target_solar_tilt = 6.0  # degrees
        self.target_varpi_dispersion = 40.0  # degrees (max allowed clustering spread)
    
    def evaluate_solar_obliquity(self, sim):
        """
        Metric B: Solar obliquity (tilt of Sun's rotation axis).
        
        The Sun is tilted 6° relative to the invariable plane (total angular
        momentum vector of the solar system). Planet 9's torque over billions
        of years is thought to cause this.
        
        Args:
            sim: Final simulation state at T=now
        
        Returns:
            float: Cost (0 if exactly 6°, increases with deviation)
        """
        # Calculate invariable plane (total L vector)
        L_total = np.array([0.0, 0.0, 0.0])
        for p in sim.particles:
            r = np.array([p.x, p.y, p.z])
            v = np.array([p.vx, p.vy, p.vz])
            L_total += p.m * np.cross(r, v)
        
        L_hat = L_total / np.linalg.norm(L_total)
        
        # Sun's rotation axis (approximation: use z-axis)
        # In reality, we'd need to track Sun's rotation in REBOUND
        # For now, assume solar spin is close to z-axis
        solar_axis = np.array([0, 0, 1])
        
        # Angle between them
        cos_theta = np.dot(solar_axis, L_hat)
        tilt_deg = np.degrees(np.arccos(np.clip(cos_theta, -1, 1)))
        
        # Cost: deviation from 6°
        cost = abs(tilt_deg - self.target_solar_tilt)
        
        logging.info(f"  Solar Tilt: {tilt_deg:.2f}° (target: {self.target_solar_tilt}°)")
        
        return cost
    
    def evaluate_cold_classical_kb(self, sim):
        """
        Metric D: Cold Classical Kuiper Belt survival.
        
        The "Cold Classical" KB (circular orbits at 42-47 AU) is pristine.
        Planet 9 must NOT have destroyed it. Check that particles in this
        region remain stable.
        
        Args:
            sim: Final simulation state
        
        Returns:
            float: Penalty if Cold Classical KB is disrupted
        """
        # Count particles in Cold Classical region
        cold_classical_count = 0
        disrupted_count = 0
        
        for p in sim.particles[6:]:  # Skip Sun, Giants, P9
            try:
                orbit = p.calculate_orbit(primary=sim.particles[0])
                a = orbit.a
                e = orbit.e
                
                # Cold Classical: 42 < a < 47 AU, e < 0.1
                if 42 < a < 47:
                    if e < 0.1:
                        cold_classical_count += 1
                    else:
                        disrupted_count += 1
            except:
                pass
        
        # Penalty if we lost too many
        survival_rate = cold_classical_count / max(1, cold_classical_count + disrupted_count)
        
        penalty = 0
        if survival_rate < 0.5:
            penalty = 100 * (0.5 - survival_rate)
            logging.warning(f"  Cold Classical KB: Only {survival_rate:.1%} survived")
        else:
            logging.info(f"  Cold Classical KB: {survival_rate:.1%} intact ✓")
        
        return penalty
    
    def evaluate_high_inclination_production(self, sim):
        """
        Metric C (Bonus): High-inclination centaurs (Niku-like).
        
        The simulation should naturally produce objects with i > 60°.
        This is NOT a hard constraint but a "bonus" - if it happens, it's
        strong evidence the P9 candidate is correct.
        
        Returns:
            float: Bonus score (negative cost) if high-inc objects exist
        """
        high_inc_count = 0
        
        for p in sim.particles[6:]:
            try:
                orbit = p.calculate_orbit(primary=sim.particles[0])
                inc_deg = np.degrees(orbit.inc)
                
                if inc_deg > 60:
                    high_inc_count += 1
                    logging.info(f"    High-inc object: i={inc_deg:.1f}°")
            except:
                pass
        
        # Bonus: -10 per high-inc object (up to -50)
        bonus = -min(50, high_inc_count * 10)
        
        if bonus < 0:
            logging.info(f"  High-Inc Production: {high_inc_count} objects (bonus: {bonus})")
        
        return bonus
    
    def evaluate_history(self, sim_final, p9_params, hamiltonian_valid=True):
        """
        The master likelihood function.
        
        L = P(Current Solar System | S_born)
        
        Args:
            sim_final: Simulation state at T=now
            p9_params: Planet 9 parameters
            hamiltonian_valid: Did the Hamiltonian stay conserved?
        
        Returns:
            float: Total cost (lower = better match to reality)
        """
        if not hamiltonian_valid:
            logging.error("  ✗ Hamiltonian violated - INVALID HISTORY")
            return float('inf')
        
        if sim_final is None:
            return float('inf')
        
        logging.info("Evaluating Historical Likelihood:")
        
        total_cost = 0
        
        # Metric A: TNO Clustering (standard Judge)
        clustering_cost = self.judge.evaluate(sim_final, p9_params)
        logging.info(f"  Metric A (TNO Clustering): {clustering_cost:.2f}")
        total_cost += clustering_cost
        
        # Metric B: Solar Obliquity
        tilt_cost = self.evaluate_solar_obliquity(sim_final)
        logging.info(f"  Metric B (Solar Tilt): {tilt_cost:.2f}")
        total_cost += tilt_cost
        
        # Metric D: Cold Classical KB Survival
        kb_cost = self.evaluate_cold_classical_kb(sim_final)
        logging.info(f"  Metric D (Cold KB): {kb_cost:.2f}")
        total_cost += kb_cost
        
        # Metric C: High-Inclination Bonus
        bonus = self.evaluate_high_inclination_production(sim_final)
        total_cost += bonus
        
        logging.info(f"✓ Total Historical Likelihood: {total_cost:.2f}")
        
        return total_cost


if __name__ == "__main__":
    # Test: Mock simulation
    print("=== Testing Historical Judge ===\n")
    
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    
    # Add Sun + Giants
    sim.add(m=1.0)
    sim.add(m=9.5458e-4, a=5.2, e=0.048)  # Jupiter
    sim.add(m=2.8588e-4, a=9.58, e=0.056) # Saturn
    sim.add(m=4.366e-5, a=19.22, e=0.046) # Uranus
    sim.add(m=5.151e-5, a=30.11, e=0.009) # Neptune
    
    # Add mock Planet 9
    sim.add(m=5e-5, a=450, e=0.65, inc=np.radians(30))
    
    # Add mock eTNOs
    for i in range(5):
        sim.add(m=0, a=200 + i*50, e=0.7, inc=np.radians(20), Omega=np.radians(100))
    
    sim.move_to_com()
    
    # Evaluate
    judge = HistoricalJudge()
    p9_params = {'a': 450, 'e': 0.65, 'inc': np.radians(30), 'm': 5e-5, 'Omega': 0, 'omega': 0}
    
    cost = judge.evaluate_history(sim, p9_params, hamiltonian_valid=True)
    print(f"\nFinal Historical Cost: {cost:.2f}")
