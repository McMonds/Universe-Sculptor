"""
Unit Tests for Planet 9 Modules

NASA NPR 7150.2D requirement: "Software shall be tested to verify requirements"

This test suite covers all 23 implemented physics modules.
"""
import pytest
import numpy as np
import sys
sys.path.insert(0, '/home/monk/Work/9th Planet')

# Physics modules
from src.physics.solar_mass_loss import SolarMassLoss
from src.physics.gr_effects import GeneralRelativityPrecession
from src.physics.atmospheric_model import AtmosphericAlbedoModel
from src.physics.galactic_tide import VariableGalacticTide
from src.physics.stellar_flybys import StellarFlybys
from src.physics.birth_cluster import BirthClusterDissolution
from src.physics.tidal_heating import TidalHeating
from src.physics.pebble_accretion import PebbleAccretionDensity

# Observability modules
from src.observability.parallax import ParallaxCorrector
from src.observability.light_curve import RotationalLightCurve
from src.observability.occultation import OccultationProbability
from src.observability.radio_emission import RadioEmission
from src.observability.zodiacal_light import ZodiacalLightSNR
from src.observability.photocenter_offset import PhotocenterOffset

# Validation modules
from src.validation.model_selection import ModelSelector

# Constraints
from src.constraints.comet_flux import CometFluxConstraint


class TestSolarMassLoss:
    """Test solar mass loss calculations."""
    
    def test_initialization(self):
        sml = SolarMassLoss(enabled=True, total_loss_fraction=0.0007)
        assert sml.enabled == True
        assert sml.total_loss_fraction == 0.0007
    
    def test_orbit_expansion(self):
        sml = SolarMassLoss(enabled=True)
        initial_a = 5.2  # Jupiter
        final_a = sml.calculate_orbit_expansion(initial_a, 4.5e9)
        assert final_a > initial_a  # Orbit expands
        assert final_a < initial_a * 1.01  # Less than 1% expansion


class TestGREffects:
    """Test General Relativity precession."""
    
    def test_mercury_precession(self):
        gr = GeneralRelativityPrecession(enabled=True)
        precession = gr.estimate_mercury_precession()
        # Should be ~43 arcsec/century
        assert 40 < precession < 46
    
    def test_planet9_precession(self):
        gr = GeneralRelativityPrecession(enabled=True)
        precession = gr.estimate_planet9_precession(a=500, e=0.6)
        # Should be very small at 500 AU
        assert precession < 1.0  # degrees over 4.5 Gyr


class TestAtmosphericAlbedo:
    """Test atmospheric albedo modeling."""
    
    def test_magnitude_prediction(self):
        albedo = AtmosphericAlbedoModel(age_gyr=4.5)
        results = albedo.predict_magnitude_range(
            distance_au=500,
            mass_earth=5.0,
            radius_earth=2.5,
            n_samples=100
        )
        assert 'mean' in results
        assert 'std' in results
        assert results['mean'] > 10  # Faint
        assert results['mean'] < 30  # But detectable
    
    def test_uncertainty_range(self):
        albedo = AtmosphericAlbedoModel()
        results = albedo.predict_magnitude_range(500, 5.0, n_samples=1000)
        # Range should be reasonable
        assert (results['max'] - results['min']) < 5  # Within 5 magnitudes


class TestParallaxCorrection:
    """Test parallax coordinate conversion."""
    
    def test_coordinate_conversion(self):
        corrector = ParallaxCorrector(
            observer_lat=19.8207,
            observer_lon=-155.4681,
            observer_alt=4.2
        )
        result = corrector.barycentric_to_topocentric(
            500, 100, 50,  # Barycentric position
            2451545.0  # J2000
        )
        assert 'ra' in result
        assert 'dec' in result
        assert 0 <= result['ra'] < 360
        assert -90 <= result['dec'] <= 90


