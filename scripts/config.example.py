"""
Configuration Template for Pre-Event Data Extraction
=====================================================

SETUP INSTRUCTIONS:
1. Copy this file to config.py:
   cp config.example.py config.py

2. Edit config.py and set ARTURO_DATA_DIR to your local data path

3. Ensure your data directory contains the required GeoPackage files

This template shows the default configuration with documentation for each setting.

Author: Roman Buegler
Created: 2025-10-28
"""

from pathlib import Path
import os

# ============================================================================
# DATA PATHS - REQUIRED CONFIGURATION
# ============================================================================

# **IMPORTANT**: Set this to your local Arturo data directory
#
# Default is ../data (relative to scripts/ directory), which means:
#   pre_event_data/data/
#
# This directory should contain state-level GeoPackage files:
#   - arturo_structuredetails_{STATE}_full.gpkg
#   - arturo_propertydetails_{STATE}_full.gpkg
#   - arturo_solarpanels_{STATE}_full.gpkg
#   - arturo_waterheaters_{STATE}_full.gpkg
#
# Where {STATE} is: NSW, VIC, QLD, WA, SA, TAS, NT, ACT
#
# You can also set this via environment variable:
#   export ARTURO_DATA_DIR=/path/to/your/data
#
# Alternative example paths:
#   Linux/Mac: Path("/mnt/data/arturo") or Path("/home/user/arturo_data")
#   Windows:   Path("C:/Data/arturo") or Path("D:/projects/arturo_data")
#
# Default (recommended): Use ../data directory in the repository
ARTURO_DATA_DIR = Path(os.environ.get(
    'ARTURO_DATA_DIR',
    '../data'  # Default: relative path to data/ directory
)).resolve()  # Convert to absolute path

# Input: Graysky AOI definitions (relative to scripts directory)
AOI_FILE = Path("../input/graysky_suncorp_aois.gpkg")

# Output: Where to save extracted pre-event data (relative to scripts directory)
OUTPUT_DIR = Path("../output")

# ============================================================================
# PROCESSING OPTIONS
# ============================================================================

# Building footprint regularization (REQUIRED - do not disable)
# Requires: pip install git+https://github.com/DPIRD-DMA/Building-Regulariser.git
# Effect: Applies orthogonal edge alignment (0°, 45°, 90°, 135°) to building footprints
#         Reduces vertex count by ~3 per building while preserving area (<3% change)
ENABLE_REGULARIZATION = True

# Regularization parameters
REGULARIZATION_PARAMS = {
    'parallel_threshold': 1.0,          # Merge parallel edges within N meters
    'simplify_tolerance': 0.5,          # Simplify vertices within N meters
    'allow_45_degree': True,            # Allow 45° diagonal edges
    'diagonal_threshold_reduction': 15, # Threshold for diagonal detection (degrees)
    'allow_circles': False,             # Don't preserve circular features as circles
    'num_cores': 0,                     # 0 = use all available CPU cores
}

# Enable MFD (Multi-Family Dwelling) deduplication
# Effect: Removes duplicate structures that span multiple property parcels
#         Keeps only the structure-property pair with largest geometry overlap
#         Typically removes ~7.5% of structures (MFDs, row houses, townhouses)
ENABLE_MFD_DEDUPLICATION = True

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration before running extraction."""
    errors = []

    if not ARTURO_DATA_DIR.exists():
        errors.append(f"ARTURO_DATA_DIR does not exist: {ARTURO_DATA_DIR}")
        errors.append("  Please set this to your local Arturo data directory in config.py")

    if not AOI_FILE.exists():
        errors.append(f"AOI_FILE does not exist: {AOI_FILE}")

    # Check for at least one state data file
    if ARTURO_DATA_DIR.exists():
        state_files = list(ARTURO_DATA_DIR.glob("arturo_structuredetails_*_full.gpkg"))
        if not state_files:
            errors.append(f"No Arturo state GeoPackage files found in: {ARTURO_DATA_DIR}")
            errors.append("  Expected files: arturo_structuredetails_{{STATE}}_full.gpkg")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True

if __name__ == "__main__":
    """Quick validation check - run with: python config.py"""
    try:
        validate_config()
        print("✓ Configuration is valid")
        print(f"  Data directory: {ARTURO_DATA_DIR}")
        print(f"  AOI file: {AOI_FILE}")
        print(f"  Output directory: {OUTPUT_DIR}")
        print(f"  Regularization: {'enabled' if ENABLE_REGULARIZATION else 'disabled'}")
        print(f"  MFD deduplication: {'enabled' if ENABLE_MFD_DEDUPLICATION else 'disabled'}")
    except ValueError as e:
        print(f"✗ Configuration error:\n{e}")
        print("\nPlease edit config.py and set ARTURO_DATA_DIR to your data path")
        exit(1)
