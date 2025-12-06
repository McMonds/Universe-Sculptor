#!/usr/bin/env python3
"""
Planet 9 Historical Solver - Main Entry Point
Optimizes Planet 9's birth state 4.5 billion years ago.

Usage:
    python run_historical_solver.py --scenario rogue_capture --generations 100
"""
import argparse
import logging
import json
import os
from datetime import datetime
from src.primordial_optimizer import PrimordialOptimizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/historical_solver.log'),
        logging.StreamHandler()
    ]
)

def main():
    parser = argparse.ArgumentParser(description='Planet 9 Historical Solver')
    parser.add_argument('--scenario', type=str, default='rogue_capture',
                       choices=['rogue_capture', 'native_ejection'],
                       help='Birth scenario: rogue_capture or native_ejection')
    parser.add_argument('--generations', type=int, default=50,
                       help='Number of optimization generations (default: 50)')
    parser.add_argument('--population', type=int, default=15,
                       help='Population size for genetic algorithm (default: 15)')
    parser.add_argument('--workers', type=int, default=-1,
                       help='Number of parallel workers (-1 = all cores)')
    parser.add_argument('--output', type=str, default='results/best_birth_state.json',
                       help='Output file for best solution')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    logging.info("="*70)
    logging.info("PLANET 9 HISTORICAL SOLVER")
    logging.info("="*70)
    logging.info(f"Scenario: {args.scenario}")
    logging.info(f"Generations: {args.generations}")
    logging.info(f"Population: {args.population}")
    logging.info(f"Parallel Workers: {args.workers if args.workers > 0 else 'ALL'}")
    logging.info("="*70)
    
    # Create optimizer
    optimizer = PrimordialOptimizer(scenario=args.scenario)
    
    # Run optimization
    try:
        best_state = optimizer.run(
            max_generations=args.generations,
            population_size=args.population,
            workers=args.workers
        )
        
        # Save results
        result = {
            'timestamp': datetime.now().isoformat(),
            'scenario': args.scenario,
            'generations': args.generations,
            'best_state': best_state
        }
        
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        
        logging.info(f"\n✓ Results saved to: {args.output}")
        logging.info(f"✓ Best cost: {best_state['cost']:.2f}")
        
        # Print summary
        print("\n" + "="*70)
        print("OPTIMIZATION COMPLETE")
        print("="*70)
        print(f"Best Birth State Found:")
        print(f"  Position: ({best_state['x0']:.1f}, {best_state['y0']:.1f}, {best_state['z0']:.1f}) AU")
        print(f"  Velocity: ({best_state['vx0']:.2f}, {best_state['vy0']:.2f}, {best_state['vz0']:.2f}) AU/yr")
        print(f"  Mass: {best_state['m']*333000:.0f} Earth masses")
        print(f"  Final Cost: {best_state['cost']:.2f}")
        print(f"\nResults: {args.output}")
        print("="*70)
        
        return 0
        
    except KeyboardInterrupt:
        logging.warning("\n\nOptimization interrupted by user")
        return 1
    except Exception as e:
        logging.error(f"\n\nOptimization failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
