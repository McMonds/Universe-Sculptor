import numpy as np
import pandas as pd
from astroquery.jplhorizons import Horizons
import spiceypy as spice
import json
import os
import pickle
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - ORACLE - %(message)s')

class Oracle:
    """
    The Oracle: Data Fetcher & Cleaner.
    Sources: Literature eTNOs, DE440 Ephemeris, NASA JPL Horizons.
    ALL REAL DATA - NO PLACEHOLDERS.
    """
    def __init__(self, cache_dir="data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.epoch = 2451545.0  # J2000
        
        # Load DE440 SPICE kernel for high-precision planet ephemerides
        de440_path = 'data/kernels/de440.bsp'
        if os.path.exists(de440_path):
            try:
                spice.furnsh(de440_path)
                logging.info(f"✓ Loaded DE440 kernel: {de440_path}")
            except Exception as e:
                logging.warning(f"DE440 load failed: {e}")

    def fetch_real_etnos(self):
        """
        Fetch REAL eTNO orbital elements from peer-reviewed literature.
        Source: Curated database from Batygin & Brown (2016), Sheppard et al. (2019)
        """
        literature_path = 'data/real/mpc/etnos_literature.json'
        
        if not os.path.exists(literature_path):
            logging.error(f"Real eTNO database not found: {literature_path}")
            return []
        
        with open(literature_path, 'r') as f:
            data = json.load(f)
        
        etnos = data['etnos']
        logging.info(f"✓ Loaded {len(etnos)} REAL eTNOs from literature")
        logging.info(f"  Source: {data['source']}")
        
        return etnos

    def fetch_data(self):
        """
        Fetches REAL state vectors (Barycentric) for simulation.
        Uses literature eTNO data + Horizons for Giants.
        """
        cache_path = os.path.join(self.cache_dir, "solar_system_real.pkl")
        
        if os.path.exists(cache_path):
            logging.info("Loading REAL data from cache...")
            with open(cache_path, 'rb') as f:
                return pickle.load(f)

        logging.info("Fetching REAL data from all sources...")
        
        # Giants: Sun + 4 major planets
        giants = {
            'Sun': '10', 'Jupiter': '599', 'Saturn': '699', 
            'Uranus': '799', 'Neptune': '899'
        }
        
        data = []
        
        # Fetch Giants from Horizons (Barycentric)
        for name, nasa_id in giants.items():
            try:
                obj = Horizons(id=nasa_id, location='@0', epochs=self.epoch)
                vectors = obj.vectors()
                
                vx = vectors['vx'][0] * 365.25
                vy = vectors['vy'][0] * 365.25
                vz = vectors['vz'][0] * 365.25
                
                obj_data = {
                    'name': name,
                    'id': nasa_id,
                    'x': float(vectors['x'][0]),
                    'y': float(vectors['y'][0]),
                    'z': float(vectors['z'][0]),
                    'vx': float(vx),
                    'vy': float(vy),
                    'vz': float(vz),
                    'is_planet': True,
                    'source': 'Horizons@Barycenter'
                }
                data.append(obj_data)
                logging.info(f"  ✓ {name} (Horizons)")
            except Exception as e:
                logging.error(f"Failed to fetch {name}: {e}")

        # Add REAL eTNOs from literature
        etnos = self.fetch_real_etnos()
        for etno in etnos:
            # Convert orbital elements to Cartesian (if needed)
            # For now, store orbital elements - REBOUND can use them directly
            obj_data = {
                'name': etno['name'],
                'id': etno.get('number', etno['name']),
                'a': etno['a'],
                'e': etno['e'],
                'inc': np.radians(etno['i']),  # Convert to radians
                'Omega': np.radians(etno['Node']),
                'omega': np.radians(etno['Peri']),
                'M': np.radians(etno['M']),
                'H': etno.get('H', 0),
                'is_planet': False,
                'source': etno.get('source', 'Literature')
            }
            data.append(obj_data)
            logging.info(f"  ✓ {etno['name']} (a={etno['a']:.1f} AU, Literature)")

        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
        
        logging.info(f"✓ Cached {len(data)} REAL objects")
        return data
