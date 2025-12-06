import rebound
import numpy as np
import h5py
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class SimConfig:
    t_max: float = 1e5 * 2 * np.pi # 100k years (in radians, if G=1)
    dt: float = 0.01
    snapshot_interval: int = 100
    integrator: str = "whfast"
    energy_tolerance: float = 1e-9
    hdf5_path: str = "data/simulation.h5"

class EnergyMonitor:
    def __init__(self, sim: rebound.Simulation, tolerance: float):
        self.sim = sim
        self.tolerance = tolerance
        self.initial_energy = sim.calculate_energy()
        self.history = []

    def check(self) -> bool:
        current_energy = self.sim.calculate_energy()
        drift = abs((current_energy - self.initial_energy) / self.initial_energy)
        self.history.append(drift)
        return drift < self.tolerance

class HDF5Logger:
    def __init__(self, filepath: str, num_particles: int, estimated_steps: int):
        self.filepath = filepath
        self.num_particles = num_particles
        
        # Initialize HDF5 file
        with h5py.File(filepath, 'w') as f:
            f.create_dataset("time", (0,), maxshape=(None,), dtype='f8')
            f.create_dataset("energy_drift", (0,), maxshape=(None,), dtype='f8')
            # Shape: [Time, Particle, 3] for x,y,z
            f.create_dataset("positions", (0, num_particles, 3), maxshape=(None, num_particles, 3), dtype='f8')

    def log(self, time: float, drift: float, sim: rebound.Simulation):
        # Zero-Copy: Get pointers to particle data
        # REBOUND particles are structs. We can extract arrays.
        # For speed, we might iterate or use a helper if available.
        # sim.particles is iterable.
        
        pos = np.zeros((self.num_particles, 3))
        for i, p in enumerate(sim.particles):
            pos[i] = [p.x, p.y, p.z]

        with h5py.File(self.filepath, 'a') as f:
            # Resize datasets
            n = f["time"].shape[0]
            f["time"].resize((n + 1,))
            f["energy_drift"].resize((n + 1,))
            f["positions"].resize((n + 1, self.num_particles, 3))

            # Write data
            f["time"][n] = time
            f["energy_drift"][n] = drift
            f["positions"][n] = pos

class SimulationEngine:
    def __init__(self, config: SimConfig):
        self.config = config
        self.sim = rebound.Simulation()
        self.sim.integrator = config.integrator
        self.sim.dt = config.dt
        self.sim.units = ('AU', 'yr', 'Msun') # Standard units
        
        self.monitor: Optional[EnergyMonitor] = None
        self.logger: Optional[HDF5Logger] = None

    def setup_solar_system(self, planet9_params: Optional[Dict] = None):
        """
        Initialize Solar System.
        planet9_params: dict with 'a', 'e', 'inc', 'Omega', 'omega', 'm'
        """
        self.sim.add(m=1.0) # Sun
        self.sim.add("Jupiter")
        self.sim.add("Saturn")
        self.sim.add("Uranus")
        self.sim.add("Neptune")
        
        # Add some TNOs (Placeholder for NASA Ingest)
        # Sedna-like
        self.sim.add(a=500, e=0.85, inc=0.2, Omega=1.0, omega=0.5, m=0) 
        
        if planet9_params:
            self.sim.add(
                a=planet9_params.get('a', 400),
                e=planet9_params.get('e', 0.6),
                inc=planet9_params.get('inc', 0.35), # ~20 deg
                Omega=planet9_params.get('Omega', 0),
                omega=planet9_params.get('omega', 0),
                m=planet9_params.get('m', 5e-5) # ~10 Earth masses
            )

        self.sim.move_to_com() # Move to Center of Momentum
        
        self.monitor = EnergyMonitor(self.sim, self.config.energy_tolerance)
        
        # Estimate steps for logging (not strictly needed for resizeable HDF5 but good for prealloc if we wanted)
        self.logger = HDF5Logger(self.config.hdf5_path, len(self.sim.particles), 0)

    def run(self):
        """
        Main simulation loop.
        Returns: Final Cost (Energy Drift for now) or Infinity if crashed.
        """
        if not self.monitor or not self.logger:
            raise RuntimeError("Simulation not initialized. Call setup_solar_system first.")

        times = np.linspace(0, self.config.t_max, int(self.config.t_max / self.config.dt))
        step = 0
        
        print(f"Starting simulation: {len(self.sim.particles)} particles, {self.config.t_max:.1f} years.")
        
        start_time = time.time()
        
        for t in times:
            try:
                self.sim.integrate(t)
                
                if step % self.config.snapshot_interval == 0:
                    if not self.monitor.check():
                        print(f"CRITICAL: Energy drift violation at t={t:.1f}")
                        return float('inf') # Penalty for bad physics
                    
                    drift = self.monitor.history[-1]
                    self.logger.log(t, drift, self.sim)
                    
                    # Check for ejections (r > 5000 AU)
                    for p in self.sim.particles:
                        r = np.sqrt(p.x**2 + p.y**2 + p.z**2)
                        if r > 5000:
                            print(f"CRITICAL: Particle ejected at t={t:.1f}")
                            return float('inf')

            except rebound.Collision:
                print("Collision detected!")
                return float('inf')
            except Exception as e:
                print(f"Simulation Error: {e}")
                return float('inf')
            
            step += 1

        elapsed = time.time() - start_time
        print(f"Simulation finished in {elapsed:.2f}s. Final Drift: {self.monitor.history[-1]:.2e}")
        
        # Calculate Clustering Metric (Sigma Pi)
        # TNOs are particles 5 onwards (0=Sun, 1-4=Giants)
        tnos = self.sim.particles[5:]
        if not tnos:
            return float('inf')

        p_longitudes = []
        for p in tnos:
            # Calculate orbital elements
            orbit = p.calculate_orbit(primary=self.sim.particles[0])
            # Longitude of perihelion = Omega + omega
            varpi = orbit.Omega + orbit.omega
            p_longitudes.append(varpi)
        
        # Circular statistics for standard deviation
        angles = np.array(p_longitudes)
        # Mean vector
        sin_sum = np.sum(np.sin(angles))
        cos_sum = np.sum(np.cos(angles))
        R = np.sqrt(sin_sum**2 + cos_sum**2) / len(angles)
        sigma_varpi = np.sqrt(-2 * np.log(R)) if R < 1 else 0

        return {
            "cost": sigma_varpi,
            "drift": self.monitor.history[-1],
            "ejections": 0 # TODO: Track ejections
        }

if __name__ == "__main__":
    # Quick Test
    cfg = SimConfig(t_max=1000, dt=0.5) # Short run
    engine = SimulationEngine(cfg)
    engine.setup_solar_system(planet9_params={'a': 400, 'e': 0.6})
    cost = engine.run()
    print(f"Run Cost: {cost}")
