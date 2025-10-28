"""
Pre-Event Data Extraction Script (with Property Integration & Regularization)
==============================================================================

Extracts Arturo building structures AND property data for selected Graysky AOIs
and transforms them into the pre-event damage assessment schema (75 columns).

Features:
- Geographic state detection with multi-state support
- Property data integration (true PARCELWKT from property boundaries)
- Property features (pools, decks, trampolines, enclosures, sport courts)
- MFD duplicate removal (structures spanning multiple parcels)
- Building footprint regularization (orthogonal edge alignment)
- Solar panel and water heater detection
- 75-column output schema

Workflow:
1. Load Arturo structures, properties, solar panels, water heaters
2. Spatial filtering within AOI
3. Join structures with properties (on parcel_id)
4. Remove MFD duplicates (keep best overlap)
5. Regularize building footprints (orthogonal alignment)
6. Transform to 75-column schema
7. Save output GeoPackage + metadata JSON

Usage:
    python extract_pre_event_data.py [--aoi-index N] [--verbose]

Author: Roman Buegler
Created: 2025-10-27
Updated: 2025-10-28 (Deduplication & Regularization)
"""

import argparse
import logging
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Polygon

# Suppress warnings
warnings.filterwarnings('ignore', message='Regularized polygon has low IoU')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='extract_pre_event_data')

# Configure logging BEFORE importing config (to avoid NameError)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from config import (
        ARTURO_DATA_DIR,
        KML_INPUT_DIR,
        OUTPUT_DIR,
        VDP_USERNAME,
        VDP_PASSWORD,
        ENABLE_REGULARIZATION,
        REGULARIZATION_PARAMS,
        ENABLE_MFD_DEDUPLICATION,
        validate_config
    )
    logger.info(f"Loaded configuration from config.py")
    logger.info(f"  Data directory: {ARTURO_DATA_DIR}")
except ImportError:
    logger.error("config.py not found! Please create it from config.example.py")
    logger.error("See README.md for setup instructions")
    sys.exit(1)

# Import Vexcel API client
try:
    import os
    vexcel_skill_path = os.path.expanduser('~/.config/claude-code/skills/vexcel_ortho_skill')
    sys.path.insert(0, vexcel_skill_path)
    from vexcel_api import VexcelClient, VexcelAuthError, VexcelAPIError
    VEXCEL_API_AVAILABLE = True
    logger.info("Vexcel API client imported successfully")
except ImportError as e:
    logger.warning(f"Could not import VexcelClient: {e}")
    logger.warning("API collections will not be available. Only local KML files will be used.")
    VEXCEL_API_AVAILABLE = False

# Import building regularization library
try:
    from buildingregulariser import regularize_geodataframe
    REGULARIZATION_AVAILABLE = True
except ImportError:
    logger.warning("Building regularization library not available. Install with: pip install git+https://github.com/DPIRD-DMA/Building-Regulariser.git")
    REGULARIZATION_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

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
# HELPER FUNCTIONS - AOI MANAGEMENT
# ============================================================================

def load_kml_aois() -> List[Dict]:
    """
    Load AOIs from KML files in the input directory.

    Returns:
        List of dicts with keys: 'name', 'source_type', 'source_path'
    """
    kml_aois = []

    if not KML_INPUT_DIR.exists():
        logger.warning(f"KML input directory does not exist: {KML_INPUT_DIR}")
        return kml_aois

    kml_files = list(KML_INPUT_DIR.glob("*.kml"))

    if not kml_files:
        logger.info("No KML files found in input directory")
        return kml_aois

    logger.info(f"Found {len(kml_files)} KML file(s) in input directory")

    for kml_file in kml_files:
        try:
            # Read KML file
            gdf = gpd.read_file(kml_file, driver='KML')

            if len(gdf) == 0:
                logger.warning(f"Empty KML file: {kml_file.name}")
                continue

            # Process each placemark in the KML file
            # Only include Polygons and MultiPolygons (skip Points, Lines, etc.)
            for idx, row in gdf.iterrows():
                geom = row.geometry
                geom_type = geom.geom_type

                # Skip non-polygon geometries (Points, LineStrings, etc.)
                if geom_type not in ['Polygon', 'MultiPolygon']:
                    logger.debug(f"  Skipping {geom_type} geometry: {row.get('Name', 'Unnamed')}")
                    continue

                # Extract name from placemark or use filename
                if 'Name' in row and pd.notna(row['Name']):
                    name = row['Name']
                else:
                    name = f"{kml_file.stem}_{idx}"

                kml_aois.append({
                    'name': name,
                    'source_type': 'KML',
                    'source_path': str(kml_file),
                    'geometry': geom
                })

                logger.info(f"  Loaded KML: {name} ({geom_type})")

        except Exception as e:
            logger.warning(f"Failed to read KML file {kml_file.name}: {e}")
            continue

    return kml_aois


