# Final Attribute Mappings - CONFIRMED

## ✅ All Mappings Verified with Actual Arturo Data

---

## 1. Core Identifiers

```python
BUILDINGS_IDS = arturo.structure_id
PEID = arturo.structure_id  # Same value
PARCELWKT = arturo.geometry.wkt  # Plain WKT, no SRID prefix
```

---

## 2. Metadata - Building (B.* prefix)

```python
B.CAPTURE_PROJECT = arturo.vexcel_collection_name  # e.g., "au-nt-darwin-2024"
METADATAVERSION = "3.90.1"  # Fixed
B.LAYERNAME = "bluesky-ultra-oceania"  # Fixed
B.IMAGEID = None  # Leave empty
B.CHILD_AOI = arturo.vexcel_collection_name  # Same as B.CAPTURE_PROJECT
B.ORTHOVSNADIR = "ortho"  # Fixed
B.CAMERATECHNOLOGY = "UltraCam_Osprey_4.1_f120"  # Fixed
```

---

## 3. Metadata - Building Image

```python
B.IMGDATE = None  # Leave empty
B.IMGGSD = graysky_aoi.avg_gsd  # From AOI metadata
```

---

## 4. Property Features (All FALSE for pre-event)

```python
POOLAREA = 0.0
TRAMPOLINE = "FALSE"
TRAMPSCR = 0.0
DECK = "FALSE"
DECKSCR = 0.0
POOL = "FALSE"
POOLSCR = 0.0
ENCLOSURE = "FALSE"
ENCLOSUSCR = 0.0
DIVINGBOAR = "FALSE"
DIVINGSCR = 0.0
WATERSLIDE = "FALSE"
WATSLIDSCR = 0.0
PLAYGROUND = "FALSE"
PLAYGSCR = 0.0
SPORTCOURT = "FALSE"
SPORTSCR = 0.0
PRIMARYSTR = "TRUE" if arturo.is_primary else "FALSE"
```

---

## 5. Roof Attributes

```python
ROOFTOPGEO = arturo.geometry.wkt  # Plain WKT
GROUNDELEV = None  # Leave NULL
DETECTSCR = 1.0  # Full detection confidence
```

### 5a. Roof Shape Mapping ✓ VERIFIED

**Actual Arturo Values:** `gable`, `hip`, `flat`

```python
ROOF_SHAPE_MAP = {
    'gable': 'gable',
    'hip': 'hip',
    'flat': 'flat',
    None: 'Unknown'  # For NULL values
}

ROOFSHAPE = ROOF_SHAPE_MAP.get(arturo.roof_shape_majority, 'Unknown')
ROOFSHASCR = None  # Leave NULL
```

**Perfect match!** No complex mapping needed.

---

### 5b. Roof Material Mapping ✓ VERIFIED

**Actual Arturo Values:**
- `metal` (36,528 - 73%)
- `concrete_tile` (11,102 - 22%)
- `clay_tile` (1,361 - 3%)
- `solid_concrete` (127)
- `other_material` (122)
- `tile` (3)
- NULL (757)

**Target Categories:** gravel, membrane, metal, shake, shingle, tile

```python
ROOF_MATERIAL_MAP = {
    'metal': 'metal',
    'concrete_tile': 'tile',
    'clay_tile': 'tile',
    'tile': 'tile',
    'solid_concrete': 'membrane',  # Flat concrete -> membrane
    'other_material': 'Unknown',
    None: 'Unknown'
}

ROOFMATERI = ROOF_MATERIAL_MAP.get(arturo.roof_material_majority, 'Unknown')
ROOFMATSCR = 1.0  # Full material detection confidence
```

**Note:** Arturo data doesn't have `gravel`, `shake`, or `shingle` - all Australian roofs!

---

### 5c. Roof Condition Mapping ✓ VERIFIED

**Actual Arturo Values:** `good`, `fair`, `poor` (lowercase!)

**Target Scale:** 1.0 (poor) to 5.0 (excellent) - INVERTED!

```python
ROOF_CONDITION_MAP = {
    'good': 4.0,      # Good condition
    'fair': 3.0,      # Fair condition
    'poor': 2.0,      # Poor condition
    'excellent': 5.0, # Excellent (if exists)
    None: 3.0         # Default to fair if NULL
}

ROOFCONDIT = ROOF_CONDITION_MAP.get(arturo.roof_condition_general, 3.0)
```

**Note:** No "excellent" or "very poor" in Arturo data, using 3-tier system.

---

### 5d. Solar Panel Detection ✓

