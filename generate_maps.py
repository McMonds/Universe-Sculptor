#!/usr/bin/env python3
"""
Generate Synthetic WISE and Gaia Maps for Testing
Based on published survey characteristics
"""
import numpy as np
import healpy as hp
import os

print("Generating Synthetic HEALPix Maps...")

# HEALPix Parameters
NSIDE = 64  # Resolution (64 -> ~1 degree pixels)
NPIX = hp.nside2npix(NSIDE)

# 1. WISE Exclusion Map
# Based on Meisner et al. (2020) - regions where WISE is sensitive
# Exclusion = 1 if WISE can "see" there, 0 if blind
print(f"Creating WISE Exclusion Map (NSIDE={NSIDE})...")

wise_map = np.ones(NPIX)  # Start with all visible

# Mark the Galactic Plane as "blind" (high background noise)
# Galactic latitude |b| < 10 degrees is noisy
theta, phi = hp.pix2ang(NSIDE, np.arange(NPIX))
# Convert to Galactic coordinates (approximation)
# For simplicity: assume Galactic plane is around ecliptic plane
# Real: would use astropy coordinate transforms

# Simulate galactic plane exclusion
l = phi  # Galactic longitude (approximation)
b = np.pi/2 - theta  # Galactic latitude (approximation)

# Exclude |b| < 10 degrees
galactic_mask = np.abs(b) < np.radians(10)
wise_map[galactic_mask] = 0  # Blind in galactic plane

# Save
os.makedirs('data/maps', exist_ok=True)
hp.write_map('data/maps/wise_exclusion.fits', wise_map, overwrite=True)
print(f"  Saved: data/maps/wise_exclusion.fits")

# 2. Gaia Density Map
# Number of stars per pixel
print(f"Creating Gaia Star Density Map (NSIDE={NSIDE})...")

# Based on Gaia DR3: ~1.8 billion stars
# Density is high near Galactic plane, low at poles
# Model: Exponential disk

# Galactic plane has ~10^6 stars per sq degree
# Poles have ~10^3 stars per sq degree

gaia_density = np.zeros(NPIX)

# Density model: N = N0 * exp(-|b|/scale_height)
N0 = 1e6  # Stars per sq deg at plane
scale_height = np.radians(5)  # Scale height in radians

for i in range(NPIX):
    lat = np.abs(b[i])
    gaia_density[i] = N0 * np.exp(-lat / scale_height)

# Save
hp.write_map('data/maps/gaia_density.fits', gaia_density, overwrite=True)
print(f"  Saved: data/maps/gaia_density.fits")

print("\n=== Map Generation Complete ===")
print("WISE Exclusion: 1=visible, 0=blind (galactic plane)")
print(f"Gaia Density: {gaia_density.min():.0f} to {gaia_density.max():.0f} stars/sq-deg")
