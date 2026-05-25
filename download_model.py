"""
Model Download Script

This script helps download the pre-trained LayoutLMv3 model from external storage.
Update the DOWNLOAD_URL with the actual link to your model files.

Usage:
    python download_model.py
"""

import os
import sys
from pathlib import Path

# ============================================================================
# CONFIGURATION - UPDATE THIS WITH YOUR ACTUAL DOWNLOAD LINK
# ============================================================================

# Option 1: Direct download URL (Google Drive, Dropbox, etc.)
DOWNLOAD_URL = "YOUR_DOWNLOAD_LINK_HERE"

# Option 2: Multiple file URLs
MODEL_FILES = {
    "model.safetensors": "YOUR_MODEL_SAFETENSORS_LINK",
    "tokenizer.json": "YOUR_TOKENIZER_JSON_LINK",
    "training_args.bin": "YOUR_TRAINING_ARGS_LINK",
}

# ============================================================================
# SCRIPT
# ============================================================================

MODEL_DIR = Path("models/layoutlmv3/best")
REQUIRED_FILES = ["model.safetensors", "tokenizer.json", "training_args.bin"]


def check_existing_files():
    """Check if model files already exist."""
    existing = []
    missing = []
    
    for file in REQUIRED_FILES:
        file_path = MODEL_DIR / file
        if file_path.exists():
            existing.append(file)
        else:
            missing.append(file)
    
    return existing, missing


def download_file(url, destination):
    """Download a file from URL to destination."""
    try:
        import requests
        from tqdm import tqdm
        
        print(f"Downloading {destination.name}...")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(destination, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"✓ Downloaded {destination.name}")
        return True
        
    except ImportError:
        print("Error: 'requests' and 'tqdm' packages are required.")
        print("Install them with: pip install requests tqdm")
        return False
    except Exception as e:
        print(f"Error downloading {destination.name}: {e}")
        return False


def verify_installation():
    """Verify the model can be loaded."""
    try:
        print("\nVerifying model installation...")
        from src.ai_extractor import LayoutLMv3Extractor
        
        extractor = LayoutLMv3Extractor()
        print("✓ Model loaded successfully!")
        return True
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return False


def main():
    print("=" * 70)
    print("LayoutLMv3 Model Download Script")
    print("=" * 70)
    
    # Check if model directory exists
    if not MODEL_DIR.exists():
        print(f"Creating model directory: {MODEL_DIR}")
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check existing files
    existing, missing = check_existing_files()
    
    if existing:
        print(f"\n✓ Found existing files: {', '.join(existing)}")
    
    if not missing:
        print("\n✓ All model files are already present!")
        verify_installation()
        return
    
    print(f"\n⚠ Missing files: {', '.join(missing)}")
    
    # Check if download URL is configured
    if DOWNLOAD_URL == "YOUR_DOWNLOAD_LINK_HERE":
        print("\n" + "=" * 70)
        print("ERROR: Download URL not configured!")
        print("=" * 70)
        print("\nPlease update this script with the actual download link:")
        print("1. Open: download_model.py")
        print("2. Update: DOWNLOAD_URL = 'YOUR_DOWNLOAD_LINK_HERE'")
        print("3. Or update: MODEL_FILES dictionary with individual file URLs")
        print("\nAlternatively, you can:")
        print("- Manually download the model files from the shared location")
        print("- Place them in: models/layoutlmv3/best/")
        print("- Or train the model yourself: python src/train_layoutlmv3.py")
        print("\nSee MODEL_SETUP.md for detailed instructions.")
        sys.exit(1)
    
    # Download files
    print("\nStarting download...")
    
    if DOWNLOAD_URL != "YOUR_DOWNLOAD_LINK_HERE":
        # Single archive download
        print(f"Downloading from: {DOWNLOAD_URL}")
        print("\nNote: This script assumes a direct download link.")
        print("For Google Drive/Dropbox, you may need to download manually.")
        print("See MODEL_SETUP.md for instructions.")
    else:
        # Individual file downloads
        success_count = 0
        for filename in missing:
            if filename in MODEL_FILES:
                url = MODEL_FILES[filename]
                if url != "YOUR_DOWNLOAD_LINK_HERE":
                    destination = MODEL_DIR / filename
                    if download_file(url, destination):
                        success_count += 1
        
        if success_count == len(missing):
            print(f"\n✓ Successfully downloaded {success_count} files!")
            verify_installation()
        else:
            print(f"\n⚠ Downloaded {success_count}/{len(missing)} files")
            print("Please check the errors above and try again.")


if __name__ == "__main__":
    main()