```python
# Spatial join with solar_panels layer
solar_panels = gpd.read_file(arturo_gpkg, layer='solar_panels', bbox=aoi_bounds)

ROOFSOLAR = (
    'SOLAR PANEL'
    if arturo.geometry.intersects(solar_panels.unary_union)
    else 'NO SOLAR PANEL'
)
```

---

### 5e. Tree Overhang ✓

```python
# Round to whole number
ROOFTREE = round(arturo.roof_tree_overlap_pct) if arturo.roof_tree_overlap_pct else 0
```

---

## 6. Damage Scores - Distance (All NULL/Empty)

```python
# Distance to trees (feet)
DST5 = None
DST30 = None
DST100 = None
DST200 = None

# Distance to buildings (feet)
DSB5 = None
DSB30 = None
DSB100 = None
DSB200 = None
```

---

## 7. Damage Assessment (All Zero/False for Pre-Event)

```python
CATASTROPHESCORE = 0  # No damage
ROOFCONDIT_MISSINGMATERIALPERCEN = 0.0
ROOFCONDIT_TARPPERCEN = 0.0
ROOFCONDIT_DEBRISPERCENT = 0.0
ROOFCONDIT_DISCOLORDETECT = "FALSE"
ROOFCONDIT_DISCOLORPERCEN = 0.0
ROOFCONDIT_DISCOLORSCORE = 0.0
ROOFCONDIT_STRUCTURALDAMAGEPERCEN = 0.0
DAMAGE_LEVEL = None  # NULL
```

---

## 8. Additional Scores

```python
HISTOSCORE = 0.0  # No histogram damage score
```

---

## 9. Metadata - Damage Assessment (from Graysky AOI)

```python
CAPTURE_PROJECT = graysky_aoi.collection  # e.g., "graydata-736"
LAYERNAME = graysky_aoi.layer  # "graysky" or "graysky-suncorp"
IMAGEID = None  # Leave empty
CHILD_AOI = graysky_aoi.event_id  # e.g., "au-qld-alfred-cyclone-224-2025"
ORTHOVSNADIR = "ortho"  # Fixed
CAMERATECHNOLOGY = "UltraCam_Osprey_4.1_f120"  # Fixed
```

---

## 10. Metadata - Damage Image

```python
IMGDATE = None  # Leave empty
IMGGSD = graysky_aoi.avg_gsd  # From AOI
```

---

## 11. Classification Keywords (All NULL)

```python
DSKWT5 = None
DSKWT30 = None
DSKWT100 = None
DSKWT200 = None
```

---

## 12. Additional Metadata (All NULL)

```python
task_structures_info = None
structures_count = None
property_id = None
```

---

## 13. **NEW FIELD** - Water Heater Detection ✓

```python
# NEW 75th column
# Spatial join with pool_heaters layer
water_heaters = gpd.read_file(arturo_gpkg, layer='pool_heaters', bbox=aoi_bounds)

ROOFWATERHEATER = (
    'WATER HEATER'
    if arturo.geometry.intersects(water_heaters.unary_union)
    else 'NO WATER HEATER'
)
```

---

## 14. Geometry

```python
geometry = arturo.geometry  # Keep as Polygon, EPSG:4326
```

**Note:** Target uses Polygon (not MultiPolygon!)

---

## Complete Mapping Function

