# Universe Sculptor: The Inverse Solver

**A Pure Mathematical Simulation of Cosmic History**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![NASA NPR 7150.2D](https://img.shields.io/badge/NASA-NPR%207150.2D-red.svg)](https://nodis3.gsfc.nasa.gov/displayDir.cfm?t=NPR&c=7150&s=2D)

> **"Don't guess the past. Solve for it."**

---

## 🌌 The Inverse Approach

Most astronomical simulations work **forward**: they set initial parameters, run a billion-year evolution, and hope the result looks like reality. It's a game of trial and error.

**Universe Sculptor is different.**

We use an **Inverse Method** (Boundary Value Problem). Instead of guessing initial conditions, we start with **real, hard data** from today—the "weird symptoms" of our solar system—and mathematically solve backwards to find the cause.

### Forward vs. Inverse

| Traditional Simulation (Forward) | Universe Sculptor (Inverse) |
|----------------------------------|-----------------------------|
| **Input**: Guessed initial parameters | **Input**: Real observed data (Symptoms) |
| **Process**: Evolve forward in time | **Process**: Solve backwards / Optimize |
| **Output**: "Does this look right?" | **Output**: "Here is exactly what happened." |
| **Method**: Monte Carlo / Brute Force | **Method**: Mathematical Optimization |

---

## 🕵️ Case Study: Hunting Planet 9

The outer solar system exhibits strange symptoms:
1.  **Clustering**: TNOs are huddled together in space.
2.  **Detachment**: Some objects are pulled away from Neptune.
3.  **High Inclination**: Objects orbiting perpendicular to the solar system.

**The Traditional Way**:
*"Let's put a planet here and see what happens in 4 billion years... No? Try there... No?"*

**The Universe Sculptor Way**:
*"Here are the symptoms. Mathematically reconstruct the gravitational history that **must** have existed to cause this specific scarring on the Kuiper Belt."*

We treat the solar system as a crime scene and reconstruct the event from the evidence.

---

## 🧮 Pure Mathematical Simulation

This is not a video game engine. It is a rigorous physics solver built on:

-   **Real Data Integration**: Direct ingestion of NASA JPL Horizons ephemerides, Gaia DR3 star maps, and WISE infrared data.
-   **Hamiltonian Mechanics**: Symplectic integrators (WHFast) that conserve energy to 1 part in 10⁹ over billions of years.
-   **Bayesian Inference**: We don't just give an answer; we give the mathematical probability (sigma) of that answer being true.

---

## 🚀 Key Capabilities

### 1. The Time Machine
Integrate solar system dynamics **backward** for 4.5 billion years, accounting for:
-   Solar Mass Loss (The sun was heavier in the past)
-   Galactic Tides (The galaxy's pull changes as we orbit the Milky Way)
-   Stellar Flybys (Random stars passing near the sun)

### 2. The Diagnostic Engine
Input a set of "symptoms" (observational constraints), and the system optimizes the hidden parameters (e.g., Planet 9's mass and orbit) to explain them.

### 3. NASA-Grade Physics
Includes 26 implemented physics modules:
-   General Relativity (Schwarzschild precession)
-   Giant Planet Migration (Nice Model)
-   Tidal Heating & Pebble Accretion
-   ...and more.

---

## 📊 Current Status

**Implementation Progress**: 26/45 Modules (58%)

-   ✅ **Core Physics**: Solved & Verified
-   ✅ **Real Data Pipeline**: Connected to NASA/MPC APIs
-   ✅ **Inverse Solver**: Operational for Planet 9 search
-   🚧 **Upcoming**: Phase 4-13 (Exotic physics, Dark Matter effects)

---

## 🛠️ Quick Start

```bash
# Clone the solver
git clone https://github.com/[USERNAME]/Universe-Sculptor.git
cd Universe-Sculptor

# Install dependencies
pip install -r requirements.txt

# Download the "Symptoms" (Real NASA Data)
./download_data.sh

# Run the Inverse Solver
# "Find the planet that causes these TNO clusters"
python run_historical_solver.py --inverse --target planet9
```

---

## 📄 License & Compliance

-   **License**: MIT (Open Source)
-   **Compliance**: Developed in accordance with NASA NPR 7150.2D software engineering standards.

---

*"We are not simulating a game. We are solving the equation of our history."*
