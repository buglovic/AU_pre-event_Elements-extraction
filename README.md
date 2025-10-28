# Pre-Event Data Extraction Workflow

## Overview
This workflow extracts Arturo building structure AND property data for Areas of Interest (AOIs) and prepares pre-event building inventories for damage assessment. AOIs can be sourced dynamically from the Vexcel Collections API or from local KML files.

**Key Features:**
- **Property Integration:** True PARCELWKT from property boundaries (not building footprints)
- **Property Features:** Pools, decks, trampolines, enclosures, sport courts
- **MFD Deduplication:** Removes duplicate structures spanning multiple parcels (~7.5% of data)
- **Footprint Regularization:** Orthogonal edge alignment and polygon simplification
- **Multi-State Support:** Automatic geographic state detection and data loading
- **75-Column Schema:** Complete pre-event damage assessment format

---

## Repository Structure

```
pre_event_data/
├── data/                          # Arturo data files (download from AWS)
│   ├── README.md                  # Data download instructions
│   ├── .gitignore                 # Excludes .gpkg files from git
│   └── arturo_*_full.gpkg         # State-level data files (not in repo)
├── input/                         # Input AOI definitions (KML files)
│   ├── .gitignore                 # Allows *.kml files
│   └── *.kml                      # Optional: Place custom KML AOI files here
├── output/                        # Generated pre-event inventories
│   └── {collection}_DA_pre-event.gpkg
├── scripts/                       # Main extraction scripts
│   ├── extract_pre_event_data.py  # Main workflow script
│   ├── config.py                  # Your local configuration (not in repo)
│   └── config.example.py          # Configuration template
└── README.md                      # This file
```

**Note:** The `data/` directory is for local use only. Download Arturo data from AWS and place it in `data/` following the instructions in `data/README.md`.

---

## Quick Start

### 1. Initial Setup

**Step 1: Download Arturo data from AWS S3**

Contact your team administrator for AWS credentials, then download the required GeoPackage files to the `data/` directory. See `data/README.md` for detailed file list and requirements.

```bash
# Example: After downloading files to data/
ls data/
# Should show: arturo_structuredetails_*.gpkg, arturo_propertydetails_*.gpkg, etc.
```

**Step 2: Configure the script**

```bash
cd scripts

# Copy configuration template
cp config.example.py config.py

# (Optional) Edit config.py if you want to change data paths
# Default is ../data which should work out of the box
```

**Step 3: Configure AOI Sources (Optional)**

The script supports two AOI sources:

1. **Vexcel Collections API** (recommended for accessing Vexcel/Graysky collections)
   ```bash
   # Set your Vexcel Data Platform credentials
   export VDP_USERNAME=your_username
   export VDP_PASSWORD=your_password
   ```

2. **Local KML Files** (for custom AOIs)
   ```bash
   # Place KML files in the input directory
   cp your_aoi.kml ../input/
   ```

**Note:** At least one source must be available. The script will show all API collections and local KML files in a unified list for selection.

**Step 4: Verify configuration**

```bash
python config.py
# Should print: ✓ Configuration is valid
```

If you see errors about missing data files, make sure you've downloaded the Arturo GeoPackage files to the `data/` directory.

### 2. Run Extraction

```bash
# Interactive mode - select AOI from list
python extract_pre_event_data.py

# Direct mode - specify AOI index
python extract_pre_event_data.py --aoi-index 8

# With verbose logging
python extract_pre_event_data.py --aoi-index 8 --verbose
```

---

## Workflow Steps

### 1. AOI Selection
The script loads AOIs from two sources:
- **Vexcel Collections API:** Dynamic collection list (requires VDP_USERNAME/VDP_PASSWORD)
- **Local KML Files:** Custom AOIs from the `input/` directory

Selection modes:
- **Interactive:** Display unified list of all available AOIs, user selects by number
- **Direct:** Specify `--aoi-index` parameter (1-N)
- Collections and KML files are presented in a numbered list [1-N]

### 2. State Detection (Geographic)
- Intersect AOI with Australian state boundaries
- Supports multi-state AOIs (e.g., border regions)
- Loads data from all intersecting states

