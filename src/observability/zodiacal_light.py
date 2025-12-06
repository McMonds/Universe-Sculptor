"""
Zodiacal Light SNR Module
Category G5: Advanced Observations [MEDIUM]

Zodiacal light = sunlight reflected off dust near ecliptic plane.
Creates bright "fog" that makes faint objects harder to detect.

Planet 9 far from ecliptic → less zodiacal contamination → better SNR.

Reference: Leinert et al. (1998) "Zodiacal Light"
"""
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - ZODIACAL - %(message)s')

class ZodiacalLightSNR:
    """Calculates SNR accounting for zodiacal light background."""
    
    def __init__(self, enabled=True):
        self.enabled = enabled
        logging.info(f"Zodiacal Light SNR: {'ENABLED' if enabled else 'DISABLED'}")
    
    def zodiacal_brightness(self, ecliptic_lat_deg, ecliptic_lon_offset_deg):
        """
        Zodiacal light surface brightness.
        
        Args:
            ecliptic_lat_deg: Latitude from ecliptic (degrees)
            ecliptic_lon_offset_deg: Angle from Sun (degrees)
        
        Returns:
            float: Surface brightness (mag/arcsec²)
        """
        # Minimum at ecliptic pole: ~23 mag/arcsec²
        # Maximum near ecliptic + Sun: ~18 mag/arcsec²
        
        lat_rad = np.radians(abs(ecliptic_lat_deg))
        
        # Latitude component (brighter near plane)
        lat_factor = np.exp(-lat_rad / 0.4)
        
        # Elongation from Sun (brighter near Sun)
        elong_factor = 1.0 / (1 + ecliptic_lon_offset_deg / 90)
        
        # Combined
        brightness = 23 - 5 * lat_factor * elong_factor
        
        return brightness
    
    def calculate_snr(self, object_mag, zodiacal_mag_per_arcsec2,
                     seeing_arcsec=1.0, exposure_sec=300,
                     telescope_aperture_m=2.4):
        """
        Signal-to-noise ratio calculation.
        
        Args:
            object_mag: Object magnitude
            zodiacal_mag_per_arcsec2: Sky background
            seeing_arcsec: Seeing disk (arcsec)
            exposure_sec: Exposure time (seconds)
            telescope_aperture_m: Aperture (meters)
        
        Returns:
            dict: SNR analysis
        """
        # Convert mag to counts
        # Assume mag 0 = 10^6 photons/sec/m²
        zero_point = 1e6
        
        # Object flux
        object_flux = zero_point * 10**(-object_mag / 2.5) * np.pi * (telescope_aperture_m / 2)**2 * exposure_sec
        
        # Sky flux (per arcsec²)
        sky_area_arcsec2 = np.pi * seeing_arcsec**2
        sky_flux_per_arcsec2 = zero_point * 10**(-zodiacal_mag_per_arcsec2 / 2.5) * np.pi * (telescope_aperture_m / 2)**2 * exposure_sec
        sky_flux_total = sky_flux_per_arcsec2 * sky_area_arcsec2
        
        # SNR = signal / sqrt(signal + sky + readnoise)
        readnoise = 10  # electrons
        snr = object_flux / np.sqrt(object_flux + sky_flux_total + readnoise**2)
        
        result = {
            'snr': snr,
            'object_flux': object_flux,
            'sky_flux': sky_flux_total,
            'zodiacal_mag': zodiacal_mag_per_arcsec2,
            'detectable_5sigma': snr > 5
        }
        
        logging.info(f"SNR Analysis:")
        logging.info(f"  Object mag: {object_mag:.2f}")
        logging.info(f"  Zodiacal: {zodiacal_mag_per_arcsec2:.2f} mag/arcsec²")
        logging.info(f"  Object flux: {object_flux:.1f} e⁻")
        logging.info(f"  Sky flux: {sky_flux_total:.1f} e⁻")
        logging.info(f"  SNR: {snr:.2f}")
        logging.info(f"  5-σ detection: {'YES ✓' if result['detectable_5sigma'] else 'NO ✗'}")
        
        return result


if __name__ == "__main__":
    print("=== Testing Zodiacal Light SNR ===\n")
    
    zodiacal = ZodiacalLightSNR(enabled=True)
    
    # Planet 9 at high ecliptic latitude
    zod_brightness = zodiacal.zodiacal_brightness(
        ecliptic_lat_deg=45,  # High latitude
        ecliptic_lon_offset_deg=120  # Away from Sun
    )
    
    print(f"Zodiacal brightness: {zod_brightness:.2f} mag/arcsec²\n")
    
    # SNR for mag 22 object
    snr = zodiacal.calculate_snr(
        object_mag=22.0,
        zodiacal_mag_per_arcsec2=zod_brightness,
        seeing_arcsec=1.0,
        exposure_sec=300,
        telescope_aperture_m=2.4
    )
