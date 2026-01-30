#!/usr/bin/env python3
"""
Helper script to start Label Studio server.
Run this before running run_label_studio.py
"""
import subprocess
import sys
import os
import time

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def check_label_studio_running(url='http://localhost:8080'):
    """Check if Label Studio is already running"""
    if not HAS_REQUESTS:
        return False  # Can't check without requests
    try:
        response = requests.get(url, timeout=2)
        return True
    except:
        return False

def start_label_studio():
    """Start Label Studio server"""
    print("Checking if Label Studio is installed...")
    
    # Try to import label-studio (this is optional, we'll try to run it anyway)
    try:
        import label_studio
        print("✓ Label Studio package found")
    except ImportError:
        print("⚠ Label Studio package not found in Python, but will try to run command anyway")
    
    # Check if already running
    if check_label_studio_running():
        print("✓ Label Studio is already running at http://localhost:8080")
        print("  You can access it in your browser at: http://localhost:8080")
        return True
    
    print("\nStarting Label Studio server...")
    print("This will open Label Studio in your browser.")
    print("Press Ctrl+C to stop the server.\n")
    
    # Set required environment variables for local file serving
    env = os.environ.copy()
    env['LOCAL_FILES_SERVING_ENABLED'] = 'true'
    # Also set the document root to the current drive root (Z:\ in this case)
    # This allows Label Studio to serve files from the Z: drive
    current_drive = os.path.splitdrive(os.getcwd())[0] + '\\'
    env['LOCAL_FILES_DOCUMENT_ROOT'] = current_drive
    
    print(f"✓ Setting LOCAL_FILES_SERVING_ENABLED=true")
    print(f"✓ Setting LOCAL_FILES_DOCUMENT_ROOT={current_drive}")
    print()
    
    try:
        # Try different ways to start Label Studio with environment variables
        # First try: label-studio command
        try:
            subprocess.run(["label-studio"], env=env, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            # Second try: python -m label_studio
            try:
                subprocess.run([sys.executable, "-m", "label_studio"], env=env, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Third try: label_studio command directly
                subprocess.run([sys.executable, "-c", "import label_studio; label_studio.main()"], env=env, check=True)
    except KeyboardInterrupt:
        print("\n\nLabel Studio server stopped.")
        return True
    except Exception as e:
        print(f"\n✗ Error starting Label Studio: {e}")
        print("\nTroubleshooting:")
        print("  1. Install Label Studio: pip install label-studio")
        print("  2. Try running manually:")
        print("     label-studio")
        print("     OR")
        print("     python -m label_studio")
        return False

if __name__ == "__main__":
    start_label_studio()

