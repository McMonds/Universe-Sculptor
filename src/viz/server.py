from flask import Flask, render_template, jsonify
import h5py
import numpy as np
import os

app = Flask(__name__)
DATA_PATH = "data/simulation.h5"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No data found. Run simulation first."})
    
    try:
        with h5py.File(DATA_PATH, 'r') as f:
            # Read all positions: [Time, Particle, 3]
            # For a large file, we should stream or downsample.
            # For demo, we send the whole thing (if small) or just the last N frames.
            # Let's send a strided version for smoothness vs bandwidth.
            
            positions = f["positions"][:]
            times = f["time"][:]
            
            # Convert to list for JSON
            # Structure: { "times": [...], "frames": [ [[x,y,z], [x,y,z]...], ... ] }
            return jsonify({
                "times": times.tolist(),
                "frames": positions.tolist()
            })
    except Exception as e:
        return jsonify({"error": str(e)})

def run_server():
    app.run(debug=True, port=5000, use_reloader=False)

if __name__ == '__main__':
    run_server()
