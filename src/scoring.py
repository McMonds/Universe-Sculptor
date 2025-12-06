import numpy as np
import rebound

def score_universe(sim, original_tno_ids):
    """
    The Cost Function - Measures how well a simulation matches reality.
    
    Lower score = Closer to observed solar system
    
    Args:
        sim: REBOUND simulation at T=now
        original_tno_ids: List of hash values for eTNO particles
    
    Returns:
        float: Total cost score
    """
    score = 0.0
    
    # Get all particle orbits at once
    try:
        orbits = [p.calculate_orbit(primary=sim.particles[0]) for p in sim.particles]
    except:
        return 1e9  # If orbit calculation fails, infinite cost
    
    # 1. ORBITAL CLUSTERING METRIC (Batygin & Brown 2016)
    # Calculate Mean Standard Deviation of Longitude of Perihelion
    varpis = []
    
    for particle in sim.particles:
        if hasattr(particle, 'hash') and particle.hash in original_tno_ids:
            try:
                # varpi = Omega + omega (longitude of perihelion)
                orbit = orbits[particle.index]
                varpi = orbit.Omega + orbit.omega
                varpis.append(varpi)
            except:
                continue
    
    # Calculate spread on the unit circle (vector averaging)
    # 0 = Perfect Alignment, 1 = Random Dispersion
    if len(varpis) > 2:
        angles = np.array(varpis)
        # Circular variance magnitude
        r = np.abs(np.mean(np.exp(1j * angles)))
        alignment_score = (1 - r) * 100.0  # Scaling weight
        score += alignment_score
    else:
        score += 1000.0  # Not enough TNOs survived
    
    # 2. SOLAR OBLIQUITY CHECK (The 6-Degree Tilt)
    # The Sun's rotation axis is tilted 6° relative to the invariable plane
    # We approximate this by checking the total angular momentum vector
    try:
        # Calculate invariable plane from total angular momentum
        L_total = np.array([0.0, 0.0, 0.0])
        for p in sim.particles:
            r = np.array([p.x, p.y, p.z])
            v = np.array([p.vx, p.vy, p.vz])
            L_total += p.m * np.cross(r, v)
        
        L_hat = L_total / np.linalg.norm(L_total)
        
        # Assume solar spin is close to z-axis
        # In reality, would need to track Sun's rotation
        solar_axis = np.array([0, 0, 1])
        
        # Angle between them
        cos_theta = np.dot(solar_axis, L_hat)
        tilt_deg = np.degrees(np.arccos(np.clip(cos_theta, -1, 1)))
        
        tilt_error = abs(tilt_deg - 6.0)
        score += tilt_error * 5.0  # Weight multiplier
    except:
        score += 100.0  # Penalty if calculation fails
    
    # 3. COLD CLASSICAL SURVIVAL CHECK
    # The Cold Classical Kuiper Belt (40-50 AU, low-e) must NOT be destroyed
    # Count particles in safe zone
    safe_zone_count = 0
    destroyed_count = 0
    
    for i, p in enumerate(sim.particles):
        try:
            if hasattr(p, 'hash') and p.hash > 90000:  # Test particles
                orbit = orbits[i]
                if 40 < orbit.a < 50:
                    if orbit.e < 0.1:
                        safe_zone_count += 1
                    else:
                        destroyed_count += 1
        except:
            continue
    
    # Massive penalty if we destroyed the Kuiper Belt
    if safe_zone_count < 10:  # Assuming we started with 20+
        score += 1000.0
    
    return score
