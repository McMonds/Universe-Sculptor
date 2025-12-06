#!/bin/bash
# Data Download Script for Project 9th Planet

echo "=== Downloading External Datasets ==="

# Create data directory
mkdir -p data/maps

# 1. WISE/NEOWISE Exclusion Map
echo "Downloading WISE Exclusion Map..."
# Source: Meisner et al. (2020) - https://arxiv.org/abs/2004.07283
# The actual map URL would be from IPAC/IRSA
# For demo, we create a placeholder
cat > data/maps/wise_exclusion.txt << EOF
# WISE Exclusion Map Placeholder
# Real data: https://irsa.ipac.caltech.edu/data/WISE/
# Format: HEALPix FITS file
# This is a placeholder. Download the actual map from IPAC.
EOF

# 2. Gaia DR3 Star Density Map
echo "Downloading Gaia Density Map..."
# Source: ESA Gaia Archive
# The actual map would be a HEALPix map of star counts
cat > data/maps/gaia_density.txt << EOF
# Gaia DR3 Density Map Placeholder
# Real data: https://gea.esac.esa.int/archive/
# Format: HEALPix FITS file
# This is a placeholder. Download the actual map from ESA.
EOF

# 3. SPICE Kernels (DE440)
echo "Downloading SPICE Kernels..."
mkdir -p data/kernels
# Real URL: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/
cat > data/kernels/de440.txt << EOF
# DE440 Kernel Placeholder
# Real data: https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp
# Download: wget https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp
EOF

echo "=== Data Download Instructions ==="
echo ""
echo "The placeholders have been created in data/maps/"
echo ""
echo "To download REAL data:"
echo "1. WISE Map: Visit https://irsa.ipac.caltech.edu/data/WISE/"
echo "2. Gaia Map: Visit https://gea.esac.esa.int/archive/"
echo "3. DE440: wget https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp -O data/kernels/de440.bsp"
echo ""
echo "Total download size: ~2-5 GB"

chmod +x "$0"