### 3. Data Loading
- **Arturo Structures:** Building footprints with roof attributes
- **Arturo Properties:** Property parcels with feature detection
- **Solar Panels:** Rooftop solar panel geometries
- **Water Heaters:** Pool/water heater geometries
- Use bounding box filter for performance
- Combine data from multiple states if needed

### 4. Spatial Filtering
- Filter all data layers within AOI geometry
- Precise geometric intersection (not just bounding box)

### 5. Property Integration
- Join structures with properties on `parcel_id`
- Skip structures without property matches (typically <0.1%)
- Property features: pools, decks, trampolines, enclosures, sport courts

### 6. MFD Deduplication
- **Problem:** Multi-family dwellings span multiple parcels → same building appears multiple times
- **Solution:** Calculate overlap between structure and property geometries
- **Action:** Keep only the structure-property pair with largest overlap
- **Result:** ~7.5% of structures are deduplicated (varies by AOI)

### 7. Footprint Regularization
- Convert to projected CRS (auto-detect UTM zone)
- Apply orthogonal edge alignment (0°, 45°, 90°, 135°)
- Polygon simplification within 0.5m tolerance
- Merge parallel edges within 1m
- Convert back to EPSG:4326
- **Result:** ~3.2 vertices reduced per building, cleaner geometries

### 8. Schema Transformation
- Transform to 75-column pre-event schema
- Map roof materials, shapes, conditions
- Set all damage fields to 0/FALSE (pre-event)
- Detect solar panels and water heaters per building

### 9. Output Generation
- Save GeoPackage: `{collection}_DA_pre-event.gpkg`
- Save metadata JSON: `{collection}_DA_pre-event.json`
- 3 layers:
  - `pre_event_structures` (75 columns)
  - `solar_panels` (geometries)
  - `water_heaters` (geometries)

---

## Output Schema

**75 Columns** organized as:

### Core Identifiers (1-3)
- **BUILDINGS_IDS:** Arturo structure_id (UUID)
- **PEID:** Property/structure ID (same as BUILDINGS_IDS)
- **PARCELWKT:** **Property boundary** geometry as WKT (from property data, NOT building footprint!)

### Building Metadata (4-12)
- **B.CAPTURE_PROJECT:** Vexcel collection name (e.g., "au-qld-redbankplains-2024")
- **METADATAVERSION:** "3.90.1"
- **B.LAYERNAME:** "bluesky-ultra-oceania"
- **B.CAMERATECHNOLOGY:** "UltraCam_Osprey_4.1_f120"
- **B.IMGGSD:** Average GSD from pre-event imagery
- etc.

### Property Features (13-28)
**From Property Data:**
- **POOL:** TRUE/FALSE (has_pool from property)
- **POOLSCR:** NULL (no model score available)
- **POOLAREA:** Total pool area in m² (pools_total_area)
- **DECK:** TRUE/FALSE (has_wooden_deck)
- **DECKSCR:** NULL
- **TRAMPOLINE:** TRUE/FALSE (has_trampoline)
- **TRAMPSCR:** NULL
- **ENCLOSURE:** TRUE/FALSE (has_enclosure)
- **ENCLOSUSCR:** NULL
- **SPORTCOURT:** TRUE/FALSE (tennis + basketball courts)
- **SPORTSCR:** NULL
- **DIVINGBOAR:** NULL (not in Arturo data)
- **WATERSLIDE:** NULL (not in Arturo data)
- **PLAYGROUND:** NULL (not in Arturo data)

**From Structure Data:**
- **PRIMARYSTR:** TRUE/FALSE (is_primary building on parcel)

### Roof Attributes (29-40)
- **ROOFTOPGEO:** Building footprint geometry as WKT (regularized)
- **ROOFSHAPE:** gable, hip, flat, complex, shed, other
- **ROOFMATERI:** metal, tile, shingle, concrete, membrane, other
- **ROOFCONDIT:** 1.0-5.0 (mapped from good=4.0, fair=3.0, poor=2.0)
- **ROOFSOLAR:** TRUE/FALSE (detected via spatial join)
- **ROOFTREE:** Tree overhang percentage (0-100, rounded)
- **ROOFWATERHEATER:** TRUE/FALSE (detected via spatial join)