def load_api_collections() -> List[Dict]:
    """
    Load collections from Vexcel API using VexcelClient.

    Queries Graysky layers for Australia/New Zealand:
    - graysky, graysky-suncorp (post-event damage assessment)

    Returns:
        List of dicts with keys: 'collection_id', 'name', 'source_type', 'layer', 'geometry'
    """
    if not VEXCEL_API_AVAILABLE:
        logger.info("Vexcel API not available (VexcelClient not imported)")
        return []

    if not VDP_USERNAME or not VDP_PASSWORD:
        logger.info("VDP credentials not set. Skipping API collections.")
        return []

    # Australia/New Zealand bounding box WKT (extended to include NZ)
    australia_nz_wkt = (
        "POLYGON ((103.886629 -49.037847, 183.691316 -49.037847, "
        "183.691316 -5.440991, 103.886629 -5.440991, 103.886629 -49.037847))"
    )

    # Layers to query - ONLY Graysky layers (post-event damage assessment)
    layers_to_query = [
        "graysky",
        "graysky-suncorp"
    ]

    try:
        # Initialize and authenticate client
        client = VexcelClient()
        client.authenticate()
        logger.info("✓ Vexcel API authenticated successfully")

        api_aois = []
        seen_collections = set()  # Deduplicate by collection name

        # Query each layer
        for layer in layers_to_query:
            try:
                logger.debug(f"Querying layer: {layer}")
                geojson_response = client.get_collections(
                    wkt=australia_nz_wkt,
                    layer=layer,
                    max_records=10000
                )

                features = geojson_response.get('features', [])
                logger.info(f"  Found {len(features)} collections in layer '{layer}'")

                # Process features
                for feature in features:
                    props = feature.get('properties', {})
                    collection_name = props.get('collection', '')

                    # Deduplicate
                    if not collection_name or collection_name in seen_collections:
                        continue

                    seen_collections.add(collection_name)

                    # Extract geometry
                    from shapely.geometry import shape as shapely_shape
                    geometry = None
                    if 'geometry' in feature and feature['geometry']:
                        geometry = shapely_shape(feature['geometry'])

                    api_aois.append({
                        'collection_id': collection_name,
                        'name': props.get('pretty-name', collection_name),
                        'source_type': 'API',
                        'layer': props.get('layer', layer),
                        'source_path': None,
                        'geometry': geometry  # Pre-loaded geometry
                    })

            except Exception as e:
                logger.warning(f"Failed to query layer {layer}: {e}")
                continue

        logger.info(f"Loaded {len(api_aois)} unique collections from Vexcel API")
        return api_aois

    except Exception as e:
        logger.error(f"Failed to load collections from API: {e}")
        return []


def load_all_aois() -> List[Dict]:
    """
    Load all available AOIs from API and KML files.

    Returns:
        Numbered list of AOIs with metadata
    """
    logger.info("Loading AOIs from all sources...")

    all_aois = []

    # Load from API
    api_aois = load_api_collections()
    all_aois.extend(api_aois)

    # Load from KML files
    kml_aois = load_kml_aois()
    all_aois.extend(kml_aois)

    if not all_aois:
        logger.error("No AOIs found! Please either:")
        logger.error("  1. Set VEXCEL_API_KEY to fetch collections from API, or")
        logger.error("  2. Place KML files in the input directory")
        sys.exit(1)

    logger.info(f"Total AOIs available: {len(all_aois)}")
    return all_aois


def display_aois(aois: List[Dict]):
    """Display available AOIs in a numbered list."""
    print("\n" + "="*80)
    print("AVAILABLE AOIs")
    print("="*80)
    print(f"{'#':<4} {'Name':<40} {'Source'}")
    print("-"*80)

    for idx, aoi in enumerate(aois, 1):
        name = aoi['name'][:38]  # Truncate long names
        source = aoi['source_type']

        # Add collection ID for API sources
        if source == 'API' and 'collection_id' in aoi:
            display_name = f"{name} ({aoi['collection_id']})"[:38]
        else:
            display_name = name

        print(f"{idx:<4} {display_name:<40} [{source}]")

    print("="*80 + "\n")


