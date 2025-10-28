# Property Data Integration - Final Mappings

## ✅ User Responses Incorporated

Based on user feedback, here are the final mapping decisions for integrating Arturo Property data.

---

## Final Mapping Decisions

### 1. Score Fields → **NULL**
**Decision**: SCR stands for model score. Arturo doesn't provide this, so set all to NULL.

```python
POOLSCR = None
TRAMPSCR = None
DECKSCR = None
ENCLOSUSCR = None
DIVINGSCR = None
WATSLIDSCR = None
PLAYGSCR = None
SPORTSCR = None
```

---

### 2. Sport Courts → **Combine All Types**
**Decision**: Collapse all sport court types from Arturo into one SPORTCOURT field.

```python
# Combine tennis, basketball, and any other sport courts
has_sport = (
    property.has_tennis_court or
    property.has_basketball_court or
    (property.has_sport_pitch if pd.notna(property.has_sport_pitch) else False)
)

SPORTCOURT = "TRUE" if has_sport else "FALSE"
SPORTSCR = None  # No score available
```

---

### 3. Missing Features → **NULL**
**Decision**: Features not in Arturo should be NULL (not FALSE).

```python
DIVINGBOAR = None
DIVINGSCR = None
WATERSLIDE = None
WATSLIDSCR = None
PLAYGROUND = None
PLAYGSCR = None
```

---

### 4. Playground → **Ignore sport_pitch**
**Decision**: Do not infer playground from sport_pitch. Ignore this attribute.

```python
PLAYGROUND = None  # Not available in Arturo
```

---

### 5. Pool Heater → **Keep Existing Logic (Structure-level)**
**Decision**: Pool heaters should only be on structures (roofs), not on property level. The pool_heaters layer in property GeoPackage is likely a false attribute.

**Action**: Keep existing spatial join logic using `pool_heaters` layer from **structure GeoPackage only**.

```python
# Load from structure GeoPackage (existing logic)
water_heaters = gpd.read_file(
    arturo_structure_gpkg,
    layer='pool_heaters',
    bbox=aoi_bounds
)

ROOFWATERHEATER = 'WATER HEATER' if has_water_heater else 'NO WATER HEATER'
```

---

### 6. Missing Property → **Skip Structure**
**Decision**: If structure.parcel_id doesn't match any property, skip that structure entirely.

```python
# Only process structures with valid property matches
if property_match is None:
    logger.warning(f"Structure {structure_id} has no property match, skipping")
    continue  # Skip this structure
```

---

### 7. Accuracy Metrics → **Skip**
**Decision**: Fully skip accuracy metrics. Do not use for scores.

```python
# Ignore accuracy_metrics field completely
```

---

### 8. Additional Geometry Layers → **Do NOT Include**
**Decision**: We do NOT include additional geometry layers (pools, trampolines, wooden_decks, etc.) in output.

**Output layers remain:**
- `pre_event_structures` (main layer)
- `solar_panels` (roof-mounted, from structure data)
- `water_heaters` (from structure data)

---

### 9. Ground Elevation → **Do NOT Add**
**Decision**: We do not add ground elevation/slope attributes.

```python
GROUNDELEV = None  # Leave NULL
```

---

## Complete Property Mapping

