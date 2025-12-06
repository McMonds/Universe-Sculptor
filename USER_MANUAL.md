# Universe Sculptor - User Manual

**Version**: 1.0.0  
**Last Updated**: 2025-12-06

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Running Simulations](#running-simulations)
6. [Module Reference](#module-reference)
7. [Data Management](#data-management)
8. [Visualization](#visualization)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Usage](#advanced-usage)

---

## 1. Introduction

Universe Sculptor is a **historical N-body solver** that finds Planet 9's initial conditions 4.5 billion years ago by solving the Solar System as a boundary value problem.

### What Makes It Different?

**Traditional simulators**: "Given Planet 9 at (a,e,i), what happens?"  
**Universe Sculptor**: "Given TODAY's Solar System, where was Planet 9born?"

This transforms the search from trial-and-error into systematic optimization.

###Use Cases

- **Academic Research**: Generate publication-quality Planet 9 predictions
- **Telescope Targeting**: Calculate precise sky coordinates for observation
- **Scientific Education**: Visualize solar system evolution over 4.5 Gyr
- **Software Development**: Extend with custom physics modules

---

## 2. Installation

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux, macOS, Windows | Linux (Ubuntu 22.04+) |
| **Python** | 3.10+ | 3.11 |
| **RAM** | 8 GB | 16 GB |
| **Disk** | 5 GB | 20 GB (with all data) |
| **CPU** | 4 cores | 8+ cores |

### Step-by-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/[USERNAME]/Universe-Sculptor.git
cd Universe-Sculptor

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Download NASA data (~500 MB)
chmod +x download_data.sh
./download_data.sh

# 5. Verify installation
python -c "from src.physics.solar_mass_loss import SolarMassLoss; print('✓ Success!')"
```

### Optional Dependencies

```bash
# For BNN surrogate (machine learning acceleration)
pip install tensorflow tensorflow-probability  # ~2 GB

# For advanced plotting
pip install seaborn plotly

# For development
pip install pytest pytest-cov flake8
```

---

## 3. Quick Start

### Your First Simulation (5 minutes)

```bash
# Run short test integration (1000 years)
python run_historical_solver.py --test

# Output: Energy conservation check, TNO clustering metric
```

**Expected output**:
```
✓ Energy drift: 1.2e-14 (excellent!)
✓ TNO clustering cost: 45.2
⏱ Runtime: 23 seconds
```

### Understanding the Output

- **Energy drift < 10⁻⁹**: Physics are conserved (good!)
- **TNO clustering cost**: Lower = better match to observations
- **Runtime**: Scales with integration time

---

## 4. Core Concepts

### The "Time Machine" Framework

```
TODAY (T=0)              4.5 Gyr AGO (T=-4.5)
┌─────────────┐         ┌──────────────┐
│ Observed    │ ◄─────  │ Unknown      │
│ TNO         │  Solve  │ Planet 9     │
│ Clustering  │  ◄─────  │ Birth State  │
└─────────────┘         └──────────────┘
    Known                   Optimize
```

**Key idea**: Integrate BACKWARD from today to find initial conditions that produce observed structure.

### The 7-Tier Constraint System

Simulations are scored on 7 tiers of real observations:

| Tier | Constraint | Data Source | Weight |
|------|-----------|-------------|--------|
| **1** | TNO clustering (σ_ϖ) | Batygin+ 2016 | 1000× |
| **2** | Cassini ranging | NASA/JPL | 500× |
| **3** | WISE W1/W2 exclusion | Meisner+ 2017 | 100× |
| **4** | Gaia star density | Gaia DR3 | 50× |
| **5** | TNO semi-major axes | MPC catalog | 10× |
| **6** | TNO inclinations | MPC catalog | 5× |
| **7** | Bonus constraints | Various | 1× |

Lower cost = better match to all observations.

---

## 5. Running Simulations

### Basic Usage

```python
from src.primordial_optimizer import Primordial Optimizer

# Create optimizer
opt = PrimordialOptimizer(
    scenario='rogue_capture',  # or 'native_ejection'
    max_generations=100,
    population_size=50
)

# Run optimization
result = opt.run()

# Access best parameters
print(f"Best Planet 9 orbit:")
print(f"  a = {result['a']} AU")
print(f"  e = {result['e']}")
print(f"  mass = {result['m']*333000:.1f} Earth masses")
```

### Command-Line Interface

```bash
# Full 4.5 Gyr integration (takes hours)
python run_historical_solver.py \
    --scenario rogue_capture \
    --generations 200 \
    --population 100 \
    --workers 8

# With specific modules enabled
python run_historical_solver.py \
    --enable-gr \
    --enable-galactic-tide \
    --enable-stellar-flybys
```

### Configuration Files

Create `config/my_run.yaml`:

```yaml
scenario: rogue_capture
integration:
  timestep: -0.5  # years (negative = backward)
  duration: 4.5e9  # years
  
physics_modules:
  solar_mass_loss: true
  gr_precession: true
  galactic_tide: true
  stellar_flybys: false  # Disable for speed

optimizer:
  max_generations: 500
  population_size: 200
  workers: 16
```

Run with:
```bash
python run_historical_solver.py --config config/my_run.yaml
```

---

## 6. Module Reference

### Physics Modules

#### Solar Mass Loss
**File**: `src/physics/solar_mass_loss.py`

```python
from src.physics.solar_mass_loss import SolarMassLoss

sml = SolarMassLoss(
    enabled=True,
    total_loss_fraction=0.0007  # 0.07% over 4.5 Gyr
)

# Apply to REBOUND simulation
rebx = sml.apply_to_simulation(sim)
```

**What it does**: Orbits expand as Sun loses mass via solar wind.

#### GR Precession
**File**: `src/physics/gr_effects.py`

```python
from src.physics.gr_effects import GeneralRelativityPrecession

gr = GeneralRelativityPrecession(
    enabled=True,
    c_light=10065.32  # AU/yr
)

# Validate with Mercury
precession = gr.estimate_mercury_precession()
# Returns: ~43 arcsec/century
```

**What it does**: Post-Newtonian corrections (Schwarzschild metric).

### Observability Modules

#### Parallax Correction
**File**: `src/observability/parallax.py`

```python
from src.observability.parallax import ParallaxCorrector

corrector = ParallaxCorrector(
    observer_lat=19.82,   # Mauna Kea
    observer_lon=-155.47,
    observer_alt=4.2      # km
)

# Convert barycentric → telescope coordinates
coords = corrector.barycentric_to_topocentric(
    x_bary=500, y_bary=100, z_bary=50,  # AU
    jd=2451545.0  # Julian Date
)

print(f"Point telescope to: RA {coords['ra']:.2f}°, Dec {coords['dec']:.2f}°")
```

### Validation Modules

#### Null Hypothesis Test
**File**: `src/validation/null_hypothesis.py`

```python
from src.validation.null_hypothesis import NullHypothesisValidator

validator = NullHypothesisValidator(
    n_trials=10000,
    target_significance=5.0  # sigma
)

results = validator.run_monte_carlo(observed_cost=25.0)

print(f"p-value: {results['p_value']}")
print(f"Significance: {results['sigma']}-sigma")
# Output: 5.0-sigma = Nobel-worthy!
```

---

## 7. Data Management

### Required Data Files

Universe Sculptor uses **real NASA data**:

| Dataset | Size | Purpose | Source |
|---------|------|---------|--------|
| **SPICE kernels** | 200 MB | Planet ephemerides | NASA JPL |
| **WISE W1/W2 maps** | 150 MB | IR exclusion zones | Meisner+ 2017 |
| **Gaia DR3 density** | 100 MB | Star crowding | Gaia Archive |
| **eTNO catalog** | 50 KB | Observed TNOs | MPC |

### Data Location

```
data/
├── real/
│   ├── de440.bsp          # NASA ephemeris
│   ├── maps/
│   │   ├── wise_w1.fits   # WISE infrared
│   │   └── gaia_dr3.fits  # Gaia stars
│   └── mpc/
│       └── etnos_literature.json
```

### Updating Data

```bash
# Re-download all data
./download_data.sh --force

# Update only eTNO catalog
python download_real_data.py --etnos-only
```

---

## 8. Visualization

### Terminal UI (Text-based)

```bash
# Launch interactive dashboard
python -m src.viz.dashboard
```

**Features**:
- Real-time simulation progress
- Parameter values
- Constraint scores (7 tiers)
- Energy conservation plot

### Generating Time-Lapse Videos

```python
from src.viz.time_lapse import TimeLapseGenerator

gen = TimeLapseGenerator(
    snapshot_dir='results/snapshots',
    output_file='planet9_history.mp4'
)

gen.generate(
    fps=30,
    duration_seconds=60,  # 4.5 Gyr in 60 seconds
    resolution=(1920, 1080)
)
```

### Example Plots

```python
import matplotlib.pyplot as plt
from src.viz.plots import plot_tnocluster, plot_energy_drift

# TNO ϖ distribution
plot_tnocluster(simulation_result)
plt.savefig('tno_clustering.png', dpi=150)

# Energy conservation
plot_energy_drift(hamiltonian_history)
plt.savefig('energy_drift.png', dpi=150)
```

---

## 9. Troubleshooting

### Common Issues

#### "ModuleNotFoundError"
**Problem**: Python can't find `src` modules

**Solution**:
```bash
export PYTHONPATH="."  # Or add to ~/.bashrc
```

#### "REBOUND error: Force 'modify_mass' not found"
**Problem**: reboundx module not compiled correctly

**Solution**:
```bash
pip uninstall reboundx
pip install reboundx --no-cache-dir
```

#### "Simulation diverges (energy drift > 1e-6)"
**Problem**: Timestep too large or integrator issue

**Solution**:
```python
sim.dt = -0.1  # Smaller timestep (slower but stable)
sim.integrator = "ias15"  # More accurate (but slower)
```

#### "Out of memory"
**Problem**: Too many test particles or long integration

**Solution**:
```python
# Reduce test particles
config['n_test_particles'] = 100  # Instead of 1000

# Use checkpointing
config['checkpoint_interval'] = 1e8  # Save every 100 Myr
```

---

## 10. Advanced Usage

### Custom Physics Modules

Create your own module:

```python
# src/physics/my_custom_force.py
class MyCustomForce:
    def __init__(self, enabled=True):
        self.enabled = enabled
    
    def apply_force(self, sim, t):
        if not self.enabled:
            return
        
        # Your custom physics here
        for p in sim.particles:
            p.ax += custom_acceleration_x(p, t)
            # ...
```

Register in `config/physics_modules.yaml`:
```yaml
my_custom_force:
  enabled: true
  parameter1: value1
```

### Parallel Optimization

```bash
# Use MPI for multi-node clusters
mpirun -np 64 python run_historical_solver.py --mpi

# Or GNU Parallel for single node
parallel python run_historical_solver.py --seed {1} ::: {1..100}
```

### Oracle Cloud Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for full ARM64 setup.

Quick start:
```bash
# Build ARM64 Docker image
docker build -f Dockerfile.arm64 -t universe-sculptor:arm64 .

# Run on Oracle compute
./deploy/oracle_setup.sh
```

---

## Appendix: Keyboard Shortcuts

### TUI Dashboard

| Key | Action |
|-----|--------|
| `q` | Quit |
| `Space` | Pause/Resume |
| `r` | Reset view |
| `s` | Save snapshot |
| `h` | Help |
| `↑/↓` | Scroll |

---

## Getting Help

- **Documentation**: [https://universe-sculptor.readthedocs.io](https://universe-sculptor.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/[USERNAME]/Universe-Sculptor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/[USERNAME]/Universe-Sculptor/discussions)

---

**Happy sculpting!** 🌌
