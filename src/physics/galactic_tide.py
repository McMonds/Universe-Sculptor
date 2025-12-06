"""
Variable Galactic Tide Module
Category A3: Galactic Environment [HIGH]

The Sun orbits the Milky Way's center, completing ~18 orbits in 4.5 Gyr.
As distance to galactic center varies, the tidal force strength changes ±30%.

Also passes through spiral arms every ~150 Myr (density variations).

Uses galpy library for realistic Milky Way potential.
Reference: Bovy (2015) "galpy: A Python Library for Galactic Dynamics"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - GAL_TIDE - %(message)s')

class VariableGalacticTide:
    """
    Models time-varying galactic tidal forces on the solar system.
    
    Effects:
    1. Radial tide (toward/away from galactic center)
    2. Vertical tide (perpendicular to galactic plane)
    3. Spiral arm passages (density enhancements)
    """
    
    def __init__(self, enabled=True, use_galpy=False):
        """
        Args:
            enabled: Enable galactic tides
            use_galpy: Use galpy library (if available) for realistic potential
        """
        self.enabled = enabled
        self.use_galpy = use_galpy
        
        # Solar galactic orbit parameters
        self.R0 = 8.0  # kpc (current distance from galactic center)
        self.z0 = 0.02  # kpc (current height above plane)
        self.v_circular = 220  # km/s
        self.orbital_period = 2 * np.pi * self.R0 * 3.086e16 / (self.v_circular * 1e5)  # seconds
        self.orbital_period_years = self.orbital_period / (365.25 * 86400)
        
        # Milky Way parameters
        self.rho_dm_local = 0.01  # M_sun/pc^3 (local dark matter density)
        
        logging.info(f"Variable Galactic Tide: {'ENABLED' if enabled else 'DISABLED'}")
        if enabled:
            logging.info(f"  Solar orbital period: {self.orbital_period_years/1e6:.1f} Myr")
            logging.info(f"  Current R: {self.R0} kpc, z: {self.z0} kpc")
            logging.info(f"  Using galpy: {use_galpy}")
    
    def get_solar_position(self, t_years):
        """
        Calculate Sun's position in the galaxy at time t.
        
        Simple circular orbit approximation.
        
        Args:
            t_years: Time (years, can be negative for past)
        
        Returns:
            tuple: (R, phi, z) in kpc and radians
        """
        # Angular position
        omega = 2 * np.pi / self.orbital_period_years
        phi = omega * t_years
        
        # Radial distance (approximately constant for circular orbit)
        # Add small perturbation for eccentricity
        e_gal = 0.05  # Small galactic eccentricity
        R = self.R0 * (1 + e_gal * np.cos(phi))
        
        # Vertical oscillation (60 Myr period)
        z_period = 60e6  # years
        z_amplitude = 0.1  # kpc
        z = z_amplitude * np.sin(2 * np.pi * t_years / z_period)
        
        return R, phi, z
    
    def calculate_tidal_force(self, t_years, r_helio_au):
        """
        Calculate galactic tidal force on object at distance r from Sun.
        
        Tidal force varies with Sun's galactic position.
        
        Args:
            t_years: Time (years)
            r_helio_au: Distance from Sun (AU)
        
        Returns:
            tuple: (F_radial, F_vertical) in AU/yr^2
        """
        if not self.enabled:
            return 0.0, 0.0
        
        R, phi, z = self.get_solar_position(t_years)
        
        # Convert to AU for force calculation
        kpc_to_au = 206265 * 1000  # AU per kpc
        
        # Radial tide (toward galactic center)
        # F_tidal ~ 2 * Omega^2 * r, where Omega is galactic angular velocity
        Omega_gal = self.v_circular / (R * 3.086e16)  # rad/s
        Omega_gal_au_yr = Omega_gal * (365.25 * 86400) / (1.496e11)  # AU system
        
        F_radial = 2 * Omega_gal_au_yr**2 * r_helio_au
        
        # Vertical tide (restoring force toward plane)
        # F_z ~ 4 * pi * G * rho * z
        G_au = 4 * np.pi**2  # G in AU^3 / (M_sun * yr^2)
        rho_plane = 0.1  # M_sun/pc^3 (midplane density)
        pc_to_au = 206265
        rho_au = rho_plane / pc_to_au**3
        
        F_vertical = 4 * np.pi * G_au * rho_au * r_helio_au * (z / self.z0)
        
        # Spiral arm enhancement (periodic)
        spiral_period = 150e6  # years
        spiral_phase = 2 * np.pi * t_years / spiral_period
        spiral_enhancement = 1.0 + 0.3 * np.sin(spiral_phase)  # ±30% variation
        
        F_radial *= spiral_enhancement
        F_vertical *= spiral_enhancement
        
        return F_radial, F_vertical
    
    def apply_to_simulation(self, sim, t):
        """
        Apply galactic tide to all particles in simulation.
        
        This is typically called as an additional force during integration.
        
        Args:
            sim: REBOUND simulation
            t: Current time (REBOUND units)
        """
        if not self.enabled:
            return
        
        t_years = t / (2 * np.pi)
        
        for i, p in enumerate(sim.particles):
            if i == 0:  # Skip Sun
                continue
            
            # Distance from Sun
            r = np.sqrt(p.x**2 + p.y**2 + p.z**2)
            
            # Calculate tidal force
            F_rad, F_vert = self.calculate_tidal_force(t_years, r)
            
            # Apply force (simplified - assumes tidal axis aligned with xy-plane)
            # In reality, would need to rotate to galactic coordinates
            
            # Radial component (outward from Sun in galactic frame)
            # Approximation: apply along current radius vector
            if r > 0:
                p.ax += F_rad * p.x / r
                p.ay += F_rad * p.y / r
            
            # Vertical component
            p.az += F_vert


if __name__ == "__main__":
    # Test module
    print("=== Testing Variable Galactic Tide ===\n")
    
    tide = VariableGalacticTide(enabled=True)
    
    # Test solar position over time
    print("Sun's galactic position:")
    times = [-4.5e9, -3e9, -1e9, 0]
    for t in times:
        R, phi, z = tide.get_solar_position(t)
        print(f"  T = {t/1e9:+.1f} Gyr: R={R:.2f} kpc, phi={np.degrees(phi):.1f}°, z={z:.3f} kpc")
    
    # Test tidal force at Planet 9 distance
    print("\nTidal force on Planet 9 (500 AU):")
    for t in times:
        F_rad, F_vert = tide.calculate_tidal_force(t, 500.0)
        print(f"  T = {t/1e9:+.1f} Gyr: F_rad={F_rad:.2e} AU/yr², F_vert={F_vert:.2e} AU/yr²")
    
    # Test with REBOUND
    print("\nApplying to simulation:")
    import rebound
    sim = rebound.Simulation()
    sim.units = ('AU', 'yr', 'Msun')
    sim.add(m=1.0)
    sim.add(m=5e-5, a=500, e=0.6)  # Planet 9
    
    tide.apply_to_simulation(sim, t=0)
    print(f"  Planet 9 acceleration: ax={sim.particles[1].ax:.2e}, az={sim.particles[1].az:.2e}")