```python
def map_with_property(structure_row, property_row, solar_panels_gdf, water_heaters_gdf, aoi_metadata):
    """
    Map structure + property data to pre-event schema.

    Args:
        structure_row: Row from arturo_structuredetails structures layer
        property_row: Row from arturo_property_details parcels layer (or None)
        solar_panels_gdf: Solar panels geometries (from structure data)
        water_heaters_gdf: Water heaters geometries (from structure data)
        aoi_metadata: Graysky AOI metadata dict

    Returns:
        dict: Mapped record for 75-column schema
    """

    # Skip if no property match
    if property_row is None:
        return None  # Caller should skip this structure

    # Get geometries
    structure_geom = structure_row.geometry
    property_geom = property_row.geometry

    # Spatial joins for solar/water heater
    has_solar = solar_panels_gdf.intersects(structure_geom).any() if len(solar_panels_gdf) > 0 else False
    has_water_heater = water_heaters_gdf.intersects(structure_geom).any() if len(water_heaters_gdf) > 0 else False

    # Sport courts (combine all types)
    has_sport = (
        property_row.get('has_tennis_court', False) or
        property_row.get('has_basketball_court', False) or
        (property_row.get('has_sport_pitch', False) if pd.notna(property_row.get('has_sport_pitch')) else False)
    )

    return {
        # Core IDs (1-3)
        'BUILDINGS_IDS': structure_row.get('structure_id'),
        'PEID': structure_row.get('structure_id'),
        'PARCELWKT': property_geom.wkt,  # ← UPDATED: True property boundary!

        # Metadata - Building (4-10)
        'B.CAPTURE_PROJECT': structure_row.get('vexcel_collection_name'),
        'METADATAVERSION': '3.90.1',
        'B.LAYERNAME': 'bluesky-ultra-oceania',
        'B.IMAGEID': None,
        'B.CHILD_AOI': structure_row.get('vexcel_collection_name'),
        'B.ORTHOVSNADIR': 'ortho',
        'B.CAMERATECHNOLOGY': 'UltraCam_Osprey_4.1_f120',

        # Metadata - Building Image (11-12)
        'B.IMGDATE': None,
        'B.IMGGSD': aoi_metadata.get('avg_gsd'),

        # Property Features (13-28) - UPDATED
        'POOLAREA': property_row.get('pools_total_area', 0.0),
        'TRAMPOLINE': 'TRUE' if property_row.get('has_trampoline', False) else 'FALSE',
        'TRAMPSCR': None,  # No score
        'DECK': 'TRUE' if property_row.get('has_wooden_deck', False) else 'FALSE',
        'DECKSCR': None,  # No score
        'POOL': 'TRUE' if property_row.get('has_pool', False) else 'FALSE',
        'POOLSCR': None,  # No score
        'ENCLOSURE': 'TRUE' if property_row.get('has_enclosure', False) else 'FALSE',
        'ENCLOSUSCR': None,  # No score
        'DIVINGBOAR': None,  # Not in Arturo
        'DIVINGSCR': None,
        'WATERSLIDE': None,  # Not in Arturo
        'WATSLIDSCR': None,
        'PLAYGROUND': None,  # Not in Arturo
        'PLAYGSCR': None,
        'SPORTCOURT': 'TRUE' if has_sport else 'FALSE',
        'SPORTSCR': None,  # No score
        'PRIMARYSTR': 'TRUE' if structure_row.get('is_primary', False) else 'FALSE',

        # Roof Attributes (29-40)
        'ROOFTOPGEO': structure_geom.wkt,
        'GROUNDELEV': None,
        'DETECTSCR': 1.0,
        'ROOFSHAPE': ROOF_SHAPE_MAP.get(structure_row.get('roof_shape_majority'), 'Unknown'),
        'ROOFSHASCR': None,
        'ROOFMATERI': ROOF_MATERIAL_MAP.get(structure_row.get('roof_material_majority'), 'Unknown'),
        'ROOFMATSCR': 1.0,
        'ROOFCONDIT': ROOF_CONDITION_MAP.get(structure_row.get('roof_condition_general'), 3.0),
        'ROOFSOLAR': 'SOLAR PANEL' if has_solar else 'NO SOLAR PANEL',
        'ROOFTREE': round(structure_row.get('roof_tree_overlap_pct', 0)) if pd.notna(structure_row.get('roof_tree_overlap_pct')) else 0,

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

        # Water Heater (74) - From structure data
        'ROOFWATERHEATER': 'WATER HEATER' if has_water_heater else 'NO WATER HEATER',

        # Geometry (75)
        'geometry': structure_geom
    }
```

---

## Implementation Steps

### 1. Load Property Data

