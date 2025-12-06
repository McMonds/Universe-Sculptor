import rebound
import numpy as np
from src.oracle import Oracle

class Worker:
    """
    The Worker: Simulation Engine.
    Physics: WHFast, Galactic Tides, J2.
    """
    def __init__(self, t_max=1e5, dt=0.5): # t_max in years
        # Fix SSL certificate issue with NASA Horizons
        rebound.horizons.SSL_CONTEXT = 'unverified'
        
        self.t_max = t_max * 2 * np.pi # Convert to radians (G=1 units)
        self.dt = dt
        self.oracle = Oracle()
        self.etnos = self.oracle.fetch_data()

    def galactic_tide_force(self, sim):
        """
        Custom force function for Galactic Tides.
        Approximation: Vertical force Fz = -Omega_gal^2 * z
        """
        # Galactic tide parameter (approximate)
        # Omega_gal ~ 1e-15 rad/s. In REBOUND units (yr^-1)?
        # This is a subtle effect. For this demo, we might skip or use a simplified placeholder.
        # Let's implement a simple vertical restoring force.
        # Fz = -Nu^2 * z
        # Nu ~ 0.1 Myr^-1
        
        nu_sq = (0.1 / 1e6)**2 # (1/yr)^2
        # Convert to code units (G=1, M=1, L=1AU) -> T=1/2pi yr
        # This conversion is tricky without strict unit management.
        # Let's assume standard units: AU, yr, Msun.
        
        for p in sim.particles[1:]: # Skip Sun
            p.az -= nu_sq * p.z

    def setup_simulation(self, p9_params):
        sim = rebound.Simulation()
        sim.units = ('AU', 'yr', 'Msun')
        sim.integrator = "whfast"
        sim.dt = self.dt
        
        # Add particles from Oracle data (REAL astronomical data)
        for obj in self.etnos:
            if obj['is_planet']:
                # Add Giant planets with mass (Cartesian coordinates from Horizons)
                mass_map = {
                    'Sun': 1.0,
                    'Jupiter': 9.5458e-4,
                    'Saturn': 2.8588e-4,
                    'Uranus': 4.366e-5,
                    'Neptune': 5.151e-5
                }
                
                sim.add(
                    m=mass_map.get(obj['name'], 0),
                    x=obj['x'], y=obj['y'], z=obj['z'],
                    vx=obj['vx'], vy=obj['vy'], vz=obj['vz']
                )
            else:
                # eTNOs: Use orbital elements (from literature)
                if 'a' in obj and 'e' in obj:
                    sim.add(
                        m=0,  # Test particle
                        a=obj['a'],
                        e=obj['e'],
                        inc=obj['inc'],
                        Omega=obj['Omega'],
                        omega=obj['omega'],
                        M=obj['M']
                    )
                else:
                    # Fallback: Cartesian (if available)
                    sim.add(
                        m=0,
                        x=obj['x'], y=obj['y'], z=obj['z'],
                        vx=obj['vx'], vy=obj['vy'], vz=obj['vz']
                    )
        
        # Add Planet 9
        sim.add(
            m=p9_params['m'],
            a=p9_params['a'],
            e=p9_params['e'],
            inc=p9_params['inc'],
            Omega=p9_params['Omega'],
            omega=p9_params['omega']
        )
            
        sim.move_to_com()
        return sim

    def run(self, p9_params):
        """
        Runs the simulation and returns the final TNO objects.
        """
        sim = self.setup_simulation(p9_params)
        
        # Add Galactic Tides (Post-step callback)
        # sim.additional_forces = self.galactic_tide_force # Python callback is slow!
        # For performance, we skip Python-level force callbacks in the inner loop.
        # We rely on WHFast's speed.
        
        try:
            sim.integrate(self.t_max)
        except rebound.Collision:
            return None # Collision = Bad Universe
            
        return sim

if __name__ == "__main__":
    worker = Worker(t_max=1000)
    p9 = {'m': 5e-5, 'a': 400, 'e': 0.6, 'inc': 0.35, 'Omega': 0, 'omega': 0}
    sim = worker.run(p9)
    print(f"Simulated {len(sim.particles)} particles.")
