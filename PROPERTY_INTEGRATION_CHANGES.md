# Property Integration Changes

## Required Changes to `extract_pre_event_data.py`

### 1. Add New Function: `load_property_data()`

**Insert after `load_arturo_data()` function:**

```python
def load_property_data(states: list, aoi_bounds: tuple) -> gpd.GeoDataFrame:
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

        logger.info(f"Loading Property data from: {property_file}")

        try:
            properties = gpd.read_file(property_file, layer='parcels', bbox=aoi_bounds)
            logger.info(f"  Loaded {len(properties)} properties from {state}")
            all_properties.append(properties)
        except Exception as e:
            logger.warning(f"  Failed to load properties from {state}: {e}")

    # Combine all properties
    if not all_properties:
        logger.warning("No property data loaded from any state")
        return gpd.GeoDataFrame(columns=['parcel_id', 'geometry'], crs='EPSG:4326')

    properties_combined = pd.concat(all_properties, ignore_index=True) if len(all_properties) > 1 else all_properties[0]
    logger.info(f"Combined properties: {len(properties_combined)}")

    return properties_combined
```

### 2. Add New Function: `join_structure_property()`

**Insert after `spatial_filter()` function:**

```python
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
    logger.info(f"Joining {len(structures)} structures with {len(properties)} properties...")

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

    # Filter out structures without property match (as per user requirement)
    before_count = len(merged)
    merged = merged[merged['geometry_property'].notna()].copy()
    after_count = len(merged)

    skipped = before_count - after_count
    if skipped > 0:
        logger.warning(f"Skipped {skipped} structures without property matches ({skipped/before_count*100:.1f}%)")

    logger.info(f"Successfully joined {after_count} structures with properties")
    return merged
```

### 3. Update `transform_to_preevent_schema()` Function

**Replace the entire function with:**

```python
def transform_to_preevent_schema(
    merged_data: gpd.GeoDataFrame,
    solar_panels: gpd.GeoDataFrame,
    water_heaters: gpd.GeoDataFrame,
    aoi_metadata: dict
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
    logger.info("Transforming to pre-event schema...")

    # Create spatial unions for intersection checks
    solar_union = None
    water_union = None

    if len(solar_panels) > 0:
        try:
            solar_union = solar_panels.geometry.unary_union
        except Exception as e:
            logger.warning(f"Failed to create solar union: {e}")

    if len(water_heaters) > 0:
        try:
            water_union = water_heaters.geometry.unary_union
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
            'PARCELWKT': property_geom.wkt,  # ← UPDATED: True property boundary!

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

            # Property Features (13-28) - UPDATED with property data
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

    logger.info(f"Transformed {len(gdf)} structures to pre-event schema")
    return gdf
```

### 4. Update `main()` Function

**Find the section where data is loaded and processed. Replace:**

```python
# OLD CODE (around line 450-480):
structures, solar_panels, water_heaters = load_arturo_data(states, aoi_bounds)
structures_filtered = spatial_filter(structures, aoi_geometry)
result_gdf = transform_to_preevent_schema(structures_filtered, solar_panels, water_heaters, aoi_metadata)
```

**WITH:**

```python
# NEW CODE:
# Load structure data
structures, solar_panels, water_heaters = load_arturo_data(states, aoi_bounds)
structures_filtered = spatial_filter(structures, aoi_geometry)

# Load property data
properties = load_property_data(states, aoi_bounds)
properties_filtered = spatial_filter(properties, aoi_geometry)

# Join structures with properties
merged_data = join_structure_property(structures_filtered, properties_filtered)

if len(merged_data) == 0:
    logger.error("No structures with property matches found!")
    return 1

# Transform to schema
result_gdf = transform_to_preevent_schema(merged_data, solar_panels, water_heaters, aoi_metadata)
```

---

## Summary of Changes

1. **Added `load_property_data()`**: Loads property parcels from arturo_{STATE}_property_details.gpkg
2. **Added `join_structure_property()`**: Joins structures with properties on parcel_id, skips unmatched structures
3. **Updated `transform_to_preevent_schema()`**:
   - Now accepts merged data (structure+property)
   - PARCELWKT uses property.geometry (not structure.geometry)
   - Property features (POOL, DECK, TRAMPOLINE, etc.) mapped from property data
   - All *SCR fields set to None (not 0.0)
   - Missing features (DIVINGBOAR, WATERSLIDE, PLAYGROUND) set to None
   - SPORTCOURT combines tennis + basketball courts
4. **Updated `main()` workflow**: Loads properties, filters, joins with structures before transformation

---

**Implementation Note**: Due to the length of the script, I've provided the changes as a patch. You can either:
1. Apply these changes manually to the existing script
2. Or I can create a complete new version of the script with all changes integrated

Would you like me to create the complete new script file?
