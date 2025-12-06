import numpy as np
import rebound
import h5py
import os
import logging
from src.oracle import Oracle
from src.hamiltonian import HamiltonianMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - TIMEMACHINE - %(message)s')

class TimeMachine:
    """
    The 4.5 Billion Year Integrator.
    
    Integrates from T=-4.5 Gyr (birth) to T=0 (now), tracking:
    - Planet 9's orbital migration
    - Conservation laws (Hamiltonian)
    - Snapshots at key epochs
    
    This is the "Great Filter" - most initial conditions will fail.
    Only histories that maintain physics AND produce the modern solar system pass.
    """
    
    def __init__(self, save_snapshots=True, snapshot_dir='data/snapshots'):
        """
        Args:
            save_snapshots: Save HDF5 snapshots at checkpoints
            snapshot_dir: Directory for snapshot files
        """
        self.save_snapshots = save_snapshots
        self.snapshot_dir = snapshot_dir
        self.oracle = Oracle()
        
        if save_snapshots:
            os.makedirs(snapshot_dir, exist_ok=True)
        
        # Checkpoint times (in years, converted to REBOUND units)
        # We simulate FORWARD from t=0 (birth) to t=4.5 Gyr
        self.checkpoints = [
            0,              # Birth
            1e9,            # 1 Gyr - Early chaos
            2e9,            # 2 Gyr - Sedna sculpting
            3e9,            # 3 Gyr - Niku flips
            4.5e9           # Now
        ]
        
        # Convert to REBOUND units (2π years)
        self.checkpoints_rebound = [t * 2 * np.pi for t in self.checkpoints]
    
    def setup_initial_simulation(self, p9_initial_state):
        """
        Create simulation at T=-4.5 Gyr (birth of Planet 9).
        
        Args:
            p9_initial_state: dict with x, y, z, vx, vy, vz, m
        
        Returns:
            rebound.Simulation
        """
        sim = rebound.Simulation()
        sim.units = ('AU', 'yr', 'Msun')
        sim.integrator = "whfast"
        sim.dt = 0.1  # Larger timestep for long integration
        
        # Add Sun (primordial, same mass)
        sim.add(m=1.0)
        
        # Add Giants (assume they were already formed and stable)
        # Using current orbits as approximation (migration is slow)
        giant_data = self.oracle.fetch_data()
        for obj in giant_data:
            if obj['is_planet'] and obj['name'] != 'Sun':
                sim.add(
                    m={'Jupiter': 9.5458e-4, 'Saturn': 2.8588e-4,
                       'Uranus': 4.366e-5, 'Neptune': 5.151e-5}.get(obj['name'], 0),
                    x=obj['x'], y=obj['y'], z=obj['z'],
                    vx=obj['vx'], vy=obj['vy'], vz=obj['vz']
                )
        
        # Add Planet 9 at BIRTH state
        sim.add(
            m=p9_initial_state['m'],
            x=p9_initial_state['x'],
            y=p9_initial_state['y'],
            z=p9_initial_state['z'],
            vx=p9_initial_state['vx'],
            vy=p9_initial_state['vy'],
            vz=p9_initial_state['vz']
        )
        
        # Add eTNOs (primordial disk)
        # For simplicity, use current eTNO orbits as "seed population"
        # In reality, these evolve significantly
        for obj in giant_data:
            if not obj['is_planet']:
                # Use orbital elements if available
                if 'a' in obj:
                    sim.add(
                        m=0,
                        a=obj['a'], e=obj['e'], inc=obj['inc'],
                        Omega=obj['Omega'], omega=obj['omega'], M=obj['M']
                    )
        
        sim.move_to_com()
        
        logging.info(f"Initialized at T=-4.5 Gyr with {sim.N} particles")
        
        return sim
    
    def track_p9_migration(self, sim, p9_index=5):
        """
        Record Planet 9's orbital elements for migration tracking.
        
        Args:
            sim: Current simulation
            p9_index: Index of Planet 9 (usually 5: Sun + 4 Giants)
        
        Returns:
            dict: Orbital elements
        """
        try:
            orbit = sim.particles[p9_index].calculate_orbit(primary=sim.particles[0])
            return {
                't': sim.t / (2 * np.pi),  # Convert to years
                'a': orbit.a,
                'e': orbit.e,
                'inc': orbit.inc,
                'Omega': orbit.Omega,
                'omega': orbit.omega
            }
        except:
            return None
    
    def save_snapshot(self, sim, epoch_name, migration_history):
        """
        Save simulation snapshot to HDF5.
        
        Args:
            sim: Current simulation
            epoch_name: e.g., "1Gyr", "4.5Gyr"
            migration_history: List of migration data points
        """
        if not self.save_snapshots:
            return
        
        filename = os.path.join(self.snapshot_dir, f"snapshot_{epoch_name}.h5")
        
        with h5py.File(filename, 'w') as f:
            # Metadata
            f.attrs['epoch'] = epoch_name
            f.attrs['time_years'] = sim.t / (2 * np.pi)
            f.attrs['N_particles'] = sim.N
            
            # Particle data
            positions = []
            velocities = []
            masses = []
            
            for p in sim.particles:
                positions.append([p.x, p.y, p.z])
                velocities.append([p.vx, p.vy, p.vz])
                masses.append(p.m)
            
            f.create_dataset('positions', data=np.array(positions))
            f.create_dataset('velocities', data=np.array(velocities))
            f.create_dataset('masses', data=np.array(masses))
            
            # Migration history
            if migration_history:
                mig_group = f.create_group('migration')
                mig_group.create_dataset('time', data=[m['t'] for m in migration_history if m])
                mig_group.create_dataset('a', data=[m['a'] for m in migration_history if m])
                mig_group.create_dataset('e', data=[m['e'] for m in migration_history if m])
        
        logging.info(f"  Saved snapshot: {filename}")
    
    def integrate_history(self, p9_initial_state):
        """
        THE TIME MACHINE: Integrate 4.5 Gyr forward.
        
        Args:
            p9_initial_state: Birth state of Planet 9
        
        Returns:
            dict: {
                'sim_final': Final simulation at T=now,
                'hamiltonian_valid': Bool,
                'migration_history': List of orbital evolution,
                'p9_final_params': Final P9 parameters
            }
        """
        logging.info("="*60)
        logging.info("STARTING TIME MACHINE: T=-4.5 Gyr → T=now")
        logging.info("="*60)
        
        # Setup
        sim = self.setup_initial_simulation(p9_initial_state)
        monitor = HamiltonianMonitor(sim, name="4.5 Gyr History")
        
        migration_history = []
        
        # Integrate through checkpoints
        for i, checkpoint in enumerate(self.checkpoints_rebound):
            epoch_gyr = self.checkpoints[i] / 1e9
            logging.info(f"\n→ Integrating to T={epoch_gyr:.1f} Gyr...")
            
            try:
                sim.integrate(checkpoint)
                
                # Check conservation
                check = monitor.check(sim, t_gyr=epoch_gyr)
                
                # Track migration
                migration = self.track_p9_migration(sim)
                migration_history.append(migration)
                
                if migration:
                    logging.info(f"  P9 orbit: a={migration['a']:.1f} AU, e={migration['e']:.3f}")
                
                # Save snapshot
                self.save_snapshot(sim, f"{epoch_gyr:.1f}Gyr", migration_history)
                
                if not check['valid']:
                    logging.error("  Physics violated - aborting")
                    return {
                        'sim_final': None,
                        'hamiltonian_valid': False,
                        'migration_history': migration_history,
                        'p9_final_params': None
                    }
                
            except rebound.Collision:
                logging.error("  Collision detected - aborting")
                return {
                    'sim_final': None,
                    'hamiltonian_valid': False,
                    'migration_history': migration_history,
                    'p9_final_params': None
                }
        
        # Final check
        is_valid = monitor.is_valid_history()
        
        # Extract final P9 params
        final_migration = migration_history[-1]
        p9_final = {
            'a': final_migration['a'],
            'e': final_migration['e'],
            'inc': final_migration['inc'],
            'Omega': final_migration['Omega'],
            'omega': final_migration['omega'],
            'm': p9_initial_state['m']
        } if final_migration else None
        
        logging.info("\n" + "="*60)
        logging.info(f"TIME MACHINE COMPLETE: {is_valid and 'SUCCESS' or 'FAILED'}")
        logging.info("="*60)
        
        return {
            'sim_final': sim,
            'hamiltonian_valid': is_valid,
            'migration_history': migration_history,
            'p9_final_params': p9_final
        }


if __name__ == "__main__":
    # Quick test: 100 year integration
    print("=== Testing Time Machine (Short Demo) ===\n")
    
    tm = TimeMachine(save_snapshots=True)
    
    # Test with a simple birth state
    test_state = {
        'x': 300.0, 'y': 0.0, 'z': 0.0,
        'vx': 0.5, 'vy': -1.0, 'vz': 0.0,
        'm': 5e-5
    }
    
    # Override checkpoints for quick test
    tm.checkpoints = [0, 50, 100]  # years
    tm.checkpoints_rebound = [t * 2 * np.pi for t in tm.checkpoints]
    
    result = tm.integrate_history(test_state)
    
    print(f"\nResult:")
    print(f"  Valid: {result['hamiltonian_valid']}")
    print(f"  Migration points: {len(result['migration_history'])}")