### Distance Scores (41-48)
- DST5-200, DSB5-200: All NULL (not in Arturo)

### Damage Assessment (49-57)
- **CATASTROPHESCORE:** 0 (pre-event)
- All damage percentages: 0.0
- **DAMAGE_LEVEL:** NULL

### Damage Metadata (58-65)
- **CAPTURE_PROJECT:** Graysky collection (e.g., "graydata-554")
- **LAYERNAME:** "graysky-suncorp"
- **CHILD_AOI:** Event ID (e.g., "au-qld-runawaybay-wind-2024")
- **IMGGSD:** Average GSD from post-event imagery

### Additional Fields (66-74)
- Classification keywords: NULL
- **ROOFCONDIT_STRUCTURALDAMAGEPERCEN:** 0.0

### Geometry (75)
- Building footprint polygon (EPSG:4326, **regularized**)

---

## Data Mappings

### From Arturo Structures

| Target Field | Arturo Source | Transformation |
|-------------|---------------|----------------|
| BUILDINGS_IDS | structure_id | Direct copy (UUID) |
| PEID | structure_id | Direct copy |
| B.CAPTURE_PROJECT | vexcel_collection_name | e.g., "au-qld-redbankplains-2024" |
| B.CHILD_AOI | vexcel_collection_name | Same as B.CAPTURE_PROJECT |
| ROOFTOPGEO | geometry | WKT after regularization |
| ROOFSHAPE | roof_shape_majority | Map: gable, hip, flat → same |
| ROOFMATERI | roof_material_majority | Map: metal→metal, concrete_tile→tile, asphalt_shingle→shingle |
| ROOFCONDIT | roof_condition_general | Map: good→4.0, fair→3.0, poor→2.0 |
| ROOFTREE | roof_tree_overlap_pct | Rounded to whole number |
| PRIMARYSTR | is_primary | TRUE/FALSE |

### From Arturo Properties

**Join Logic:**
- Join structures with properties on `parcel_id`
- Calculate overlap area between structure and property geometries
- **Deduplication:** If structure_id appears multiple times (MFDs), keep pair with largest overlap
- Skip structures without property match (typically <0.1%)

**Property Features:**
| Target Field | Property Source | Notes |
|-------------|----------------|-------|
| PARCELWKT | property.geometry | Property boundary (NOT building footprint!) |
| POOL | has_pool | Boolean from property detection |
| POOLAREA | pools_total_area | Total area in m² |
| DECK | has_wooden_deck | Boolean |
| TRAMPOLINE | has_trampoline | Boolean |
| ENCLOSURE | has_enclosure | Boolean (screened enclosure) |
| SPORTCOURT | has_tennis_court OR has_basketball_court | Combined |

**Missing Features:**
- All `*SCR` fields: NULL (no model confidence scores in Arturo)
- DIVINGBOAR, WATERSLIDE, PLAYGROUND: NULL (not detected by Arturo)

### From Graysky AOI

| Target Field | AOI Source | Notes |
|-------------|-----------|-------|
| CAPTURE_PROJECT | collection | e.g., "graydata-554" |
| LAYERNAME | layer | "graysky" or "graysky-suncorp" |
| CHILD_AOI | event_id | e.g., "au-qld-alfred-cyclone-224-2025" |
| B.IMGGSD | avg_gsd | Average GSD (pre-event) |
| IMGGSD | avg_gsd | Average GSD (post-event, same value) |

### Fixed Values

- METADATAVERSION: "3.90.1"
- B.LAYERNAME: "bluesky-ultra-oceania"
- B.CAMERATECHNOLOGY: "UltraCam_Osprey_4.1_f120"
- All damage scores: 0 or FALSE
- All distance scores: NULL

---

## Directory Structure

