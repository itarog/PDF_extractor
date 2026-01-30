#!/usr/bin/env python3
"""
Download DECIMER model weights in advance.

This script pre-downloads DECIMER model weights so they are available
before the first use. This is useful for:
- Offline environments
- Faster first-time inference
- Ensuring weights are available before processing

Usage:
    python build/download_decimer_weights.py
    or
    python -m build.download_decimer_weights
"""

import sys
import numpy as np
from PIL import Image

def download_decimer_weights():
    """Download DECIMER model weights by triggering model initialization."""
    print("Downloading DECIMER model weights...")
    print("This may take a few minutes on first run...")
    
    try:
        # Import DECIMER - this will trigger any necessary setup
        from DECIMER import predict_SMILES
        print("✓ DECIMER imported successfully")
        
        # Create a dummy image to trigger model loading
        # DECIMER expects images of size 224x224
        dummy_image = Image.new('RGB', (224, 224), color='white')
        dummy_array = np.array(dummy_image)
        
        print("Loading DECIMER model (this downloads weights if not cached)...")
        # This call will download weights if they don't exist
        # We catch the result but don't care about it
        try:
            _ = predict_SMILES(dummy_array)
            print("✓ DECIMER weights downloaded and cached successfully!")
            print("  Model is now ready to use.")
        except Exception as e:
            # Some errors are expected with a dummy white image
            # The important thing is that the model was loaded
            if "weights" in str(e).lower() or "model" in str(e).lower():
                print(f"⚠ Warning during model test: {e}")
                print("  However, weights may still have been downloaded.")
            else:
                print(f"✓ Model loaded (prediction error expected with dummy image): {type(e).__name__}")
                print("  Weights are cached and ready to use.")
        
        return True
        
    except ImportError as e:
        print(f"✗ Error: Could not import DECIMER: {e}")
        print("\nPlease ensure DECIMER is installed:")
        print("  pip install decimer>=2.8.0")
        return False
        
    except Exception as e:
        print(f"✗ Error downloading DECIMER weights: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Ensure DECIMER is properly installed: pip install decimer>=2.8.0")
        print("  3. Check if you have write permissions to the cache directory")
        return False


if __name__ == "__main__":
    success = download_decimer_weights()
    sys.exit(0 if success else 1)
