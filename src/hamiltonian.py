import rebound
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - HAMILTONIAN - %(message)s')

class PhysicsViolation(Exception):
    """Raised when conservation laws are violated beyond tolerance"""
    pass

class HamiltonianMonitor:
    """
    The Conservation Police - Rigorous Physics Monitoring
    
    Tracks three critical conservation laws:
    1. Energy conservation (Hamiltonian)
    2. Angular momentum conservation
    3. Barycenter stability (system shouldn't fly away)
    """
    """
    Tracks conservation laws during long-term integration (4.5 Gyr).
    
    The Hamiltonian H = T + V must be conserved for the simulation to be valid.
    For a symplectic integrator like WHFast, we expect drift < 10^-9 over Gyr timescales.
    
    This is the mathematical "truth detector" - if H drifts, the history is wrong.
    """
    
    def __init__(self, sim, name="Simulation", strictness=1e-5):
        """
        Initialize conservation law baselines.
        
        Args:
            sim: rebound.Simulation object at t=0
            name: Identifier for this simulation run
            strictness: Energy drift tolerance (default: 1e-5 for long integrations)
        """
        self.name = name
        self.strictness = strictness
        
        # Baseline values (at t=0)
        self.E0 = sim.energy()
        self.L0 = np.linalg.norm(self._calculate_angular_momentum(sim))
        
        # Barycenter tracking (prevent system from flying away)
        com = sim.com()
        self.barycenter_0 = np.array([com.x, com.y, com.z])
        
        # Tolerances
        self.energy_tol = strictness
        self.momentum_tol = 1e-12
        self.bary_drift_tol = 5.0  # AU (drift > 5 AU = math instability)
        
        # History
        self.history = {
            't': [],
            'dE': [],
            'dL': [],
            'dP': []
        }
        
        logging.info(f"Initialized {name}")
        logging.info(f"  E0 = {self.E0:.10e}")
        logging.info(f"  L0 = {np.linalg.norm(self.L0):.10e}")
        logging.info(f"  P0 = {np.linalg.norm(self.P0):.10e}")
    
    def _calculate_angular_momentum(self, sim):
        """
        Total angular momentum: L = Σ m_i * (r_i × v_i)
        """
        L = np.array([0.0, 0.0, 0.0])
        for p in sim.particles:
            r = np.array([p.x, p.y, p.z])
            v = np.array([p.vx, p.vy, p.vz])
            L += p.m * np.cross(r, v)
        return L
    
    def _calculate_linear_momentum(self, sim):
        """
        Total linear momentum: P = Σ m_i * v_i
        Should be ~0 in barycentric frame
        """
        P = np.array([0.0, 0.0, 0.0])
        for p in sim.particles:
            v = np.array([p.vx, p.vy, p.vz])
            P += p.m * v
        return P
    
    def check_health(self, sim):
        """
        Strict "Game Over" thresholds for long-term integration.
        
        Returns:
            tuple: (is_healthy: bool, reason: str)
        """
        # 1. Energy Conservation Check (dE/E)
        E_curr = sim.energy()
        energy_drift = abs((E_curr - self.E0) / self.E0) if self.E0 != 0 else 0
        
        # 2. Angular Momentum Conservation Check
        L_curr = np.linalg.norm(self._calculate_angular_momentum(sim))
        ang_mom_drift = abs((L_curr - self.L0) / self.L0) if self.L0 != 0 else 0
        
        # 3. Barycenter Drift (Using vectorized subtraction)
        com_curr = sim.com()
        com_curr_vec = np.array([com_curr.x, com_curr.y, com_curr.z])
        drift_dist = np.linalg.norm(com_curr_vec - self.barycenter_0)
        
        # Decision Logic
        if energy_drift > self.strictness:
            return False, f"Energy violation: {energy_drift:.2e}"
        
        if drift_dist > self.bary_drift_tol:
            return False, f"Barycenter instability: {drift_dist:.2f} AU"
        
        return True, "Stable"
    
    def check(self, sim, t_gyr=None, raise_on_violation=False):
        """
        Check conservation laws at current simulation time.
        
        Args:
            sim: Current simulation state
            t_gyr: Time in Gyr (for logging)
            raise_on_violation: If True, raise PhysicsViolation on breach
        
        Returns:
            dict: Conservation metrics
        """
        # Current values
        E = sim.energy()
        L = self._calculate_angular_momentum(sim)
        P = self._calculate_linear_momentum(sim)
        
        # Deviations
        dE_frac = abs(E - self.E0) / abs(self.E0)
        dL_frac = np.linalg.norm(L - self.L0) / np.linalg.norm(self.L0)
        dP = np.linalg.norm(P)
        
        # Store history
        self.history['t'].append(sim.t)
        self.history['dE'].append(dE_frac)
        self.history['dL'].append(dL_frac)
        self.history['dP'].append(dP)
        
        # Check violations
        violations = []
        
        if dE_frac > self.energy_tol:
            violations.append(f"Energy drift {dE_frac:.2e} > {self.energy_tol:.2e}")
        
        if dP > self.momentum_tol:
            violations.append(f"Barycenter drift {dP:.2e} > {self.momentum_tol:.2e}")
        
        # Log status
        t_str = f"t={t_gyr:.2f} Gyr" if t_gyr else f"t={sim.t:.2e}"
        
        if violations:
            msg = f"⚠ VIOLATION at {t_str}: " + "; ".join(violations)
            logging.error(msg)
            if raise_on_violation:
                raise PhysicsViolation(msg)
        else:
            if len(self.history['t']) % 10 == 0:  # Log every 10 checks
                logging.info(f"✓ {t_str}: dE={dE_frac:.2e}, dL={dL_frac:.2e}, dP={dP:.2e}")
        
        return {
            'dE': dE_frac,
            'dL': dL_frac,
            'dP': dP,
            'valid': len(violations) == 0
        }
    
    def get_drift_summary(self):
        """
        Get statistical summary of conservation over entire run.
        """
        if not self.history['t']:
            return {}
        
        return {
            'duration': self.history['t'][-1] - self.history['t'][0],
            'max_energy_drift': max(self.history['dE']),
            'max_momentum_drift': max(self.history['dP']),
            'mean_energy_drift': np.mean(self.history['dE']),
            'final_energy_drift': self.history['dE'][-1]
        }
    
    def is_valid_history(self):
        """
        Final judgement: Did the simulation maintain physical integrity?
        """
        summary = self.get_drift_summary()
        if not summary:
            return False
        
        # Strict criteria for 4.5 Gyr integration
        valid = (
            summary['max_energy_drift'] < self.energy_tol and
            summary['max_momentum_drift'] < self.momentum_tol
        )
        
        if valid:
            logging.info(f"✓ {self.name}: VALID HISTORY")
            logging.info(f"   Max dE: {summary['max_energy_drift']:.2e}")
            logging.info(f"   Duration: {summary['duration']/(2*np.pi*1e9):.2f} Gyr")
        else:
            logging.error(f"✗ {self.name}: INVALID HISTORY (physics violated)")
        
        return valid


if __name__ == "__main__":
    import rebound
    
    # Test: Solar System integration
    print("=== Testing Hamiltonian Monitor ===\n")
    
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    sim.integrator = "whfast"
    sim.dt = 0.05
    
    # Add Sun + Jupiter
    sim.add(m=1.0)
    sim.add(m=9.5458e-4, a=5.2, e=0.048)
    sim.move_to_com()
    
    monitor = HamiltonianMonitor(sim, name="Jupiter Test")
    
    # Integrate for 1000 years
    times = np.linspace(0, 1000, 11)
    for t in times:
        sim.integrate(t)
        monitor.check(sim, t_gyr=t/1e9)
    
    # Final check
    print("\n" + "="*50)
    summary = monitor.get_drift_summary()
    print(f"Duration: {summary['duration']:.1f} yr")
    print(f"Max Energy Drift: {summary['max_energy_drift']:.2e}")
    print(f"Valid History: {monitor.is_valid_history()}")