```
pre_event_data/
├── README.md                              # This file
├── scripts/
│   ├── extract_pre_event_data.py          # Main extraction script
│   ├── config.py                          # Local configuration (not in repo)
│   ├── config.example.py                  # Configuration template
│   └── test_footprint_regularization.py   # Regularization testing tool (if present)
├── input/
│   ├── .gitignore                         # Allows *.kml files
│   └── *.kml                              # Optional: Custom AOI files
├── output/                                # Generated outputs
│   ├── {collection}_DA_pre-event.gpkg     # Example output
│   ├── {collection}_DA_pre-event.json     # Metadata JSON
│   └── ... (one pair per extraction)
└── data/                                  # Arturo data (not in repo)
    └── arturo_*_full.gpkg                 # Downloaded from AWS
```

---

## Data Sources

### Input Data

**AOIs (Areas of Interest):**

Two sources are supported:

1. **Vexcel Collections API** (dynamic, requires credentials)
   - Real-time access to Graysky post-event collections
   - Configuration: Set `VDP_USERNAME` and `VDP_PASSWORD` environment variables
   - Fetches collection name, ID, and geometry
   - Queries Graysky layers: graysky, graysky-suncorp
   - Coverage: Australia and New Zealand

2. **Local KML Files** (optional, for custom AOIs)
   - Location: `input/*.kml`
   - Place custom AOI KML files in the input directory
   - Geometry loaded from KML on startup
   - Useful for testing or custom regions

**Arturo Structure Details:**
- Location: `data/arturo_structuredetails_{STATE}_full.gpkg` (download from AWS S3)
- Layer: `structures`
- Coverage:
  - NSW: 3.3M structures (6.1 GB)
  - VIC: 3.3M structures (6.5 GB)
  - QLD: 2.3M structures (3.8 GB)
  - WA, SA, ACT, TAS, NT: 1.9M structures total

**Arturo Property Details:**
- Location: `data/arturo_propertydetails_{STATE}_full.gpkg` (download from AWS S3)
- Layer: `parcels`
- Columns: 63 (property boundaries + feature detection)
- Features: pools, decks, trampolines, enclosures, sport courts
- Join key: `parcel_id`

**Solar Panels & Water Heaters:**
- Layers: `solar_panels`, `pool_heaters` in Arturo structure files
- Used for spatial joins to detect ROOFSOLAR and ROOFWATERHEATER

### Output Data

**Pre-Event Building Inventories:**
- Location: `output/`
- Format: GeoPackage (.gpkg) + metadata JSON (.json)
- Naming: `{collection}_DA_pre-event.gpkg` (e.g., `graydata-554_DA_pre-event.gpkg`)
- Metadata: CATASTROPHE_DEFAULT.1.0.5 schema with batch_id, creation_date, capture_project, WKT

---

## Performance

### Processing Times

**Typical Performance:**
- Small AOI (<10 km², ~5K structures): 8-15 seconds
- Medium AOI (10-50 km², ~30K structures): 20-40 seconds
- Large AOI (>100 km², ~70K structures): 60-120 seconds

**Breakdown (30K structures):**
- Data loading: ~2 seconds
- Spatial filtering: ~2 seconds
- Property join: ~1 second
- **MFD deduplication:** ~0.6 seconds
- **Footprint regularization:** ~6 seconds (5,271 buildings/sec)
- Schema transformation: ~10 seconds
- Output writing: ~1 second

### Example Results

**AU Christmas Storms (graydata-554):**
- Area: 66.80 km²
- Input: 33,032 structures (with MFD duplicates)
- Deduplicated: 30,545 unique structures (2,483 removed, 7.5%)
- Regularization: 96,913 vertices reduced (3.2 per building)
- Output: 30,545 structures, 19,821 solar panels, 3,849 water heaters
- Processing time: ~35 seconds
- File size: ~56 MB

**Alfred Cyclone (graydata-735):**
- Area: 1,175 km²
- Expected: ~70K structures
- Processing time: ~90 seconds
- File size: ~130 MB

### Regularization Statistics

- **Vertex reduction:** Average 3.2 vertices per building
- **Processing rate:** 5,000-6,000 buildings/second (parallel processing)
- **Area preservation:** Mean change <3% (very accurate)
- **Orthogonal edges:** Cleaner 90° and 45° angles
- **Low IoU warnings:** ~0.5% of buildings (original returned for poor fits)