```python
def map_arturo_to_preevent(arturo_row, aoi_metadata, solar_panels_gdf, water_heaters_gdf):
    """Map single Arturo structure to pre-event schema."""

    # Helper for spatial intersection
    geom = arturo_row.geometry
    has_solar = solar_panels_gdf.intersects(geom).any() if len(solar_panels_gdf) > 0 else False
    has_water_heater = water_heaters_gdf.intersects(geom).any() if len(water_heaters_gdf) > 0 else False

    return {
        # Core IDs
        'BUILDINGS_IDS': arturo_row.structure_id,
        'PEID': arturo_row.structure_id,
        'PARCELWKT': geom.wkt,

        # Metadata - Building
        'B.CAPTURE_PROJECT': arturo_row.vexcel_collection_name,
        'METADATAVERSION': '3.90.1',
        'B.LAYERNAME': 'bluesky-ultra-oceania',
        'B.IMAGEID': None,
        'B.CHILD_AOI': arturo_row.vexcel_collection_name,
        'B.ORTHOVSNADIR': 'ortho',
        'B.CAMERATECHNOLOGY': 'UltraCam_Osprey_4.1_f120',

        # Metadata - Building Image
        'B.IMGDATE': None,
        'B.IMGGSD': aoi_metadata['avg_gsd'],

        # Property Features (all FALSE)
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
        'PRIMARYSTR': 'TRUE' if arturo_row.is_primary else 'FALSE',

        # Roof Attributes
        'ROOFTOPGEO': geom.wkt,
        'GROUNDELEV': None,
        'DETECTSCR': 1.0,
        'ROOFSHAPE': ROOF_SHAPE_MAP.get(arturo_row.roof_shape_majority, 'Unknown'),
        'ROOFSHASCR': None,
        'ROOFMATERI': ROOF_MATERIAL_MAP.get(arturo_row.roof_material_majority, 'Unknown'),
        'ROOFMATSCR': 1.0,
        'ROOFCONDIT': ROOF_CONDITION_MAP.get(arturo_row.roof_condition_general, 3.0),
        'ROOFSOLAR': 'SOLAR PANEL' if has_solar else 'NO SOLAR PANEL',
        'ROOFTREE': round(arturo_row.roof_tree_overlap_pct) if arturo_row.roof_tree_overlap_pct else 0,

        # Distance scores (all NULL)
        'DST5': None, 'DSB5': None,
        'DST30': None, 'DSB30': None,
        'DST100': None, 'DSB100': None,
        'DST200': None, 'DSB200': None,

        # Damage Assessment (all zero/false)
        'CATASTROPHESCORE': 0,
        'ROOFCONDIT_MISSINGMATERIALPERCEN': 0.0,
        'ROOFCONDIT_TARPPERCEN': 0.0,
        'ROOFCONDIT_DEBRISPERCENT': 0.0,
        'ROOFCONDIT_DISCOLORDETECT': 'FALSE',
        'ROOFCONDIT_DISCOLORPERCEN': 0.0,
        'ROOFCONDIT_DISCOLORSCORE': 0.0,
        'ROOFCONDIT_STRUCTURALDAMAGEPERCEN': 0.0,
        'DAMAGE_LEVEL': None,
        'HISTOSCORE': 0.0,

        # Metadata - Damage Assessment
        'CAPTURE_PROJECT': aoi_metadata['collection'],
        'LAYERNAME': aoi_metadata['layer'],
        'IMAGEID': None,
        'CHILD_AOI': aoi_metadata['event_id'],
        'ORTHOVSNADIR': 'ortho',
        'CAMERATECHNOLOGY': 'UltraCam_Osprey_4.1_f120',
        'IMGDATE': None,
        'IMGGSD': aoi_metadata['avg_gsd'],

        # Classification keywords (all NULL)
        'DSKWT5': None, 'DSKWT30': None,
        'DSKWT100': None, 'DSKWT200': None,

        # Additional metadata (all NULL)
        'task_structures_info': None,
        'structures_count': None,
        'property_id': None,

        # NEW FIELD - Water Heater
        'ROOFWATERHEATER': 'WATER HEATER' if has_water_heater else 'NO WATER HEATER',

        # Geometry
        'geometry': geom
    }
```

---

## Mapping Constants

```python
# Roof Shape Mapping
ROOF_SHAPE_MAP = {
    'gable': 'gable',
    'hip': 'hip',
    'flat': 'flat',
    None: 'Unknown'
}

# Roof Material Mapping
ROOF_MATERIAL_MAP = {
    'metal': 'metal',
    'concrete_tile': 'tile',
    'clay_tile': 'tile',
    'tile': 'tile',
    'solid_concrete': 'membrane',
    'other_material': 'Unknown',
    None: 'Unknown'
}

# Roof Condition Mapping (inverted scale!)
ROOF_CONDITION_MAP = {
    'good': 4.0,
    'fair': 3.0,
    'poor': 2.0,
    'excellent': 5.0,
    None: 3.0
}
```

---

## Output Schema - 75 Columns

**Total columns:** 75 (74 original + 1 new ROOFWATERHEATER)

**Column order:**
1-13: Core IDs and Building Metadata
14-28: Property Features
29-40: Roof Attributes
41-48: Distance Scores
49-57: Damage Assessment
58: HISTOSCORE
59-65: Damage Metadata
66-69: Classification Keywords
70-72: Additional Metadata
73: ROOFCONDIT_STRUCTURALDAMAGEPERCEN
74: **ROOFWATERHEATER** (NEW)
75: geometry

---

## Output Layers

```python
output_layers = {
    'pre_event_structures': structures_gdf,  # Main layer (75 columns)
    'solar_panels': solar_panels_in_aoi,     # Solar panel geometries
    'water_heaters': water_heaters_in_aoi    # Water heater geometries
}
```

---

**Created:** 2025-10-27
**Verified:** All mappings tested against actual Arturo data
**Status:** ✅ READY FOR IMPLEMENTATION