def select_aoi_interactive(aois: List[Dict]) -> int:
    """Prompt user to select an AOI."""
    display_aois(aois)

    while True:
        try:
            selection = input(f"Select AOI number (1-{len(aois)}) or 'q' to quit: ").strip()

            if selection.lower() == 'q':
                print("Exiting...")
                sys.exit(0)

            aoi_index = int(selection) - 1

            if 0 <= aoi_index < len(aois):
                return aoi_index
            else:
                print(f"❌ Invalid selection. Please enter a number between 1 and {len(aois)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


def get_aoi_geometry(aoi: Dict) -> gpd.GeoDataFrame:
    """
    Get geometry for selected AOI.

    Geometry is already pre-loaded for both API and KML sources.

    Returns:
        GeoDataFrame with AOI geometry
    """
    if 'geometry' not in aoi or aoi['geometry'] is None:
        logger.error(f"No geometry found for AOI: {aoi['name']}")
        sys.exit(1)

    # Create GeoDataFrame from pre-loaded geometry
    gdf = gpd.GeoDataFrame(
        [{'name': aoi['name'], 'collection_id': aoi.get('collection_id', aoi['name'])}],
        geometry=[aoi['geometry']],
        crs='EPSG:4326'
    )

    return gdf


def get_aoi_metadata(aoi: Dict, geometry) -> Dict:
    """
    Extract metadata from AOI.

    Args:
        aoi: AOI dict from load_all_aois()
        geometry: Shapely geometry

    Returns:
        Dict with metadata
    """
    # Calculate area
    # Convert to local projection for accurate area calculation
    gdf_temp = gpd.GeoDataFrame([{}], geometry=[geometry], crs='EPSG:4326')
    gdf_utm = gdf_temp.to_crs('+proj=utm +zone=55 +south +datum=WGS84')  # Rough UTM for AU
    area_km2 = gdf_utm.geometry.area.iloc[0] / 1_000_000

    return {
        'event_id': aoi.get('collection_id', aoi['name']),
        'event_name': aoi['name'],
        'collection': aoi.get('collection_id', aoi['name']),
        'layer': 'pre_event_structures',
        'avg_gsd': 0.0,  # Not available from API/KML
        'area_km2': area_km2
    }


# ============================================================================
# HELPER FUNCTIONS - STATE DETECTION
# ============================================================================

def determine_states(aoi_geometry) -> List[str]:
    """
    Determine which Australian state(s) the AOI intersects with.

    Uses geographic intersection with state bounding boxes.
    Supports multi-state AOIs.

    Args:
        aoi_geometry: AOI geometry (Shapely polygon/multipolygon)

    Returns:
        List of state codes (e.g., ['NSW', 'VIC'])
    """
    intersecting_states = []

    for state, bounds in STATE_BOUNDS.items():
        state_box = box(*bounds)
        if aoi_geometry.intersects(state_box):
            intersecting_states.append(state)
            logger.info(f"AOI intersects with state: {state}")

    if not intersecting_states:
        logger.warning("No state intersection found! AOI may be outside Australia.")

    return intersecting_states


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_arturo_data(states: List[str], aoi_bounds: tuple) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Load Arturo structure data for given state(s).

    Args:
        states: List of state codes (e.g., ['NSW', 'VIC'])
        aoi_bounds: Bounding box tuple (minx, miny, maxx, maxy)

    Returns:
        Tuple of (structures, solar_panels, water_heaters) GeoDataFrames
    """
    all_structures = []
    all_solar_panels = []
    all_water_heaters = []

    for state in states:
        arturo_file = ARTURO_DATA_DIR / f"arturo_structuredetails_{state}_full.gpkg"

        if not arturo_file.exists():
            logger.warning(f"Arturo data not found for {state}: {arturo_file}")
            continue

        logger.info(f"Loading Arturo structure data from: {state}")

        # Load structures
        try:
            structures = gpd.read_file(arturo_file, layer='structures', bbox=aoi_bounds)
            logger.info(f"  Loaded {len(structures):,} structures from {state}")
            all_structures.append(structures)
        except Exception as e:
            logger.error(f"  Failed to load structures from {state}: {e}")
            continue

        # Load solar panels
        try:
            solar_panels = gpd.read_file(arturo_file, layer='solar_panels', bbox=aoi_bounds)
            logger.info(f"  Loaded {len(solar_panels):,} solar panels from {state}")
            all_solar_panels.append(solar_panels)
        except Exception as e:
            logger.warning(f"  No solar panels for {state}: {e}")

        # Load water heaters (pool_heaters)
        try:
            water_heaters = gpd.read_file(arturo_file, layer='pool_heaters', bbox=aoi_bounds)
            logger.info(f"  Loaded {len(water_heaters):,} water heaters from {state}")
            all_water_heaters.append(water_heaters)
        except Exception as e:
            logger.warning(f"  No water heaters for {state}: {e}")

    # Combine all data
    if not all_structures:
        raise ValueError("No structure data loaded from any state")

    structures_combined = pd.concat(all_structures, ignore_index=True) if len(all_structures) > 1 else all_structures[0]
    solar_panels_combined = pd.concat(all_solar_panels, ignore_index=True) if all_solar_panels else gpd.GeoDataFrame(columns=['geometry'], crs='EPSG:4326')
    water_heaters_combined = pd.concat(all_water_heaters, ignore_index=True) if all_water_heaters else gpd.GeoDataFrame(columns=['geometry'], crs='EPSG:4326')

    logger.info(f"Combined: {len(structures_combined):,} structures, {len(solar_panels_combined):,} solar panels, {len(water_heaters_combined):,} water heaters")

    return structures_combined, solar_panels_combined, water_heaters_combined


def load_property_data(states: List[str], aoi_bounds: tuple) -> gpd.GeoDataFrame:
    """
    Load Arturo property data for given state(s).

    Args:
        states: List of state codes (e.g., ['NSW', 'VIC'])
        aoi_bounds: Bounding box tuple (minx, miny, maxx, maxy)

    Returns:
        GeoDataFrame with property parcels (combined from all states)
    """
    all_properties = []

    for state in states:
        property_file = ARTURO_DATA_DIR / f"arturo_{state}_property_details.gpkg"

        if not property_file.exists():
            logger.warning(f"Property data not found for {state}: {property_file}")
            continue

        logger.info(f"Loading Arturo property data from: {state}")

        try:
            properties = gpd.read_file(property_file, layer='parcels', bbox=aoi_bounds)
            logger.info(f"  Loaded {len(properties):,} properties from {state}")
            all_properties.append(properties)
        except Exception as e:
            logger.warning(f"  Failed to load properties from {state}: {e}")

    # Combine all properties
    if not all_properties:
        logger.warning("No property data loaded from any state")
        return gpd.GeoDataFrame(columns=['parcel_id', 'geometry'], crs='EPSG:4326')

    properties_combined = pd.concat(all_properties, ignore_index=True) if len(all_properties) > 1 else all_properties[0]
    logger.info(f"Combined: {len(properties_combined):,} properties")

    return properties_combined


# ============================================================================
# SPATIAL OPERATIONS
# ============================================================================

def spatial_filter(gdf: gpd.GeoDataFrame, aoi_geometry, label: str = "features") -> gpd.GeoDataFrame:
    """Filter GeoDataFrame to only features intersecting the AOI."""
    logger.info(f"Filtering {label} within AOI...")

    # Ensure same CRS
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')

    # Spatial filter
    mask = gdf.intersects(aoi_geometry)
    filtered = gdf[mask].copy()

    logger.info(f"Filtered to {len(filtered):,} {label} within AOI")
    return filtered


def join_structure_property(structures: gpd.GeoDataFrame,
                           properties: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Join structures with properties on parcel_id.
    Returns only structures with valid property matches.

    Args:
        structures: Structure GeoDataFrame
        properties: Property GeoDataFrame

    Returns:
        Merged GeoDataFrame with both structure and property data
    """
    logger.info(f"Joining {len(structures):,} structures with {len(properties):,} properties...")

    # Select relevant property columns
    property_cols = [
        'parcel_id', 'geometry',
        'has_pool', 'pools_total_area',
        'has_trampoline', 'trampoline_ct',
        'has_wooden_deck', 'wooden_deck_area',
        'has_enclosure', 'enclosure_area',
        'has_tennis_court', 'tennis_court_ct',
        'has_basketball_court', 'basketball_court_ct',
        'has_sport_pitch', 'sport_pitch_ct'
    ]

    # Filter to only available columns
    available_cols = [col for col in property_cols if col in properties.columns]

    # Left join on parcel_id
    merged = structures.merge(
        properties[available_cols],
        on='parcel_id',
        how='left',
        suffixes=('_structure', '_property')
    )

    # Filter out structures without property match
    before_count = len(merged)
    merged = merged[merged['geometry_property'].notna()].copy()
    after_count = len(merged)

    skipped = before_count - after_count
    if skipped > 0:
        pct = skipped/before_count*100
        logger.warning(f"Skipped {skipped:,} structures without property matches ({pct:.1f}%)")

    # Early exit if no structures remain
    if len(merged) == 0:
        logger.warning("No structures remaining after property join")
        return merged

    # Deduplicate structures that span multiple parcels (MFDs) if enabled
    if ENABLE_MFD_DEDUPLICATION:
        logger.info("Removing duplicate structures (MFDs spanning multiple parcels)...")
        duplicates_before = len(merged)

        # Calculate overlap area between structure and property geometries
        merged['overlap_area'] = merged.apply(
            lambda row: row['geometry_structure'].intersection(row['geometry_property']).area,
            axis=1
        )

        # Sort by overlap area (descending) and keep first per structure_id
        merged = merged.sort_values('overlap_area', ascending=False)
        merged = merged.drop_duplicates(subset='structure_id', keep='first')

        # Drop the temporary overlap_area column
        merged = merged.drop(columns=['overlap_area'])

        duplicates_removed = duplicates_before - len(merged)
        if duplicates_removed > 0:
            pct = duplicates_removed/duplicates_before*100
            logger.info(f"  Removed {duplicates_removed:,} duplicate structures ({pct:.1f}%)")
    else:
        logger.info("MFD deduplication disabled in config")

    logger.info(f"Successfully joined {len(merged):,} unique structures with properties")
    return merged


def regularize_footprints(merged_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Regularize building footprints using Building-Regulariser library.

    Applies orthogonal edge alignment and polygon simplification to create
    cleaner, more realistic building geometries.

    Args:
        merged_data: GeoDataFrame with structure and property data

    Returns:
        GeoDataFrame with regularized building footprints (geometry_structure column)
    """
    if not REGULARIZATION_AVAILABLE:
        logger.warning("Skipping footprint regularization (library not installed)")
        return merged_data

    logger.info(f"Regularizing {len(merged_data):,} building footprints...")
    start_time = time.time()

    # Extract structure geometries for regularization
    structures_for_reg = merged_data[['structure_id', 'geometry_structure']].copy()
    structures_for_reg = structures_for_reg.rename(columns={'geometry_structure': 'geometry'})
    structures_for_reg = gpd.GeoDataFrame(structures_for_reg, geometry='geometry', crs='EPSG:4326')

    # Convert to projected CRS for accurate regularization
    original_crs = structures_for_reg.crs
    if original_crs and original_crs.is_geographic:
        # Determine appropriate UTM zone based on centroid
        centroid = structures_for_reg.geometry.union_all().centroid
        utm_zone = int((centroid.x + 180) / 6) + 1
        hemisphere = 'north' if centroid.y >= 0 else 'south'
        target_crs = f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84"
        logger.info(f"  Converting to UTM Zone {utm_zone}{' N' if hemisphere == 'north' else ' S'} for regularization")
        structures_for_reg = structures_for_reg.to_crs(target_crs)

    # Calculate original vertex counts
    original_vertices = structures_for_reg.geometry.apply(
        lambda g: len(g.exterior.coords) if isinstance(g, Polygon) else 0
    ).sum()

    # Apply regularization using parameters from config
    logger.info("  Applying orthogonal edge alignment and simplification...")
    regularized = regularize_geodataframe(
        structures_for_reg,
        parallel_threshold=REGULARIZATION_PARAMS['parallel_threshold'],
        simplify=True,
        simplify_tolerance=REGULARIZATION_PARAMS['simplify_tolerance'],
        allow_45_degree=REGULARIZATION_PARAMS['allow_45_degree'],
        diagonal_threshold_reduction=REGULARIZATION_PARAMS['diagonal_threshold_reduction'],
        allow_circles=REGULARIZATION_PARAMS['allow_circles'],
        num_cores=REGULARIZATION_PARAMS['num_cores'],
        include_metadata=False,          # Don't include IoU/direction metadata
        neighbor_alignment=False         # Don't align with neighbors
    )

    # Convert back to original CRS
    if original_crs and original_crs.is_geographic:
        regularized = regularized.to_crs(original_crs)

    # Calculate regularized vertex counts
    regularized_vertices = regularized.geometry.apply(
        lambda g: len(g.exterior.coords) if isinstance(g, Polygon) else 0
    ).sum()

    # Update geometry_structure in merged_data
    regularized_dict = dict(zip(regularized['structure_id'], regularized.geometry))
    merged_data['geometry_structure'] = merged_data['structure_id'].map(regularized_dict)

    # Log statistics
    processing_time = time.time() - start_time
    vertex_reduction = original_vertices - regularized_vertices
    avg_reduction = vertex_reduction / len(merged_data)

    logger.info(f"  Regularization complete in {processing_time:.2f} seconds")
    logger.info(f"  Vertex reduction: {vertex_reduction:,} total ({avg_reduction:.1f} per building)")
    logger.info(f"  Processing rate: {len(merged_data)/processing_time:.0f} buildings/sec")

    return merged_data


# ============================================================================
# SCHEMA TRANSFORMATION
# ============================================================================

def transform_to_preevent_schema(
    merged_data: gpd.GeoDataFrame,
    solar_panels: gpd.GeoDataFrame,
    water_heaters: gpd.GeoDataFrame,
    aoi_metadata: Dict
) -> gpd.GeoDataFrame:
    """
    Transform merged structure+property data to pre-event schema (75 columns).

    Args:
        merged_data: Merged structure+property GeoDataFrame
        solar_panels: Solar panels geometries
        water_heaters: Water heater geometries
        aoi_metadata: AOI metadata dictionary

    Returns:
        GeoDataFrame with 75-column pre-event schema
    """
    logger.info("Transforming to 75-column pre-event schema...")

    # Create spatial unions for intersection checks
    solar_union = None
    water_union = None

    if len(solar_panels) > 0:
        try:
            solar_union = solar_panels.geometry.union_all()
        except Exception as e:
            logger.warning(f"Failed to create solar union: {e}")

    if len(water_heaters) > 0:
        try:
            water_union = water_heaters.geometry.union_all()
        except Exception as e:
            logger.warning(f"Failed to create water heater union: {e}")

    records = []

    for idx, row in merged_data.iterrows():
        # Get geometries
        structure_geom = row['geometry_structure']
        property_geom = row['geometry_property']

        # Spatial joins
        has_solar = False
        has_water_heater = False

        if solar_union is not None:
            try:
                has_solar = structure_geom.intersects(solar_union)
            except Exception:
                pass

        if water_union is not None:
            try:
                has_water_heater = structure_geom.intersects(water_union)
            except Exception:
                pass

        # Map property features
        has_pool = row.get('has_pool', False)
        has_trampoline = row.get('has_trampoline', False)
        has_wooden_deck = row.get('has_wooden_deck', False)
        has_enclosure = row.get('has_enclosure', False)

        # Sport courts (combine all types)
        has_sport = (
            row.get('has_tennis_court', False) or
            row.get('has_basketball_court', False) or
            (row.get('has_sport_pitch', False) if pd.notna(row.get('has_sport_pitch')) else False)
        )

        # Map roof attributes
        roof_shape = ROOF_SHAPE_MAP.get(row.get('roof_shape_majority'), 'Unknown')
        roof_material = ROOF_MATERIAL_MAP.get(row.get('roof_material_majority'), 'Unknown')
        roof_condition = ROOF_CONDITION_MAP.get(row.get('roof_condition_general'), 3.0)
        tree_overlap = round(row.get('roof_tree_overlap_pct', 0)) if pd.notna(row.get('roof_tree_overlap_pct')) else 0
        is_primary = 'TRUE' if row.get('is_primary', False) else 'FALSE'

        record = {
            # Core IDs (1-3)
            'BUILDINGS_IDS': row.get('structure_id'),
            'PEID': row.get('structure_id'),
            'PARCELWKT': property_geom.wkt,  # ← Property boundary (not building!)

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

            # Property Features (13-28) - FROM PROPERTY DATA
            'POOLAREA': row.get('pools_total_area', 0.0),
            'TRAMPOLINE': 'TRUE' if has_trampoline else 'FALSE',
            'TRAMPSCR': None,  # No model score
            'DECK': 'TRUE' if has_wooden_deck else 'FALSE',
            'DECKSCR': None,  # No model score
            'POOL': 'TRUE' if has_pool else 'FALSE',
            'POOLSCR': None,  # No model score
            'ENCLOSURE': 'TRUE' if has_enclosure else 'FALSE',
            'ENCLOSUSCR': None,  # No model score
            'DIVINGBOAR': None,  # Not in Arturo
            'DIVINGSCR': None,
            'WATERSLIDE': None,  # Not in Arturo
            'WATSLIDSCR': None,
            'PLAYGROUND': None,  # Not in Arturo
            'PLAYGSCR': None,
            'SPORTCOURT': 'TRUE' if has_sport else 'FALSE',
            'SPORTSCR': None,  # No model score
            'PRIMARYSTR': is_primary,

            # Roof Attributes (29-40)
            'ROOFTOPGEO': structure_geom.wkt,
            'GROUNDELEV': None,
            'DETECTSCR': 1.0,
            'ROOFSHAPE': roof_shape,
            'ROOFSHASCR': None,
            'ROOFMATERI': roof_material,
            'ROOFMATSCR': 1.0,
            'ROOFCONDIT': roof_condition,
            'ROOFSOLAR': 'SOLAR PANEL' if has_solar else 'NO SOLAR PANEL',
            'ROOFTREE': tree_overlap,

            # Distance Scores (41-48) - All NULL
            'DST5': None, 'DSB5': None,
            'DST30': None, 'DSB30': None,
            'DST100': None, 'DSB100': None,
            'DST200': None, 'DSB200': None,

            # Damage Assessment (49-57) - All zero/false (pre-event)
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

            # Classification Keywords (65-68) - All NULL
            'DSKWT5': None,
            'DSKWT30': None,
            'DSKWT100': None,
            'DSKWT200': None,

            # Additional Metadata (69-71) - All NULL
            'task_structures_info': None,
            'structures_count': None,
            'property_id': None,

            # Additional Damage Field (72-73)
            'ROOFCONDIT_STRUCTURALDAMAGEPERCEN': 0.0,

            # Water Heater (74)
            'ROOFWATERHEATER': 'WATER HEATER' if has_water_heater else 'NO WATER HEATER',

            # Geometry (75)
            'geometry': structure_geom
        }

        records.append(record)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(records, crs='EPSG:4326')

    logger.info(f"Transformed {len(gdf):,} structures to pre-event schema")
    return gdf


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def save_output(
    structures: gpd.GeoDataFrame,
    solar_panels: gpd.GeoDataFrame,
    water_heaters: gpd.GeoDataFrame,
    aoi_metadata: Dict,
    aoi_geometry
) -> Path:
    """
    Save output GeoPackage with 3 layers + metadata JSON.

    Args:
        structures: Main structures layer (75 columns)
        solar_panels: Solar panel geometries
        water_heaters: Water heater geometries
        aoi_metadata: AOI metadata
        aoi_geometry: AOI geometry (for WKT)

    Returns:
        Path to output GeoPackage
    """
    # Generate output filename using collection name
    collection_name = aoi_metadata['collection']  # e.g., "graydata-735"

    # Use standardized naming: {collection}_DA_pre-event
    base_name = f"{collection_name}_DA_pre-event"
    output_gpkg = OUTPUT_DIR / f"{base_name}.gpkg"
    output_json = OUTPUT_DIR / f"{base_name}.json"

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving output to: {output_gpkg}")

    # Save main structures layer
    structures.to_file(output_gpkg, driver='GPKG', layer='pre_event_structures')
    logger.info(f"  Saved {len(structures):,} structures to layer: pre_event_structures")

    # Save solar panels layer
    if len(solar_panels) > 0:
        solar_panels.to_file(output_gpkg, driver='GPKG', layer='solar_panels')
        logger.info(f"  Saved {len(solar_panels):,} solar panels to layer: solar_panels")

    # Save water heaters layer
    if len(water_heaters) > 0:
        water_heaters.to_file(output_gpkg, driver='GPKG', layer='water_heaters')
        logger.info(f"  Saved {len(water_heaters):,} water heaters to layer: water_heaters")

    # Save metadata JSON
    import json

    # Convert geometry to WKT
    geom_wkt = aoi_geometry.wkt

    metadata = {
        "batch_id": base_name,
        "creation_date": datetime.now().isoformat(),
        "capture_project": aoi_metadata['event_id'],
        "wkt": geom_wkt,
        "schema_version": "CATASTROPHE_DEFAULT.1.0.5"
    }

    with open(output_json, 'w') as f:
        json.dump(metadata, f)

    logger.info(f"  Saved metadata to: {output_json}")

    return output_gpkg


def print_summary(structures: gpd.GeoDataFrame, aoi_metadata: Dict, output_file: Path):
    """Print extraction summary."""
    print("\n" + "="*80)
    print("EXTRACTION COMPLETE")
    print("="*80)
    print(f"Event: {aoi_metadata['event_name']}")
    print(f"AOI ID: {aoi_metadata['event_id']}")
    print(f"Area: {aoi_metadata['area_km2']:.2f} km²")
    print()
    print(f"Extracted: {len(structures):,} structures")
    print(f"Schema: 75 columns")
    print()
    print(f"Output: {output_file}")
    print(f"Layers: pre_event_structures, solar_panels, water_heaters")
    print("="*80 + "\n")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract pre-event data with property integration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--aoi-index", "-a",
        type=int,
        help="AOI index (1-56) for direct selection"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Load AOIs from all sources (API + KML)
        aois = load_all_aois()

        # Select AOI
        if args.aoi_index:
            aoi_index = args.aoi_index - 1
            if aoi_index < 0 or aoi_index >= len(aois):
                logger.error(f"Invalid AOI index: {args.aoi_index}. Must be 1-{len(aois)}")
                return 1
        else:
            aoi_index = select_aoi_interactive(aois)

        # Get selected AOI
        selected_aoi = aois[aoi_index]

        # Get geometry (fetch from API or use pre-loaded from KML)
        aoi_gdf = get_aoi_geometry(selected_aoi)
        aoi_geometry = aoi_gdf.geometry.iloc[0]

        # Get metadata
        aoi_metadata = get_aoi_metadata(selected_aoi, aoi_geometry)
        aoi_bounds = aoi_geometry.bounds

        print(f"\nSelected: {aoi_metadata['event_name']}")
        print(f"Area: {aoi_metadata['area_km2']:.2f} km²\n")

        # Determine states
        states = determine_states(aoi_geometry)
        if not states:
            logger.error("Cannot determine state for AOI")
            return 1

        logger.info(f"Will load data from states: {', '.join(states)}")

        # Load structure data
        structures, solar_panels, water_heaters = load_arturo_data(states, aoi_bounds)

        # Load property data
        properties = load_property_data(states, aoi_bounds)

        # Spatial filtering
        structures_filtered = spatial_filter(structures, aoi_geometry, "structures")
        properties_filtered = spatial_filter(properties, aoi_geometry, "properties")
        solar_panels_filtered = spatial_filter(solar_panels, aoi_geometry, "solar panels") if len(solar_panels) > 0 else solar_panels
        water_heaters_filtered = spatial_filter(water_heaters, aoi_geometry, "water heaters") if len(water_heaters) > 0 else water_heaters

        # Join structures with properties (includes deduplication if enabled)
        merged_data = join_structure_property(structures_filtered, properties_filtered)

        if len(merged_data) == 0:
            logger.error("No structures with property matches found! Cannot proceed.")
            return 1

        # Regularize building footprints (if enabled in config)
        if ENABLE_REGULARIZATION and REGULARIZATION_AVAILABLE:
            merged_data = regularize_footprints(merged_data)
        elif ENABLE_REGULARIZATION and not REGULARIZATION_AVAILABLE:
            logger.warning("Regularization enabled in config but library not available. Skipping.")
        else:
            logger.info("Footprint regularization disabled in config")

        # Transform to schema
        result_gdf = transform_to_preevent_schema(
            merged_data,
            solar_panels_filtered,
            water_heaters_filtered,
            aoi_metadata
        )

        # Save output
        output_file = save_output(
            result_gdf,
            solar_panels_filtered,
            water_heaters_filtered,
            aoi_metadata,
            aoi_geometry
        )

        # Print summary
        print_summary(result_gdf, aoi_metadata, output_file)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