---

## Installation & Dependencies

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/AU_pre-event_Elements-extraction.git
cd AU_pre-event_Elements-extraction
```

### 2. Install Required Libraries

```bash
# Core dependencies
pip install geopandas pandas shapely fiona pyogrio

# Building regularization (required for footprint processing)
pip install git+https://github.com/DPIRD-DMA/Building-Regulariser.git
```

### 4. Configure Data Paths

```bash
cd scripts
cp config.example.py config.py
# (Optional) Edit config.py if you need to change the data path
# Default is ../data which points to the data/ directory in the repository
```

See [Quick Start](#quick-start) section for detailed setup instructions.

---

## AOI Sources

### Vexcel Collections API

When `VDP_USERNAME` and `VDP_PASSWORD` are configured, the script dynamically fetches available collections from the Vexcel Data Platform API v2. This includes:
- **Graysky layers**: graysky, graysky-suncorp (post-event damage assessment)
- Real-time availability (no static list needed)
- Collection metadata and geometries
- Coverage: Australia and New Zealand

**Advantages:**
- Always up-to-date with latest event collections
- No local storage of collection metadata
- Access to all Graysky post-event damage assessment collections
- Automatic deduplication across layers

### Local KML Files

Custom AOI files can be placed in the `input/` directory for:
- Testing with specific regions
- Custom event boundaries
- Offline usage (when API is unavailable)

**Format Requirements:**
- File extension: `.kml`
- Must contain valid geometry (Polygon or MultiPolygon)
- Optional: Include a `<name>` tag for display

**Usage:**
Run `python extract_pre_event_data.py` to see the complete list of available AOIs from both sources.

---

## State Detection

### Geographic Intersection Method

Uses bounding boxes from actual Arturo data coverage:

```python
STATE_BOUNDS = {
    "NSW": (141.88, -36.12, 153.64, -28.17),
    "VIC": (141.99, -38.63, 146.99, -34.12),
    "QLD": (145.60, -28.57, 153.55, -16.72),
    "WA":  (115.58, -33.45, 116.32, -31.49),
    "SA":  (137.50, -35.59, 140.80, -32.47),
    "ACT": (148.97, -35.48, 149.23, -35.14),
    "TAS": (145.65, -43.11, 147.53, -40.95),
    "NT":  (130.82, -12.63, 131.18, -12.35)
}
```

### Multi-State Support

- AOI geometry intersects with state boundaries
- Loads and combines data from all intersecting states
- Deduplicates structures appearing in multiple state datasets
- Example: Border regions between NSW/VIC

---

## Troubleshooting

### "config.py not found"
- **Error:** `config.py not found! Please create it from config.example.py`
- **Solution:** Copy the template: `cp config.example.py config.py`
- **Note:** The default configuration uses `../data` which should work if you've placed Arturo data in the `data/` directory

### "ARTURO_DATA_DIR does not exist"
- **Error:** Configuration validation fails with path error
- **Solution:** The default `ARTURO_DATA_DIR` is `../data` (relative to scripts/ directory)
- **Fix:** Make sure you've downloaded Arturo data files to the `data/` directory in the repository root
- **Verify:** Run `python config.py` to validate configuration
- **Alternative:** Edit `config.py` to point to a different location, or set environment variable: `export ARTURO_DATA_DIR=/path/to/data`

### "No Arturo state GeoPackage files found"
- **Error:** No `arturo_structuredetails_*_full.gpkg` files found in data directory
- **Solution:** Download Arturo data from AWS S3 (contact team for credentials)
- **Expected files:** `arturo_structuredetails_{STATE}_full.gpkg` where STATE = NSW, VIC, QLD, WA, SA, TAS, NT, ACT

### "No structures found within AOI bounds"
- Check if AOI is in Australia/NZ (script only covers these regions)
- Verify Arturo data exists for the determined state
- Check if AOI geometry is valid
- Try `--verbose` to see detailed state detection

### "Skipped X structures without property matches"
- Normal: <0.1% of structures may not have property data
- Not critical: These structures are excluded from final output
- Cause: Property boundaries don't overlap with structure footprint

### "Removed X duplicate structures (MFDs)"
- Normal: 5-10% of structures in urban areas
- Cause: Multi-family dwellings spanning multiple parcels
- Solution: Keeps the best property match (largest overlap)

### "Low IoU warnings" during regularization
- Normal: ~0.5% of complex buildings
- Cause: Regularization changes geometry too much
- Solution: Original geometry is automatically kept for these cases

### Slow Performance
- Large AOIs (>100 km²) take several minutes
- Use `--verbose` flag to monitor progress
- Consider processing in smaller sub-regions
- Regularization takes ~2-6 seconds per 10K structures

### Memory Issues
- Very large AOIs (>200K structures) may need 16+ GB RAM
- Property join and regularization are memory-intensive
- Consider filtering by smaller geographic regions
- Close other applications to free memory

---

## Validation

### Output Validation

```bash
# Check layers
ogrinfo output/graydata-554_DA_pre-event.gpkg

