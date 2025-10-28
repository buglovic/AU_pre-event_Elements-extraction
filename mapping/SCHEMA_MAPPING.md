# Schema Mapping: Arturo → Pre-Event Data

## Target Schema Overview

**Source**: `annotations.gpkg` layer `caboolture_final_vision`
**Format**: GeoPackage with 12 attributes + geometry
**Purpose**: Pre-event building inventory for damage assessment

---

## Attribute Definitions

| Attribute | Type | Required | Pre-Event Value | Description | Notes |
|-----------|------|----------|-----------------|-------------|-------|
| **ROOFTOPGEO** | String | No | `NULL` | Rooftop geometry (WKT) | Leave empty |
| **PARCELWKT** | String | No | `NULL` | Parcel geometry as WKT | Leave empty |
| **PEID** | String | No | `NULL` | Property/Parcel ID | Leave empty |
| **LAYERNAME** | String | **YES** ⚠️ | From AOI | Layer name | `"graysky"` or `"graysky-suncorp"` |
| **CAPTURE_PROJECT** | String | No | `NULL` | Capture project identifier | Leave empty |
| **CHILD_AOI** | String | **YES** ⚠️ | From AOI | Event AOI identifier | Example: `"au-nsw-coffsharbour-hail-2021"` |
| **ROOFSOLAR** | String | No | `NULL` | Solar panel presence | Leave empty |
| **ROOFWATERHEATER** | String | No | `NULL` | Water heater presence | Leave empty |
| **ROOFSOLARPANELDAMAGE** | Boolean | **YES** ⚠️ | `False` | Solar panel damage flag | **Always False** (pre-event) |
| **ROOFWATERHEATERDAMAGE** | Boolean | **YES** ⚠️ | `False` | Water heater damage flag | **Always False** (pre-event) |
| **TARPONROOF** | Float | No | `NULL` | Tarp on roof flag | Leave empty |
| **geometry** | MultiPolygon | **YES** ⚠️ | From Arturo | Building footprint | From structures layer |

---

## Damage Attributes (Post-Event Context)

### ROOFSOLARPANELDAMAGE
- **Type**: Boolean
- **Description**: Binary output if solar panel on roof is damaged
- **Scope**: Not included in CATASTROPHESCORE or DAMAGE_LEVEL
- **Peril**: Filled for hail events only
- **Pre-Event Value**: `False` (no damage yet)
- **Post-Event Values**: `True` or `False`

### ROOFWATERHEATERDAMAGE
- **Type**: Boolean
- **Description**: Binary output if water heater on roof is damaged
- **Scope**: Not included in CATASTROPHESCORE or DAMAGE_LEVEL
- **Peril**: Filled for hail events only
- **Pre-Event Value**: `False` (no damage yet)
- **Post-Event Values**: `True` or `False`

---

## Mapping Rules

### ✅ Required Fields

| Field | Source | Transformation |
|-------|--------|----------------|
| **LAYERNAME** | `graysky_aois.layer` | Direct copy: `"graysky"` or `"graysky-suncorp"` |
| **CHILD_AOI** | `graysky_aois.event_id` | Direct copy: `"au-qld-alfred-cyclone-224-2025"` |
| **ROOFSOLARPANELDAMAGE** | Hardcoded | Always `False` (pre-event) |
| **ROOFWATERHEATERDAMAGE** | Hardcoded | Always `False` (pre-event) |
| **geometry** | `arturo_structures.geometry` | Convert Polygon → MultiPolygon, reproject to EPSG:4326 |

### 🔲 NULL Fields (Leave Empty)

- ROOFTOPGEO
- PARCELWKT
- PEID
- CAPTURE_PROJECT
- ROOFSOLAR
- ROOFWATERHEATER
- TARPONROOF

---

## Workflow Implementation

### Step 1: AOI Selection
```python
# Load Graysky AOIs
aois = gpd.read_file('pre_event_data/input/graysky_suncorp_aois.gpkg', layer='graysky_aois')

# User selects AOI (or loop through all)
selected_aoi = aois[aois['event_id'] == 'au-qld-alfred-cyclone-224-2025']

# Extract metadata
layer_name = selected_aoi['layer'].values[0]          # "graysky-suncorp"
event_id = selected_aoi['event_id'].values[0]         # "au-qld-alfred-cyclone-224-2025"
event_name = selected_aoi['event_name'].values[0]     # "Alfred Cyclone"
aoi_geometry = selected_aoi.geometry.values[0]        # Polygon/MultiPolygon
```

### Step 2: State Matching
```python
# Determine which Australian state contains the AOI
aoi_centroid = aoi_geometry.centroid

# State boundaries (simplified approach - use centroid)
# More robust: spatial join with state boundaries
state_mapping = {
    'NSW': (-33.8688, 151.2093),  # Sydney centroid as reference
    'VIC': (-37.8136, 144.9631),  # Melbourne
    'QLD': (-27.4698, 153.0251),  # Brisbane
    # ... etc
}

# Or use bounding box to determine state
bounds = aoi_geometry.bounds
# bounds = (minx, miny, maxx, maxy)
# Determine state from coordinates

state = determine_state(aoi_centroid)  # Returns: 'NSW', 'VIC', 'QLD', etc.
```

