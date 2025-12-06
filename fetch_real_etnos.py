#!/usr/bin/env python3
"""
Fetch REAL eTNO data from Minor Planet Center
Using direct API queries for known extreme TNOs
"""
from astroquery.mpc import MPC
import pandas as pd
import json
import os

print("=== Fetching REAL eTNO Data from MPC ===\n")

# List of well-studied extreme TNOs from literature
# Source: Batygin & Brown (2016), Trujillo & Sheppard (2014)
known_etnos = [
    '90377',   # Sedna
    '541132',  # Leleākūhonua (2015 TG387)
    '474640',  # 2004 VN112
    '2012 VP113',  # Biden
    '2013 RF98',   # Drac
    '2007 TG422',
    '2010 GB174',
    '2013 FT28',
    '2015 KG163',
    '2015 RX245',
    '2015 GT50',
    '2016 QV89',
]

etnos_data = []

for name in known_etnos:
    try:
        print(f"Querying MPC for {name}...")
        result = MPC.query_object('asteroid', designation=name)
        
        if result is not None and len(result) > 0:
            obj = result[0]
            # Extract orbital elements
            data = {
                'name': name,
                'designation': str(obj['designation']) if 'designation' in obj.colnames else name,
                'a': float(obj['semimajor_axis']) if 'semimajor_axis' in obj.colnames else None,
                'e': float(obj['eccentricity']) if 'eccentricity' in obj.colnames else None,
                'i': float(obj['inclination']) if 'inclination' in obj.colnames else None,
                'Node': float(obj['ascending_node']) if 'ascending_node' in obj.colnames else None,
                'Peri': float(obj['argument_of_perihelion']) if 'argument_of_perihelion' in obj.colnames else None,
                'M': float(obj['mean_anomaly']) if 'mean_anomaly' in obj.colnames else None,
                'H': float(obj['absolute_magnitude']) if 'absolute_magnitude' in obj.colnames else None,
            }
            
            if data['a'] and data['a'] > 150:  # Verify it's an eTNO
                etnos_data.append(data)
                print(f"  ✓ {name}: a={data['a']:.1f} AU, e={data['e']:.3f}")
            else:
                print(f"  ✗ {name}: Not an eTNO (a={data['a']})")
        else:
            print(f"  ✗ {name}: No data found")
            
    except Exception as e:
        print(f"  ✗ {name}: Error - {e}")

print(f"\n✓ Successfully fetched {len(etnos_data)} eTNOs")

# Save to file
os.makedirs('data/real/mpc', exist_ok=True)
with open('data/real/mpc/etnos_real.json', 'w') as f:
    json.dump(etnos_data, f, indent=2)

print(f"✓ Saved to data/real/mpc/etnos_real.json")
print(f"\neTNO List:")
for obj in etnos_data:
    q = obj['a'] * (1 - obj['e'])
    print(f"  {obj['name']}: a={obj['a']:.1f} AU, e={obj['e']:.3f}, q={q:.1f} AU")