# Validate schema (should show 75 columns)
ogrinfo -al -so output/graydata-554_DA_pre-event.gpkg pre_event_structures | grep ": "

# Check for duplicates
python3 -c "
import geopandas as gpd
gdf = gpd.read_file('output/graydata-554_DA_pre-event.gpkg', layer='pre_event_structures')
print(f'Total structures: {len(gdf):,}')
print(f'Unique PEIDs: {gdf[\"PEID\"].nunique():,}')
print(f'Duplicates: {len(gdf) - gdf[\"PEID\"].nunique()}')
"

# Verify regularization
python3 -c "
import geopandas as gpd
from shapely.geometry import Polygon
gdf = gpd.read_file('output/graydata-554_DA_pre-event.gpkg', layer='pre_event_structures')
vertices = gdf.geometry.apply(lambda g: len(g.exterior.coords) if isinstance(g, Polygon) else 0)
print(f'Mean vertices per building: {vertices.mean():.1f}')
print(f'Median vertices: {vertices.median():.0f}')
"
```

### Metadata Validation

```bash
# Check metadata JSON
cat output/graydata-554_DA_pre-event.json | python3 -m json.tool

# Should contain:
# - batch_id: "graydata-554_DA_pre-event"
# - creation_date: ISO timestamp
# - capture_project: "graydata-554"
# - wkt: AOI geometry
# - schema_version: "CATASTROPHE_DEFAULT.1.0.5"
```

---

## Schema Documentation

Detailed documentation available:

- **`FINAL_SCHEMA_REFERENCE.md`** - Complete 75-column schema with descriptions
- **`FINAL_MAPPINGS.md`** - All attribute mappings (Arturo → Output)
- **`MAPPING_DECISIONS_FINAL.md`** - Mapping decisions log
- **`PROPERTY_MAPPINGS_FINAL.md`** - Property feature mappings

---

## Status

✅ **Production Ready** (Version 2.0)

**Implemented Features:**
- [x] 56 Graysky-Suncorp AOIs available
- [x] Geographic state detection (multi-state support)
- [x] Property data integration (PARCELWKT, features)
- [x] MFD deduplication (7.5% duplicates removed)
- [x] Footprint regularization (orthogonal alignment)
- [x] 75-column schema implemented
- [x] Solar panel & water heater detection
- [x] All damage fields set to pre-event values (0/FALSE)
- [x] 3 geometry layers per output
- [x] Metadata JSON files (CATASTROPHE_DEFAULT.1.0.5)
- [x] Tested with multiple AOIs

**Recent Updates (2025-10-28):**
- ✨ Added property integration (true PARCELWKT from property boundaries)
- ✨ Added property features (pools, decks, trampolines, enclosures, sport courts)
- ✨ Added MFD deduplication (removes structures spanning multiple parcels)
- ✨ Added footprint regularization (orthogonal edge alignment, vertex reduction)
- ✨ Changed output naming: `{collection}_DA_pre-event.gpkg`
- ✨ Added metadata JSON: `{collection}_DA_pre-event.json`

**Last Updated:** 2025-10-28
**Version:** 2.2
**Author:** Roman Buegler

---

## Next Steps

### Immediate
1. ✅ Property integration - COMPLETE
2. ✅ MFD deduplication - COMPLETE
3. ✅ Footprint regularization - COMPLETE
4. ⏳ Batch processing for all 56 AOIs

### Future Enhancements
5. Post-event damage assessment workflow
6. Change detection (pre-event vs post-event)
7. FEMA damage level classification
8. Automated quality control reports

---

## Support

For issues or questions:
- Check this README first
- Review schema documentation files
- Use `--verbose` flag for detailed logging
- Check output validation scripts above

---

## Changelog

### Version 2.2 (2025-10-28) - Dynamic AOI Sources with VexcelClient
- **Major:** Dual AOI source system using VexcelClient
  - **Vexcel Collections API:** Real-time collection fetching (requires VDP_USERNAME/VDP_PASSWORD)
  - **Local KML Files:** Custom AOIs from input/ directory
  - Unified selection interface (API collections + KML files)
  - Pre-loads geometry for both API and KML sources
- **Refactored:** Vexcel API integration
  - Uses existing `VexcelClient` from vexcel_ortho_skill
  - Queries Graysky layers only: graysky, graysky-suncorp
  - Extended coverage: Australia AND New Zealand
  - Automatic deduplication across layers
  - Consistent authentication with other project scripts
- **Changed:** AOI selection workflow
  - Removed static `graysky_suncorp_aois.gpkg` file
  - Replaced `load_aois()` with `load_all_aois()`
  - Simplified `get_aoi_geometry()` (geometry pre-loaded)
  - Updated `display_aois()` for unified list display
- **Updated:** Configuration
  - Changed from `VEXCEL_API_KEY` to `VDP_USERNAME`/`VDP_PASSWORD`
  - Added `KML_INPUT_DIR` path configuration
  - Removed `AOI_FILE` constant
- **Improved:** Flexibility
  - Works with or without VDP credentials (KML fallback)
  - Supports custom/test AOIs via KML
  - Always up-to-date with latest Graysky event collections
  - Extended geographic coverage: Australia AND New Zealand
- **Fixed:** KML geometry handling
  - Only loads Polygon/MultiPolygon geometries from KML files
  - Skips Point and LineString geometries
  - Supports KML files with multiple placemarks
- **Fixed:** MFD deduplication crash with empty DataFrames
  - Added early exit check when no structures found
- **Improved:** Clean console output
  - Suppressed Building Regulariser IoU warnings
  - Replaced deprecated `unary_union` with `union_all()` for Shapely
  - No deprecation warnings in output

### Version 2.1 (2025-10-28) - GitHub Release Preparation
- **Major:** Configurable data paths via `config.py`
  - No hardcoded paths to external directories
  - Environment variable support for `ARTURO_DATA_DIR`
  - Template-based configuration (`config.example.py`)
  - Configuration validation on startup
- **Added:** Optional feature toggles in config
  - `ENABLE_REGULARIZATION` (default: True)
  - `ENABLE_MFD_DEDUPLICATION` (default: True)
  - Configurable regularization parameters
- **Improved:** Documentation for external users
  - AWS data source instructions
  - Detailed setup and installation steps
  - Configuration troubleshooting section

### Version 2.0 (2025-10-28)
- **Major:** Property data integration
  - PARCELWKT now from property boundaries (not building footprints)
  - Property features: pools, decks, trampolines, enclosures, sport courts
- **Major:** MFD deduplication
  - Removes duplicate structures spanning multiple parcels (~7.5%)
  - Keeps best property match based on geometry overlap
- **Major:** Footprint regularization
  - Orthogonal edge alignment (0°, 45°, 90°, 135°)
  - Polygon simplification (average 3.2 vertices reduced per building)
  - Processing: 5,000+ buildings/second
- **Changed:** Output naming from `{event}_pre_event_*.gpkg` to `{collection}_DA_pre-event.gpkg`
- **Added:** Metadata JSON files (CATASTROPHE_DEFAULT.1.0.5 schema)

### Version 1.0 (2025-10-27)
- Initial production release
- 56 Graysky-Suncorp AOIs
- Geographic state detection
- 75-column schema
- Solar panel & water heater detection
