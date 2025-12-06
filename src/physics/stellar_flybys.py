"""
Stochastic Stellar Flybys Module
Category A2: Galactic Environment [HIGH]

Stars pass near the solar system randomly, perturbing outer objects.
Typical flyby: ~1 every 100 million years within 50,000 AU.

Implements Monte Carlo stellar encounters based on local stellar density.

Reference: Rickman et al. (2008) "Stellar perturbations on the scattered disk"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - FLYBYS - %(message)s')

class StellarFlybys:
    """
    Models random stellar encounters with the solar system.
    
    Uses Monte Carlo to inject impulse kicks at random times.
    """
    
    def __init__(self, enabled=True, encounter_rate=1e-8):
        """
        Args:
            enabled: Enable stellar flybys
            encounter_rate: Encounters per year (default: ~1 per 100 Myr)
        """
        self.enabled = enabled
        self.encounter_rate = encounter_rate  # yr^-1
        
        # Stellar properties (typical solar neighborhood)
        self.typical_mass = 0.5  # M_sun (average star mass)
        self.typical_velocity = 30  # km/s relative
        self.min_distance = 10000  # AU (close approach)
        self.max_distance = 100000  # AU
        
        # Track encounters
        self.encounters = []
        self.total_encounters = 0
        
        logging.info(f"Stellar Flybys: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Encounter rate: {1/encounter_rate/1e6:.1f} Myr per encounter")
            logging.info(f"  Typical mass: {self.typical_mass} M_sun")
            logging.info(f"  Typical velocity: {self.typical_velocity} km/s")
    
    def generate_encounter(self, t_current_years):
        """
        Generate parameters for a random stellar encounter.
        
        Args:
            t_current_years: Current simulation time (years)
        
        Returns:
            dict: Encounter parameters
        """
        # Stellar mass (IMF distribution - simplified)
        # Most stars are M-dwarfs (0.1-0.5 M_sun)
        mass = np.random.lognormal(np.log(0.3), 0.5)
        mass = np.clip(mass, 0.08, 2.0)  # M-dwarf to A-star range
        
        # Impact parameter (distance of closest approach)
        b = np.random.uniform(self.min_distance, self.max_distance)
        
        # Velocity (Maxwell-Boltzmann)
        v_km_s = np.random.normal(self.typical_velocity, 10)
        v_au_yr = v_km_s * (365.25 * 86400 / 1.496e8)  # Convert to AU/yr
        
        # Random direction (unit vector)
        phi = np.random.uniform(0, 2*np.pi)
        theta = np.arccos(np.random.uniform(-1, 1))
        
        direction = np.array([
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta)
        ])
        
        encounter = {
            'time': t_current_years,
            'mass': mass,
            'impact_parameter': b,
            'velocity': v_au_yr,
            'direction': direction
        }
        
        self.encounters.append(encounter)
        self.total_encounters += 1
        
        logging.info(f"Encounter #{self.total_encounters}:")
        logging.info(f"  T = {t_current_years/1e6:.1f} Myr")
        logging.info(f"  M_star = {mass:.2f} M_sun")
        logging.info(f"  b = {b:.0f} AU")
        logging.info(f"  v = {v_km_s:.1f} km/s")
        
        return encounter
    
    def calculate_impulse(self, particle_pos, encounter):
        """
        Calculate velocity kick from stellar encounter.
        
        Uses impulse approximation (rapid flyby).
        
        Args:
            particle_pos: [x, y, z] position of particle (AU)
            encounter: Encounter parameters dict
        
        Returns:
            array: [dvx, dvy, dvz] velocity kick (AU/yr)
        """
        # Stellar position at closest approach
        b = encounter['impact_parameter']
        direction = encounter['direction']
        star_pos = b * direction
        
        # Relative position
        r_vec = particle_pos - star_pos
        r = np.linalg.norm(r_vec)
        
        if r < 1:  # Too close, skip
            return np.zeros(3)
        
        # Gravitational impulse
        # Δv = 2GM/(b*v) in impulsive limit
        G = 4 * np.pi**2  # AU^3 / (M_sun * yr^2)
        M_star = encounter['mass']
        v_star = encounter['velocity']
        
        # Impulse magnitude
        dv_magnitude = 2 * G * M_star / (r * v_star)
        
        # Direction (perpendicular to velocity)
        # Simplified: kick in direction of star
        dv_vec = dv_magnitude * (star_pos - particle_pos) / r
        
        return dv_vec
    
    def check_for_encounter(self, t_years, dt_years):
        """
        Check if an encounter occurs in this timestep (Monte Carlo).
        
        Args:
            t_years: Current time (years)
            dt_years: Timestep size (years)
        
        Returns:
            encounter dict or None
        """
        if not self.enabled:
            return None
        
        # Probability of encounter in this timestep
        prob = self.encounter_rate * dt_years
        
        if np.random.random() < prob:
            return self.generate_encounter(t_years)
        
        return None
    
    def apply_to_simulation(self, sim, t, dt):
        """
        Apply stellar flyby kicks to simulation.
        
        Args:
            sim: REBOUND simulation
            t: Current time (REBOUND units)
            dt: Timestep (REBOUND units)
        """
        if not self.enabled:
            return
        
        t_years = t / (2 * np.pi)
        dt_years = dt / (2 * np.pi)
        
        # Check for encounter
        encounter = self.check_for_encounter(t_years, dt_years)
        
        if encounter is not None:
            # Apply impulse to outer particles
            for i, p in enumerate(sim.particles):
                if i == 0:  # Skip Sun
                    continue
                
                # Only affect distant objects (> 50 AU)
                r = np.sqrt(p.x**2 + p.y**2 + p.z**2)
                if r < 50:
                    continue
                
                pos = np.array([p.x, p.y, p.z])
                dv = self.calculate_impulse(pos, encounter)
                
                # Apply velocity kick
                p.vx += dv[0]
                p.vy += dv[1]
                p.vz += dv[2]


if __name__ == "__main__":
    # Test module
    print("=== Testing Stellar Flybys ===\n")
    
    flybys = StellarFlybys(enabled=True, encounter_rate=1e-8)
    
    # Simulate encounters over 1 Gyr
    print("Simulating encounters over 1 Gyr...")
    t = 0
    dt = 1e6  # 1 Myr steps
    n_steps = 1000
    
    for step in range(n_steps):
        encounter = flybys.check_for_encounter(t, dt)
        t += dt
    
    print(f"\nTotal encounters: {flybys.total_encounters}")
    print(f"Expected: ~{n_steps * dt * flybys.encounter_rate:.1f}")
    
    if flybys.total_encounters > 0:
        print("\nFirst encounter details:")
        enc = flybys.encounters[0]
        print(f"  Mass: {enc['mass']:.2f} M_sun")
        print(f"  Distance: {enc['impact_parameter']:.0f} AU")
        print(f"  Velocity: {enc['velocity']:.2f} AU/yr")
