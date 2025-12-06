import sys
import os

def main():
    print("Initializing Project 9th Planet...")
    
    # Check dependencies
    try:
        import rebound
        import textual
        import flask
        import h5py
    except ImportError as e:
        print(f"Error: Missing dependency {e}. Run 'pip install -r requirements.txt'")
        sys.exit(1)

    # Ensure directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    print("Launching Dashboard...")
    # Ensure src is in path
    sys.path.append(os.getcwd())
    
    from src.viz.dashboard import Dashboard
    app = Dashboard()
    app.run()

if __name__ == "__main__":
    main()