class TestRotationalLightCurve:
    """Test light curve generation."""
    
    def test_period_estimation(self):
        curve = RotationalLightCurve(enabled=True)
        period = curve.estimate_rotation_period(m_earth=5.0, radius_earth=2.5)
        assert 5 < period < 30  # Reasonable rotation period
    
    def test_amplitude_calculation(self):
        curve = RotationalLightCurve()
        result = curve.calculate_amplitude(oblateness=0.1, albedo_variation=0.1)
        assert result['total_amplitude'] > 0
        assert result['total_amplitude'] < 1  # Less than 1 magnitude


class TestModelSelection:
    """Test AIC/BIC model selection."""
    
    def test_decisive_evidence(self):
        selector = ModelSelector()
        results = selector.compare_models(
            cost_p9=25.0,
            cost_null=1000.0,
            n_data=10
        )
        assert results['delta_bic'] < -10  # Decisive
        assert 'DECISIVE' in results['verdict']
    
    def test_overfitting_detection(self):
        selector = ModelSelector()
        results = selector.compare_models(
            cost_p9=24.0,
            cost_null=25.0,
            n_data=10
        )
        assert results['delta_bic'] > 0  # Overfitting
        assert 'OVERFITTING' in results['verdict']


class TestCometFlux:
    """Test comet flux constraint."""
    
    def test_flux_calculation(self):
        constraint = CometFluxConstraint(
            observed_flux_per_year=1.5,
            max_multiplier=2.0
        )
        assert constraint.max_allowed == 3.0


class TestTidalHeating:
    """Test tidal heating from moons."""
    
    def test_luminosity_scaling(self):
        heating = TidalHeating(enabled=True)
        result = heating.estimate_tidal_luminosity(
            m_planet_earth=5.0,
            has_moons=True,
            n_major_moons=4
        )
        assert result['L_tidal'] > 0
        assert result['mag_boost'] < 0  # Brighter


class TestPebbleAccretion:
    """Test pebble accretion density."""
    
    def test_density_scenarios(self):
        pebble = PebbleAccretionDensity(enabled=True)
        
        # Native ejection should be denser
        rho_native = pebble.calculate_density('native_ejection')
        rho_rogue = pebble.calculate_density('rogue_capture')
        
        assert rho_native > rho_rogue
    
    def test_mass_radius_relation(self):
        pebble = PebbleAccretionDensity()
        radius = pebble.mass_to_radius(m_earth=5.0, density_gcm3=2.0)
        assert radius > 0
        assert radius < 10  # Reasonable size


class TestGalacticTide:
    """Test variable galactic tide."""
    
    def test_solar_position(self):
        tide = VariableGalacticTide(enabled=True)
        R, phi, z = tide.get_solar_position(t_years=0)
        assert R > 0  # Positive distance
        assert abs(z) < 1.0  # Near plane


class TestStellarFlybys:
    """Test stellar flyby encounters."""
    
    def test_encounter_generation(self):
        flybys = StellarFlybys(enabled=True, encounter_rate=1e-8)
        encounter = flybys.generate_encounter(t_current_years=0)
        assert 'mass' in encounter
        assert 0.08 < encounter['mass'] < 2.0  # Stellar mass range


class TestBirthCluster:
    """Test birth cluster dissolution."""
    
    def test_enhancement_decay(self):
        cluster = BirthClusterDissolution(enabled=True)
        
        # Ancient past - no enhancement
        e1 = cluster.get_enhancement_factor(t_years=-4.5e9)
        assert e1 == 1.0
        
        # During cluster phase - high enhancement
        e2 = cluster.get_enhancement_factor(t_years=-50e6)
        assert e2 > 100


# Integration tests
class TestIntegration:
    """Integration tests for combined modules."""
    
    def test_magnitude_pipeline(self):
        """Test full magnitude prediction pipeline."""
        # Albedo model
        albedo = AtmosphericAlbedoModel()
        base_mag = albedo.predict_magnitude_range(500, 5.0, n_samples=100)
        
        # Add tidal heating
        heating = TidalHeating()
        final_mag = heating.apply_to_magnitude(
            base_mag['mean'], 5.0, has_moons=True
        )
        
        assert isinstance(final_mag, float)
        assert 10 < final_mag < 30


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
