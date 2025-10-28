"""
Pre-Event Data Extraction Script
=================================

Extracts Arturo building structures for selected Graysky AOIs and transforms
them into the pre-event damage assessment schema (75 columns).

Usage:
    python extract_pre_event_data.py

The script will:
1. Display available Graysky AOIs
2. Prompt user to select an AOI
3. Extract structures within AOI from Arturo data
4. Transform to pre-event schema
5. Save output GeoPackage with 3 layers

Author: Roman Buegler
Created: 2025-10-27
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
ARTURO_DATA_DIR = Path("/Users/romanbuegler/dev/hail_damage/data/final")
AOI_FILE = Path("../input/graysky_suncorp_aois.gpkg")
OUTPUT_DIR = Path("../output")

# Mapping constants
ROOF_SHAPE_MAP = {
    'gable': 'gable',
    'hip': 'hip',
    'flat': 'flat',
    None: 'Unknown'
}

ROOF_MATERIAL_MAP = {
    'metal': 'metal',
    'concrete_tile': 'tile',
    'clay_tile': 'tile',
    'tile': 'tile',
    'solid_concrete': 'membrane',
    'other_material': 'Unknown',
    None: 'Unknown'
}

ROOF_CONDITION_MAP = {
    'good': 4.0,
    'fair': 3.0,
    'poor': 2.0,
    'excellent': 5.0,
    None: 3.0
}

# State boundaries (geographic extents from Arturo data)
# Format: (minx, miny, maxx, maxy)
STATE_BOUNDS = {
    "NSW": (141.883391, -36.120228, 153.636795, -28.165654),
    "VIC": (141.988271, -38.634372, 146.987789, -34.119868),
    "QLD": (145.596151, -28.574471, 153.551443, -16.723084),
    "WA": (115.582252, -33.4476, 116.320862, -31.485581),
    "SA": (137.501566, -35.588245, 140.800519, -32.465986),
    "ACT": (148.973766, -35.480152, 149.231645, -35.139768),
    "TAS": (145.653797, -43.105749, 147.534922, -40.954031),
    "NT": (130.818874, -12.629241, 131.177811, -12.349308),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_aois() -> gpd.GeoDataFrame:
    """Load Graysky AOIs from GeoPackage."""
    logger.info("Loading Graysky AOIs...")
    aois = gpd.read_file(AOI_FILE, layer='graysky_aois')
    logger.info(f"Loaded {len(aois)} AOIs")
    return aois


def display_aois(aois: gpd.GeoDataFrame):
    """Display available AOIs for user selection."""
    print("\n" + "="*80)
    print("AVAILABLE GRAYSKY-SUNCORP AOIs")
    print("="*80)

    for idx, row in aois.iterrows():
        print(f"\n{idx + 1}. {row['event_name']}")
        print(f"   Event ID: {row['event_id']}")
        print(f"   Layer: {row['layer']}")
        print(f"   Collection: {row['collection']}")
        print(f"   Area: {row['area_km2']:.2f} km²")
        print(f"   Avg GSD: {row['avg_gsd']:.4f} m")

    print("\n" + "="*80)


def select_aoi(aois: gpd.GeoDataFrame) -> Optional[pd.Series]:
    """Prompt user to select an AOI."""
    while True:
        try:
            choice = input(f"\nSelect AOI (1-{len(aois)}) or 'q' to quit: ").strip()

            if choice.lower() == 'q':
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(aois):
                selected = aois.iloc[idx]
                print(f"\n✓ Selected: {selected['event_name']}")
                return selected
            else:
                print(f"❌ Please enter a number between 1 and {len(aois)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q' to quit.")


def determine_states(aoi_geometry) -> list:
    """
    Determine which Australian state(s) intersect with the AOI.
    Returns list of states, as AOI may span multiple states.

    Args:
        aoi_geometry: AOI geometry (Shapely geometry)

    Returns:
        List of state codes (e.g., ['NSW'] or ['NSW', 'VIC'])
    """
    from shapely.geometry import box

    aoi_bounds = aoi_geometry.bounds  # (minx, miny, maxx, maxy)
    intersecting_states = []

    for state, state_bounds in STATE_BOUNDS.items():
        # Create bounding box for state
        state_box = box(*state_bounds)

        # Check if AOI intersects with state bounds
        if aoi_geometry.intersects(state_box):
            intersecting_states.append(state)
            logger.info(f"AOI intersects with state: {state}")

    if not intersecting_states:
        # Fallback: find closest state by centroid
        logger.warning("No intersection found, using centroid-based fallback")
        aoi_centroid = aoi_geometry.centroid
        min_dist = float('inf')
        closest_state = None

        for state, (minx, miny, maxx, maxy) in STATE_BOUNDS.items():
            # Use center of state bounds
            state_center = Point((minx + maxx) / 2, (miny + maxy) / 2)
            dist = aoi_centroid.distance(state_center)
            if dist < min_dist:
                min_dist = dist
                closest_state = state

        intersecting_states = [closest_state]
        logger.info(f"Fallback determined state: {closest_state}")

    logger.info(f"Final state list: {intersecting_states}")
    return intersecting_states


def load_arturo_data(state: str, aoi_bounds: tuple) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Load Arturo structures, solar panels, and water heaters for given state and bounds.

    Args:
        state: Australian state code (NSW, VIC, QLD, etc.)
        aoi_bounds: Bounding box (minx, miny, maxx, maxy)

    Returns:
        Tuple of (structures, solar_panels, water_heaters) GeoDataFrames
    """
    arturo_file = ARTURO_DATA_DIR / f"arturo_structuredetails_{state}_full.gpkg"

    if not arturo_file.exists():
        raise FileNotFoundError(f"Arturo data not found: {arturo_file}")

    logger.info(f"Loading Arturo data from: {arturo_file}")
    logger.info(f"Bounding box filter: {aoi_bounds}")

    # Load structures
    logger.info("Loading structures layer...")
    structures = gpd.read_file(arturo_file, layer='structures', bbox=aoi_bounds)
    logger.info(f"Loaded {len(structures)} structures")

    # Load solar panels
    logger.info("Loading solar_panels layer...")
    try:
        solar_panels = gpd.read_file(arturo_file, layer='solar_panels', bbox=aoi_bounds)
        logger.info(f"Loaded {len(solar_panels)} solar panels")
    except Exception as e:
        logger.warning(f"Failed to load solar panels: {e}")
        solar_panels = gpd.GeoDataFrame(columns=['geometry'], crs='EPSG:4326')

    # Load water heaters (pool_heaters)
    logger.info("Loading pool_heaters layer...")
    try:
        water_heaters = gpd.read_file(arturo_file, layer='pool_heaters', bbox=aoi_bounds)
        logger.info(f"Loaded {len(water_heaters)} water heaters")
    except Exception as e:
        logger.warning(f"Failed to load water heaters: {e}")
        water_heaters = gpd.GeoDataFrame(columns=['geometry'], crs='EPSG:4326')

    return structures, solar_panels, water_heaters


