#!/bin/bash
# Oracle Cloud ARM64 Deployment Script
# Run on Oracle Cloud Ampere A1 instance (Ubuntu 22.04/24.04)

set -e

echo "=== Planet 9 Historical Solver - Oracle Cloud Setup ==="
echo ""

# Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "2. Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt install -y docker.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "   ✓ Docker installed"
else
    echo "   ✓ Docker already installed"
fi

# Install rsync for data transfer
echo "3. Installing rsync..."
sudo apt install -y rsync

# Create workspace
echo "4. Creating workspace..."
mkdir -p ~/planet9_project
mkdir -p ~/planet9_results

# Build Docker image (ARM64-native)
echo "5. Building ARM64-optimized Docker image..."
cd ~/planet9_project
docker build -f Dockerfile.arm64 -t planet9-solver:arm64 .

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the Historical Solver:"
echo ""
echo "  docker run -d \\"
echo "    --name planet9_solver \\"
echo "    --restart unless-stopped \\"
echo "    -v ~/planet9_results:/app/data \\"
echo "    -e SCENARIO=rogue_capture \\"
echo "    -e MAX_GENERATIONS=100 \\"
echo "    planet9-solver:arm64"
echo ""
echo "Monitor progress:"
echo "  docker logs -f planet9_solver"
echo ""
echo "System Stats:"
echo "  docker stats planet9_solver"
echo ""