### Step 3: Load Arturo Structures
```python
# Load structures from corresponding state GeoPackage
arturo_file = f"/Users/romanbuegler/dev/hail_damage/data/final/arturo_structuredetails_{state}_full.gpkg"

# Use bounding box filter for performance
bbox = aoi_geometry.bounds  # (minx, miny, maxx, maxy)

structures = gpd.read_file(
    arturo_file,
    layer='structures',
    bbox=bbox
)

# Reproject to EPSG:4326 if needed
if structures.crs.to_epsg() != 4326:
    structures = structures.to_crs('EPSG:4326')
```

### Step 4: Spatial Intersection
```python
# Filter structures within AOI
structures_in_aoi = structures[structures.intersects(aoi_geometry)]

print(f"Found {len(structures_in_aoi)} structures in AOI")
```

### Step 5: Schema Transformation
```python
from shapely.geometry import MultiPolygon, Polygon

def to_multipolygon(geom):
    """Convert Polygon to MultiPolygon if needed."""
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom

# Create output GeoDataFrame with target schema
output = gpd.GeoDataFrame({
    'ROOFTOPGEO': None,
    'PARCELWKT': None,
    'PEID': None,
    'LAYERNAME': layer_name,
    'CAPTURE_PROJECT': None,
    'CHILD_AOI': event_id,
    'ROOFSOLAR': None,
    'ROOFWATERHEATER': None,
    'ROOFSOLARPANELDAMAGE': False,
    'ROOFWATERHEATERDAMAGE': False,
    'TARPONROOF': None,
    'geometry': structures_in_aoi.geometry.apply(to_multipolygon)
}, crs='EPSG:4326')

# Ensure correct data types
output['ROOFSOLARPANELDAMAGE'] = output['ROOFSOLARPANELDAMAGE'].astype(bool)
output['ROOFWATERHEATERDAMAGE'] = output['ROOFWATERHEATERDAMAGE'].astype(bool)
```

### Step 6: Output Generation
```python
# Create output filename
output_file = f"pre_event_data/output/{event_name.replace(' ', '_').lower()}_pre_event.gpkg"

# Save to GeoPackage
output.to_file(output_file, driver='GPKG', layer='pre_event_structures')

print(f"✓ Saved {len(output)} structures to: {output_file}")
```

---

## Example Output

**Input:**
- AOI: Alfred Cyclone (au-qld-alfred-cyclone-224-2025)
- Layer: graysky-suncorp
- State: QLD
- Structures found: 1,234

**Output GeoPackage:**
```
File: alfred_cyclone_pre_event.gpkg
Layer: pre_event_structures
Features: 1,234
CRS: EPSG:4326

Attributes:
├── ROOFTOPGEO: NULL (all records)
├── PARCELWKT: NULL (all records)
├── PEID: NULL (all records)
├── LAYERNAME: "graysky-suncorp" (all records)
├── CAPTURE_PROJECT: NULL (all records)
├── CHILD_AOI: "au-qld-alfred-cyclone-224-2025" (all records)
├── ROOFSOLAR: NULL (all records)
├── ROOFWATERHEATER: NULL (all records)
├── ROOFSOLARPANELDAMAGE: False (all records)
├── ROOFWATERHEATERDAMAGE: False (all records)
├── TARPONROOF: NULL (all records)
└── geometry: MULTIPOLYGON (...) (1,234 unique geometries)
```

---

## Data Quality Checks

### Pre-Processing Validation:
- ✓ AOI geometry is valid
- ✓ AOI intersects with Australian state boundaries
- ✓ Arturo state GeoPackage exists and is readable
- ✓ CRS is EPSG:4326 or can be reprojected

### Post-Processing Validation:
- ✓ All required fields are populated (not NULL)
- ✓ ROOFSOLARPANELDAMAGE = False for all records
- ✓ ROOFWATERHEATERDAMAGE = False for all records
- ✓ All geometries are MultiPolygon type
- ✓ All geometries are valid
- ✓ CRS is EPSG:4326
- ✓ Feature count > 0

---

## Performance Notes

### Arturo Data Size:
- NSW: 6.1 GB (3.3M structures)
- VIC: 6.5 GB (3.3M structures)
- QLD: 3.8 GB (2.3M structures)

### Optimization Strategies:
1. **Bounding box filter**: Use `bbox` parameter in `read_file()` to load only relevant area
2. **Spatial index**: GeoPackages have built-in spatial indices
3. **Chunking**: Process large AOIs in chunks if needed
4. **Batch processing**: Process multiple small AOIs in parallel

### Expected Processing Times:
- Small AOI (<10 km²): 10-30 seconds
- Medium AOI (10-100 km²): 30-120 seconds
- Large AOI (>100 km²): 2-10 minutes

---

## CRS Information

**Source CRS (Arturo)**: EPSG:3857 (Web Mercator)
**Target CRS (Output)**: EPSG:4326 (WGS 84)

Reprojection required: Yes

```python
if structures.crs.to_epsg() != 4326:
    structures = structures.to_crs('EPSG:4326')
```

---

**Created:** 2025-10-27
**Status:** ✓ Schema defined, ready for implementation
**Next Steps:** Implement extraction and transformation script
