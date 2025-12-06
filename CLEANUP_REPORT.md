# Codebase Cleanup Report
**Date**: 2025-12-05
**Status**: Pre-Phase 3 Cleanup

## Analysis Summary

### Project Structure ✅
```
9th Planet/
├── src/
│   ├── physics/           (32K - 4 modules) ✅ ACTIVE
│   ├── validation/        (40K - 4 modules) ✅ ACTIVE
│   ├── observability/     (8K - 1 module)  ✅ ACTIVE
│   ├── constraints/       (8K - 2 modules) ✅ ACTIVE
│   └── viz/              (28K - 5 modules) ✅ ACTIVE
├── deploy/               (3 scripts) ✅ ACTIVE
└── data/                 (13 subdirs) ✅ ACTIVE
```

### Files to REMOVE ❌

1. **`9th.py`** - Empty file (0 bytes)
2. **`test_null_hypothesis.txt`** - Temporary test output
3. **Python cache** - 7,052 `__pycache__` directories (safe to delete)

### Files to KEEP ✅

**Root Scripts** (All Active):
- `main.py` - TUI dashboard entry point
- `run_historical_solver.py` - Historical solver runner
- `download_real_data.py` - Data fetcher
- `fetch_real_etnos.py` - eTNO fetcher
- `generate_maps.py` - HEALPix map generator
- `download_data.sh` - SPICE kernel downloader

**Core Modules** (All Active):
- `src/core.py` - SimulationEngine
- `src/oracle.py` - NASA data loader
- `src/worker.py` - REBOUND wrapper
- `src/judge.py` - TNO clustering evaluator
- `src/optimizer.py` - 3-stage optimizer
- `src/hamiltonian.py` - Conservation monitor
- `src/historical_judge.py` - Historical likelihood
- `src/primordial_optimizer.py` - Birth state search
- `src/time_machine.py` - 4.5 Gyr integrator
- `src/scoring.py` - Improved cost function
- `src/constraints.py` - Tier 5-7 constraints
- `src/validator.py` - Kozai-Lidov check

**Phase 1-2 Modules** (10 modules - All Active):
- `src/physics/solar_mass_loss.py`
- `src/physics/gr_effects.py` 
- `src/physics/planet_migration.py`
- `src/physics/atmospheric_model.py`
- `src/validation/null_hypothesis.py`
- `src/validation/injection_recovery.py`
- `src/validation/model_selection.py`
- `src/validation/uncertainty.py`
- `src/observability/parallax.py`
- `src/constraints/comet_flux.py`

**Visualization** (All Active):
- `src/viz/server.py` - Flask API
- `src/viz/dashboard.py` - Textual TUI
- `src/viz/time_lapse.py` - Video generator
- `src/viz/templates/index.html` - Three.js frontend

**Deployment** (All Active):
- `Dockerfile`, `Dockerfile.arm64`
- `docker-compose.yml`
- `deploy/oracle_setup.sh`
- `deploy/monitor.sh`
- `deploy/sync_results.sh`

**Documentation** (All Active):
- `README.md`
- `QUICKSTART.md`
- `GRAPHS.md`
- `NASA_MODULES_STATUS.md`
- `requirements.txt`

## Cleanup Actions

### 1. Remove Empty/Temporary Files
```bash
rm -f 9th.py
rm -f test_null_hypothesis.txt
```

### 2. Clean Python Cache (Optional - regenerates automatically)
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
```

### 3. Clean Logs (Optional - keep recent)
```bash
# Keep recent logs, remove old ones if needed
ls -lt logs/
```

## Disk Usage Summary

- **Total project**: ~250 MB
- **venv/**: Most space (Python packages)
- **data/**: ~50 MB (SPICE kernels + maps)
- **src/**: ~200 KB (clean, efficient)

## Recommendation

✅ **The codebase is CLEAN and well-organized**
- No duplicate modules found
- All files serve active purposes
- Clear modular structure
- Only minor cleanup needed (2 temp files)

**Action**: Remove `9th.py` and `test_null_hypothesis.txt`, then proceed to Phase 3.