```python
def load_property_data(state: str, aoi_bounds: tuple) -> gpd.GeoDataFrame:
    """Load property data from arturo_property_details.gpkg"""
    property_file = Path(f'/Users/romanbuegler/dev/hail_damage/data/final/arturo_{state}_property_details.gpkg')

    if not property_file.exists():
        logger.warning(f"Property file not found: {property_file}")
        return gpd.GeoDataFrame(columns=['parcel_id', 'geometry'], crs='EPSG:4326')

    try:
        properties = gpd.read_file(property_file, layer='parcels', bbox=aoi_bounds)
        logger.info(f"Loaded {len(properties)} properties from {state}")
        return properties
    except Exception as e:
        logger.error(f"Failed to load properties: {e}")
        return gpd.GeoDataFrame(columns=['parcel_id', 'geometry'], crs='EPSG:4326')
```

---

### 2. Join Structure + Property

```python
def join_structure_property(structures: gpd.GeoDataFrame,
                           properties: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Join structures with properties on parcel_id.
    Returns only structures with valid property matches.
    """
    logger.info(f"Joining {len(structures)} structures with {len(properties)} properties")

    # Left join on parcel_id
    merged = structures.merge(
        properties[['parcel_id', 'geometry'] + PROPERTY_FEATURE_COLS],
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
        logger.warning(f"Skipped {skipped} structures without property matches")

    logger.info(f"Successfully joined {after_count} structures with properties")
    return merged
```

---

### 3. Transform to Schema

```python
def transform_to_preevent_schema(merged_gdf, solar_panels, water_heaters, aoi_metadata):
    """
    Transform merged structure+property data to 75-column pre-event schema.
    """
    records = []

    for idx, row in merged_gdf.iterrows():
        # Extract geometries
        structure_geom = row['geometry_structure']
        property_geom = row['geometry_property']

        # Map to schema
        record = map_with_property(
            structure_row=row,  # Has structure fields + property fields
            property_row=row,   # Same row (merged)
            solar_panels_gdf=solar_panels,
            water_heaters_gdf=water_heaters,
            aoi_metadata=aoi_metadata
        )

        if record is not None:
            records.append(record)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(records, crs='EPSG:4326')
    return gdf
```

---

### 4. Property Feature Columns

```python
PROPERTY_FEATURE_COLS = [
    'has_pool',
    'pools_total_area',
    'has_trampoline',
    'trampoline_ct',
    'has_wooden_deck',
    'wooden_deck_area',
    'has_enclosure',
    'enclosure_area',
    'has_tennis_court',
    'has_basketball_court',
    'has_sport_pitch',
    'tennis_court_ct',
    'basketball_court_ct',
]
```

---

## Key Changes from Current Implementation

| Aspect | Old Behavior | New Behavior |
|--------|-------------|--------------|
| **PARCELWKT** | structure.geometry.wkt | property.geometry.wkt |
| **Property Features** | All FALSE/0.0 | Mapped from property data |
| **POOL** | FALSE | From property.has_pool |
| **POOLAREA** | 0.0 | From property.pools_total_area |
| **TRAMPOLINE** | FALSE | From property.has_trampoline |
| **DECK** | FALSE | From property.has_wooden_deck |
| **ENCLOSURE** | FALSE | From property.has_enclosure |
| **SPORTCOURT** | FALSE | Combined from tennis/basketball courts |
| **All *SCR fields** | 0.0 | NULL (no model scores) |
| **Missing features** | FALSE | NULL (not available) |
| **Structures w/o property** | Included | **Skipped** |

---

## Output Schema - Still 75 Columns

No change to column count or order. Only the source data changes.

---

## Testing Checklist

- [ ] Load property data for each state
- [ ] Join structures with properties on parcel_id
- [ ] Verify PARCELWKT is property boundary (larger than building)
- [ ] Verify ROOFTOPGEO is still building footprint
- [ ] Check property features are correctly mapped
- [ ] Verify structures without property matches are skipped
- [ ] Check all *SCR fields are NULL (not 0.0)
- [ ] Verify DIVINGBOAR, WATERSLIDE, PLAYGROUND are NULL
- [ ] Test with AOI that has pool/trampoline/deck features

---

**Status**: ✅ Ready for implementation

**Created**: 2025-10-27

**User Responses**: All 9 questions answered
