"""
Rotational Light Curve Module
Category G2: Advanced Observations [MEDIUM]

Planet 9 isn't a perfect sphere - it rotates (likely 10-20 hours period).
If it has surface features (storms, spots) or oblong shape, brightness varies.

This periodic signal helps detection and characterization.

Reference: Ginzburg & Sari (2018) "The detectability of Planet Nine with LSST"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - LIGHT_CURVE - %(message)s')

class RotationalLightCurve:
    """
    Models brightness variations from rotation.
    
    Assumes ellipsoidal shape or surface albedo variations.
    """
    
    def __init__(self, enabled=True):
        """
        Args:
            enabled: Enable rotational light curve modeling
        """
        self.enabled = enabled
        
        logging.info(f"Rotational Light Curve: {'ENABLED' if enabled else 'DISABLED'}")
    
    def estimate_rotation_period(self, m_earth, radius_earth):
        """
        Estimate rotation period based on size.
        
        Most planets spin down to ~10-20 hour periods.
        
        Args:
            m_earth: Mass (Earth masses)
            radius_earth: Radius (Earth radii)
        
        Returns:
            float: Rotation period (hours)
        """
        # Empirical: larger planets rotate slower (tidal evolution)
        # Jupiter: 10 hours, Saturn: 10.7 hours
        
        period_hours = 10 + 2 * (m_earth / 10)  # Rough scaling
        period_hours = np.clip(period_hours, 5, 30)
        
        return period_hours
    
    def calculate_amplitude(self, oblateness=0.1, albedo_variation=0.1):
        """
        Calculate light curve amplitude.
        
        Sources of variation:
        1. Shape (oblateness) → projected area varies
        2. Surface features (albedo) → brightness varies
        
        Args:
            oblateness: (R_eq - R_pole) / R_eq (0.1 = 10% oblate)
            albedo_variation: ΔA / A (0.1 = 10% variation)
        
        Returns:
            dict: Light curve parameters
        """
        # Shape contribution (ellipsoid rotating)
        # Flux ∝ projected area
        # Amplitude ≈ 2.5 * log₁₀(1 + oblateness)
        
        mag_amplitude_shape = 2.5 * np.log10(1 + oblateness)
        
        # Albedo contribution (spots/storms)
        # Amplitude ≈ 2.5 * log₁₀(1 + albedo_var)
        
        mag_amplitude_albedo = 2.5 * np.log10(1 + albedo_variation)
        
        # Total amplitude (add in quadrature)
        total_amplitude = np.sqrt(mag_amplitude_shape**2 + mag_amplitude_albedo**2)
        
        result = {
            'shape_amplitude': mag_amplitude_shape,
            'albedo_amplitude': mag_amplitude_albedo,
            'total_amplitude': total_amplitude
        }
        
        logging.info(f"Light Curve Amplitude:")
        logging.info(f"  From shape: {mag_amplitude_shape:.3f} mag")
        logging.info(f"  From albedo: {mag_amplitude_albedo:.3f} mag")
        logging.info(f"  Total: {total_amplitude:.3f} mag")
        
        return result
    
    def generate_light_curve(self, base_magnitude, period_hours, amplitude_mag,
                           times_hours, phase_offset=0):
        """
        Generate synthetic light curve.
        
        Args:
            base_magnitude: Mean magnitude
            period_hours: Rotation period (hours)
            amplitude_mag: Peak-to-peak amplitude
            times_hours: Observation times (hours)
            phase_offset: Initial phase (0-1)
        
        Returns:
            array: Magnitudes at each time
        """
        if not self.enabled:
            return np.ones_like(times_hours) * base_magnitude
        
        # Sinusoidal variation
        phase = (times_hours / period_hours + phase_offset) * 2 * np.pi
        
        # Magnitude varies: m(t) = m₀ + A * sin(phase)
        magnitudes = base_magnitude + (amplitude_mag / 2) * np.sin(phase)
        
        return magnitudes
    
    def detection_strategy(self, base_mag, period_hours, amplitude_mag,
                          telescope_limit=24.0, min_observations=10):
        """
        Determine if light curve is detectable.
        
        Args:
            base_mag: Mean magnitude
            period_hours: Period
            amplitude_mag: Amplitude
            telescope_limit: Limiting magnitude
            min_observations: Minimum points needed
        
        Returns:
            dict: Detectability assessment
        """
        # Peak brightness
        peak_mag = base_mag - amplitude_mag / 2
        
        # Faintest point
        faint_mag = base_mag + amplitude_mag / 2
        
        # Observable if peak < limit
        observable = peak_mag < telescope_limit
        
        # Required cadence (sample at least 4 times per period)
        required_cadence_hours = period_hours / 4
        
        # Duration for N observations
        min_duration_hours = min_observations * required_cadence_hours
        
        result = {
            'observable': observable,
            'peak_mag': peak_mag,
            'faint_mag': faint_mag,
            'amplitude': amplitude_mag,
            'period': period_hours,
            'required_cadence_hours': required_cadence_hours,
            'min_duration_hours': min_duration_hours,
            'telescope_limit': telescope_limit
        }
        
        logging.info(f"\nDetection Strategy:")
        logging.info(f"  Base magnitude: {base_mag:.2f}")
        logging.info(f"  Peak: {peak_mag:.2f}, Faint: {faint_mag:.2f}")
        logging.info(f"  Amplitude: {amplitude_mag:.3f} mag")
        logging.info(f"  Period: {period_hours:.1f} hours")
        logging.info(f"  Required cadence: {required_cadence_hours:.1f} hours")
        logging.info(f"  Min duration: {min_duration_hours:.1f} hours (~{min_duration_hours/24:.1f} days)")
        logging.info(f"  Observable: {'YES ✓' if observable else 'NO ✗'}")
        
        return result


if __name__ == "__main__":
    # Test module
    print("=== Testing Rotational Light Curve ===\n")
    
    curve = RotationalLightCurve(enabled=True)
    
    # Estimate parameters for 5 M⊕ planet
    period = curve.estimate_rotation_period(m_earth=5.0, radius_earth=2.5)
    print(f"Estimated period: {period:.1f} hours\n")
    
    # Calculate amplitude
    amplitude_result = curve.calculate_amplitude(oblateness=0.1, albedo_variation=0.15)
    
    # Detection strategy
    strategy = curve.detection_strategy(
        base_mag=22.0,
        period_hours=period,
        amplitude_mag=amplitude_result['total_amplitude'],
        telescope_limit=24.0
    )
    
    # Generate sample light curve
    print("\n\nGenerating sample light curve...")
    times = np.linspace(0, 48, 100)  # 48 hours, 100 points
    mags = curve.generate_light_curve(
        base_magnitude=22.0,
        period_hours=period,
        amplitude_mag=amplitude_result['total_amplitude'],
        times_hours=times
    )
    
    print(f"  Time span: {times.max():.1f} hours")
    print(f"  Brightness range: {mags.min():.2f} - {mags.max():.2f} mag")
    print(f"  Variation: {mags.max() - mags.min():.3f} mag")
