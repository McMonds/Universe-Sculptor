# Quick Start Guide

## Installation Complete ✓

All dependencies have been installed in a virtual environment at `/home/monk/Work/9th Planet/venv/`.

## Running the System

### Option 1: Launch the Dashboard (TUI)
```bash
cd "/home/monk/Work/9th Planet"
./venv/bin/python3 main.py
```

This will open the **Textual Dashboard** where you can:
- Click **"Start Optimization"** to run the Planet 9 search
- Click **"Launch Web Viz"** to start the 3D visualization server

### Option 2: Run the Optimizer Directly
```bash
cd "/home/monk/Work/9th Planet"
./venv/bin/python3 src/optimizer.py
```

This runs the optimization without the TUI (outputs to terminal).

## What Happens

1. **The Oracle** fetches real eTNO data from NASA (or loads from cache)
2. **Stage 1 (Scout)**: Parallel genetic algorithm spawns 15 universes across all CPU cores
3. **Stage 2 (Sharpshooter)**: Nelder-Mead refines the best candidate
4. **Output**: Best Planet 9 parameters (Mass, Semi-major axis, Eccentricity, Inclination, etc.)

## Logs

- Optimizer logs: `logs/optimizer.log`
- Simulation data: `data/simulation.h5` (HDF5 format)
- Cached NASA data: `data/cache/solar_system_barycentric.pkl`

## Expected Runtime

- **Stage 1**: ~10-30 minutes (depends on CPU)
- **Stage 2**: ~20-60 minutes (higher precision)

## Next Steps

To reach full "NASA-Grade":
1. Download WISE Exclusion Map
2. Download Gaia Density Map
3. Implement coordinate transforms for optical constraints