def spatial_filter(structures: gpd.GeoDataFrame, aoi_geometry) -> gpd.GeoDataFrame:
    """Filter structures to only those intersecting the AOI."""
    logger.info("Filtering structures within AOI...")

    # Ensure same CRS
    if structures.crs != 'EPSG:4326':
        structures = structures.to_crs('EPSG:4326')

    # Spatial filter
    mask = structures.intersects(aoi_geometry)
    filtered = structures[mask].copy()

    logger.info(f"Filtered to {len(filtered)} structures within AOI")
    return filtered


def check_intersection(geom, gdf: gpd.GeoDataFrame) -> bool:
    """Check if geometry intersects any geometry in GeoDataFrame."""
    if len(gdf) == 0:
        return False
    try:
        return gdf.intersects(geom).any()
    except Exception:
        return False


def transform_to_preevent_schema(
    structures: gpd.GeoDataFrame,
    aoi_metadata: dict,
    solar_panels: gpd.GeoDataFrame,
    water_heaters: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Transform Arturo structures to pre-event schema (75 columns).

    Args:
        structures: Arturo structures GeoDataFrame
        aoi_metadata: Dictionary with AOI metadata
        solar_panels: Solar panels GeoDataFrame
        water_heaters: Water heaters GeoDataFrame

    Returns:
        Transformed GeoDataFrame with 75 columns
    """
    logger.info("Transforming to pre-event schema...")

    # Create spatial index for faster intersection checks
    solar_union = solar_panels.geometry.unary_union if len(solar_panels) > 0 else None
    water_union = water_heaters.geometry.unary_union if len(water_heaters) > 0 else None

    records = []
    total = len(structures)

    for idx, row in structures.iterrows():
        if (idx + 1) % 1000 == 0:
            logger.info(f"Processing {idx + 1}/{total} structures...")

        geom = row.geometry

        # Check solar panel intersection
        has_solar = False
        if solar_union is not None:
            try:
                has_solar = geom.intersects(solar_union)
            except Exception:
                pass

        # Check water heater intersection
        has_water_heater = False
        if water_union is not None:
            try:
                has_water_heater = geom.intersects(water_union)
            except Exception:
                pass

        # Map values
        roof_shape = ROOF_SHAPE_MAP.get(row.get('roof_shape_majority'), 'Unknown')
        roof_material = ROOF_MATERIAL_MAP.get(row.get('roof_material_majority'), 'Unknown')
        roof_condition = ROOF_CONDITION_MAP.get(row.get('roof_condition_general'), 3.0)
        tree_overlap = round(row.get('roof_tree_overlap_pct', 0)) if pd.notna(row.get('roof_tree_overlap_pct')) else 0
        is_primary = 'TRUE' if row.get('is_primary', False) else 'FALSE'

        record = {
            # Core IDs (1-3)
            'BUILDINGS_IDS': row.get('structure_id'),
            'PEID': row.get('structure_id'),
            'PARCELWKT': geom.wkt,

            # Metadata - Building (4-10)
            'B.CAPTURE_PROJECT': row.get('vexcel_collection_name'),
            'METADATAVERSION': '3.90.1',
            'B.LAYERNAME': 'bluesky-ultra-oceania',
            'B.IMAGEID': None,
            'B.CHILD_AOI': row.get('vexcel_collection_name'),
            'B.ORTHOVSNADIR': 'ortho',
            'B.CAMERATECHNOLOGY': 'UltraCam_Osprey_4.1_f120',

            # Metadata - Building Image (11-12)
            'B.IMGDATE': None,
            'B.IMGGSD': aoi_metadata.get('avg_gsd'),

            # Property Features (13-28)
            'POOLAREA': 0.0,
            'TRAMPOLINE': 'FALSE',
            'TRAMPSCR': 0.0,
            'DECK': 'FALSE',
            'DECKSCR': 0.0,
            'POOL': 'FALSE',
            'POOLSCR': 0.0,
            'ENCLOSURE': 'FALSE',
            'ENCLOSUSCR': 0.0,
            'DIVINGBOAR': 'FALSE',
            'DIVINGSCR': 0.0,
            'WATERSLIDE': 'FALSE',
            'WATSLIDSCR': 0.0,
            'PLAYGROUND': 'FALSE',
            'PLAYGSCR': 0.0,
            'SPORTCOURT': 'FALSE',
            'SPORTSCR': 0.0,
            'PRIMARYSTR': is_primary,

            # Roof Attributes (29-40)
            'ROOFTOPGEO': geom.wkt,
            'GROUNDELEV': None,
            'DETECTSCR': 1.0,
            'ROOFSHAPE': roof_shape,
            'ROOFSHASCR': None,
            'ROOFMATERI': roof_material,
            'ROOFMATSCR': 1.0,
            'ROOFCONDIT': roof_condition,
            'ROOFSOLAR': 'SOLAR PANEL' if has_solar else 'NO SOLAR PANEL',
            'ROOFTREE': tree_overlap,

            # Distance Scores (41-48)
            'DST5': None, 'DSB5': None,
            'DST30': None, 'DSB30': None,
            'DST100': None, 'DSB100': None,
            'DST200': None, 'DSB200': None,

            # Damage Assessment (49-57)
            'CATASTROPHESCORE': 0,
            'ROOFCONDIT_MISSINGMATERIALPERCEN': 0.0,
            'ROOFCONDIT_TARPPERCEN': 0.0,
            'ROOFCONDIT_DEBRISPERCENT': 0.0,
            'ROOFCONDIT_DISCOLORDETECT': 'FALSE',
            'ROOFCONDIT_DISCOLORPERCEN': 0.0,
            'ROOFCONDIT_DISCOLORSCORE': 0.0,
            'DAMAGE_LEVEL': None,
            'HISTOSCORE': 0.0,

            # Metadata - Damage Assessment (58-64)
            'CAPTURE_PROJECT': aoi_metadata.get('collection'),
            'LAYERNAME': aoi_metadata.get('layer'),
            'IMAGEID': None,
            'CHILD_AOI': aoi_metadata.get('event_id'),
            'ORTHOVSNADIR': 'ortho',
            'CAMERATECHNOLOGY': 'UltraCam_Osprey_4.1_f120',
            'IMGDATE': None,
            'IMGGSD': aoi_metadata.get('avg_gsd'),

            # Classification Keywords (65-68)
            'DSKWT5': None,
            'DSKWT30': None,
            'DSKWT100': None,
            'DSKWT200': None,

            # Additional Metadata (69-71)
            'task_structures_info': None,
            'structures_count': None,
            'property_id': None,

            # Damage percent (72)
            'ROOFCONDIT_STRUCTURALDAMAGEPERCEN': 0.0,

            # NEW FIELD - Water Heater (73)
            'ROOFWATERHEATER': 'WATER HEATER' if has_water_heater else 'NO WATER HEATER',

            # Geometry (74)
            'geometry': geom
        }

        records.append(record)

    # Create GeoDataFrame
    output = gpd.GeoDataFrame(records, crs='EPSG:4326')

    logger.info(f"Transformation complete: {len(output)} structures, {len(output.columns)} columns")
    return output


def save_output(
    structures: gpd.GeoDataFrame,
    solar_panels: gpd.GeoDataFrame,
    water_heaters: gpd.GeoDataFrame,
    aoi_metadata: dict,
    aoi_geometry
) -> Path:
    """
    Save output GeoPackage with 3 layers.

    Args:
        structures: Transformed structures
        solar_panels: Solar panels within AOI
        water_heaters: Water heaters within AOI
        aoi_metadata: AOI metadata dictionary
        aoi_geometry: AOI geometry for spatial filtering

    Returns:
        Path to output file
    """
    # Create output filename
    event_name = aoi_metadata['event_name'].replace(' ', '_').replace('/', '_').lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = OUTPUT_DIR / f"{event_name}_pre_event_{timestamp}.gpkg"

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving output to: {output_file}")

    # Save main structures layer
    logger.info(f"Saving pre_event_structures layer ({len(structures)} features)...")
    structures.to_file(output_file, driver='GPKG', layer='pre_event_structures')

    # Filter and save solar panels within AOI
    if len(solar_panels) > 0:
        solar_in_aoi = solar_panels[solar_panels.intersects(aoi_geometry)].copy()
        logger.info(f"Saving solar_panels layer ({len(solar_in_aoi)} features)...")
        if len(solar_in_aoi) > 0:
            solar_in_aoi.to_file(output_file, driver='GPKG', layer='solar_panels')
        else:
            logger.warning("No solar panels within AOI - skipping layer")

    # Filter and save water heaters within AOI
    if len(water_heaters) > 0:
        water_in_aoi = water_heaters[water_heaters.intersects(aoi_geometry)].copy()
        logger.info(f"Saving water_heaters layer ({len(water_in_aoi)} features)...")
        if len(water_in_aoi) > 0:
            water_in_aoi.to_file(output_file, driver='GPKG', layer='water_heaters')
        else:
            logger.warning("No water heaters within AOI - skipping layer")

    logger.info(f"✓ Output saved successfully: {output_file}")
    return output_file


def print_summary(structures: gpd.GeoDataFrame, output_file: Path):
    """Print summary statistics."""
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total structures: {len(structures):,}")
    print(f"Total columns: {len(structures.columns)}")
    print(f"\nOutput file: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

    print(f"\nRoof Materials:")
    print(structures['ROOFMATERI'].value_counts().head())

    print(f"\nRoof Shapes:")
    print(structures['ROOFSHAPE'].value_counts())

    print(f"\nSolar Panels:")
    print(structures['ROOFSOLAR'].value_counts())

    print(f"\nWater Heaters:")
    print(structures['ROOFWATERHEATER'].value_counts())

    print(f"\nPrimary Structures:")
    print(structures['PRIMARYSTR'].value_counts())

    print("="*80 + "\n")


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract pre-event building data for Graysky AOIs"
    )
    parser.add_argument(
        '--aoi-index',
        type=int,
        help='AOI index to process (1-based). If not provided, will prompt interactively.'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Load AOIs
        aois = load_aois()

        # Select AOI
        if args.aoi_index:
            if 1 <= args.aoi_index <= len(aois):
                selected_aoi = aois.iloc[args.aoi_index - 1]
                print(f"\n✓ Selected AOI {args.aoi_index}: {selected_aoi['event_name']}")
            else:
                logger.error(f"Invalid AOI index: {args.aoi_index}")
                return 1
        else:
            display_aois(aois)
            selected_aoi = select_aoi(aois)

            if selected_aoi is None:
                logger.info("User cancelled operation")
                return 0

        # Extract AOI metadata
        aoi_metadata = {
            'event_name': selected_aoi['event_name'],
            'event_id': selected_aoi['event_id'],
            'collection': selected_aoi['collection'],
            'layer': selected_aoi['layer'],
            'avg_gsd': selected_aoi['avg_gsd']
        }

        aoi_geometry = selected_aoi['geometry']

        # Determine state(s)
        states = determine_states(aoi_geometry)

        # Load Arturo data from all intersecting states
        aoi_bounds = aoi_geometry.bounds
        all_structures = []
        all_solar_panels = []
        all_water_heaters = []

        for state in states:
            logger.info(f"Loading data for state: {state}")
            structures, solar_panels, water_heaters = load_arturo_data(state, aoi_bounds)
            all_structures.append(structures)
            all_solar_panels.append(solar_panels)
            all_water_heaters.append(water_heaters)

        # Combine data from all states
        import pandas as pd
        structures = pd.concat(all_structures, ignore_index=True) if all_structures else gpd.GeoDataFrame()
        solar_panels = pd.concat(all_solar_panels, ignore_index=True) if all_solar_panels else gpd.GeoDataFrame()
        water_heaters = pd.concat(all_water_heaters, ignore_index=True) if all_water_heaters else gpd.GeoDataFrame()

        logger.info(f"Combined data from {len(states)} state(s): {len(structures)} structures")

        # Spatial filter
        if len(structures) > 0:
            structures = spatial_filter(structures, aoi_geometry)
        else:
            structures = gpd.GeoDataFrame()

        if len(structures) == 0:
            logger.error("No structures found within AOI bounds!")
            return 1

        # Transform to pre-event schema
        output_structures = transform_to_preevent_schema(
            structures, aoi_metadata, solar_panels, water_heaters
        )

        # Save output
        output_file = save_output(
            output_structures, solar_panels, water_heaters,
            aoi_metadata, aoi_geometry
        )

        # Print summary
        print_summary(output_structures, output_file)

        logger.info("✓ Pre-event data extraction completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Error during extraction: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
