# Final Target Schema Reference

**Source File**: `graydata-736_DA_RomanFakeQA.gpkg`
**Layer**: `graydata-736_Damage_Assessment_filtered`
**Features**: 61,603 structures
**CRS**: EPSG:4326 (WGS 84)
**Geometry**: Polygon

---

## Complete Schema (74 Columns)

### 1. Core Identifiers (3 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **BUILDINGS_IDS** | String | No | Unique building identifier | From Arturo `arturo_id` |
| **PEID** | String | No | Property/Parcel ID | From Arturo `arturo_id` (duplicate) |
| **PARCELWKT** | String | No | Parcel geometry as WKT | From Arturo structures geometry |

### 2. Metadata - Building (B. prefix) (7 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **B.CAPTURE_PROJECT** | String | No | Building capture project | From AOI `collection` |
| **METADATAVERSION** | String | No | Metadata version | `"3.90.1"` (fixed) |
| **B.LAYERNAME** | String | No | Building layer name | From AOI `layer` |
| **B.IMAGEID** | String | No | Building image ID | From AOI or Arturo |
| **B.CHILD_AOI** | String | No | Building child AOI | From AOI `event_id` |
| **B.ORTHOVSNADIR** | String | No | Ortho vs Nadir | `"ortho"` (default) |
| **B.CAMERATECHNOLOGY** | String | No | Camera technology | From AOI or `"Unknown"` |

### 3. Metadata - Building Image (2 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **B.IMGDATE** | String | No | Building image date | From AOI or Arturo |
| **B.IMGGSD** | Real | No | Building image GSD | From AOI `avg_gsd` |

### 4. Property Features (18 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **POOLAREA** | Real | No | Pool area in sq meters | `0.0` |
| **TRAMPOLINE** | String | No | Trampoline presence | `"FALSE"` |
| **TRAMPSCR** | Real | No | Trampoline score | `0.0` |
| **DECK** | String | No | Deck presence | `"FALSE"` |
| **DECKSCR** | Real | No | Deck score | `0.0` |
| **POOL** | String | No | Pool presence | `"FALSE"` |
| **POOLSCR** | Real | No | Pool score | `0.0` |
| **ENCLOSURE** | String | No | Enclosure presence | `"FALSE"` |
| **ENCLOSUSCR** | Real | No | Enclosure score | `0.0` |
| **DIVINGBOAR** | String | No | Diving board presence | `"FALSE"` |
| **DIVINGSCR** | Real | No | Diving board score | `0.0` |
| **WATERSLIDE** | String | No | Water slide presence | `"FALSE"` |
| **WATSLIDSCR** | Real | No | Water slide score | `0.0` |
| **PLAYGROUND** | String | No | Playground presence | `"FALSE"` |
| **PLAYGSCR** | Real | No | Playground score | `0.0` |
| **SPORTCOURT** | String | No | Sport court presence | `"FALSE"` |
| **SPORTSCR** | Real | No | Sport court score | `0.0` |
| **PRIMARYSTR** | String | No | Primary structure flag | `"TRUE"` |

### 5. Roof Attributes (9 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **ROOFTOPGEO** | String | No | Rooftop geometry WKT | From Arturo structures geometry |
| **GROUNDELEV** | Real | Yes | Ground elevation | NULL or from Arturo |
| **DETECTSCR** | Real | No | Detection score | `1.0` |
| **ROOFSHAPE** | String | No | Roof shape | From Arturo or `"Unknown"` |
| **ROOFSHASCR** | String | Yes | Roof shape score | NULL |
| **ROOFMATERI** | String | No | Roof material | From Arturo or `"Unknown"` |
| **ROOFMATSCR** | Real | No | Roof material score | `1.0` |
| **ROOFCONDIT** | Real | No | Roof condition | `1.0` (excellent, pre-event) |
| **ROOFSOLAR** | String | No | Solar panel presence | `"NO SOLAR PANEL"` |
| **ROOFTREE** | Real | No | Tree overhang | `0.0` |

### 6. Damage Scores - Distance (8 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **DST5** | Real | No | Distance score top 5m | `0.0` |
| **DSB5** | Real | No | Distance score bottom 5m | `0.0` |
| **DST30** | Real | No | Distance score top 30m | `0.0` |
| **DSB30** | Real | No | Distance score bottom 30m | `0.0` |
| **DST100** | Real | No | Distance score top 100m | `0.0` |
| **DSB100** | Real | No | Distance score bottom 100m | `0.0` |
| **DST200** | Real | No | Distance score top 200m | `0.0` |
| **DSB200** | Real | No | Distance score bottom 200m | `0.0` |

### 7. Damage Assessment (9 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **CATASTROPHESCORE** | Integer64 | No | Catastrophe score (0-100) | `0` (no damage) |
| **ROOFCONDIT_MISSINGMATERIALPERCEN** | Real | No | Missing material percent | `0.0` |
| **ROOFCONDIT_TARPPERCEN** | Real | No | Tarp percent | `0.0` |
| **ROOFCONDIT_DEBRISPERCENT** | Real | No | Debris percent | `0.0` |
| **ROOFCONDIT_DISCOLORDETECT** | String | No | Discoloration detection | `"FALSE"` |
| **ROOFCONDIT_DISCOLORPERCEN** | Real | No | Discoloration percent | `0.0` |
| **ROOFCONDIT_DISCOLORSCORE** | Real | No | Discoloration score | `0.0` |
| **ROOFCONDIT_STRUCTURALDAMAGEPERCEN** | Real | No | Structural damage percent | `0.0` |
| **DAMAGE_LEVEL** | String | Yes | FEMA damage level | NULL (pre-event) |

### 8. Additional Scores (1 column)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **HISTOSCORE** | Real | No | Histogram score | `0.0` |

### 9. Metadata - Damage Assessment (Duplicate fields) (6 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **CAPTURE_PROJECT** | String | No | DA capture project | From AOI `collection` |
| **LAYERNAME** | String | No | DA layer name | From AOI `layer` |
| **IMAGEID** | String | No | DA image ID | From AOI |
| **CHILD_AOI** | String | No | DA child AOI | From AOI `event_id` |
| **ORTHOVSNADIR** | String | No | DA ortho vs nadir | `"ortho"` |
| **CAMERATECHNOLOGY** | String | No | DA camera technology | From AOI |

### 10. Metadata - Damage Image (2 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **IMGDATE** | String | No | DA image date | From AOI |
| **IMGGSD** | Real | No | DA image GSD | From AOI `avg_gsd` |

### 11. Classification Keywords (4 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **DSKWT5** | String | Yes | Damage keyword top 5m | NULL |
| **DSKWT30** | String | Yes | Damage keyword top 30m | NULL |
| **DSKWT100** | String | Yes | Damage keyword top 100m | NULL |
| **DSKWT200** | String | Yes | Damage keyword top 200m | NULL |

### 12. Additional Metadata (3 columns)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **task_structures_info** | Real | Yes | Task structures info | NULL |
| **structures_count** | Real | Yes | Structures count | NULL |
| **property_id** | Real | Yes | Property ID | NULL |

### 13. Geometry (1 column)

| Column | Type | Nullable | Description | Pre-Event Value |
|--------|------|----------|-------------|-----------------|
| **geometry** | Polygon | No | Building footprint | From Arturo structures |

---

## Arturo to Schema Mapping

### Direct Mappings from Arturo Structures Layer

| Target Column | Arturo Source | Transformation |
|--------------|---------------|----------------|
| BUILDINGS_IDS | `arturo_id` | Direct copy |
| PEID | `arturo_id` | Direct copy (duplicate) |
| PARCELWKT | `geometry` | Convert to WKT string |
| ROOFTOPGEO | `geometry` | Convert to WKT string |
| ROOFMATERI | `roof_material` or similar | Map to: metal, tile, shingle, membrane, shake |
| ROOFSHAPE | `roof_shape` or similar | Map to roof shape types |
| geometry | `geometry` | Keep as Polygon, CRS: EPSG:4326 |

### Mappings from Graysky AOI

| Target Column | AOI Source | Notes |
|--------------|------------|-------|
| B.CAPTURE_PROJECT | `collection` | Example: `"graydata-736"` |
| CAPTURE_PROJECT | `collection` | Duplicate field |
| B.LAYERNAME | `layer` | Example: `"graysky-suncorp"` |
| LAYERNAME | `layer` | Duplicate field |
| B.CHILD_AOI | `event_id` | Example: `"au-qld-alfred-cyclone-224-2025"` |
| CHILD_AOI | `event_id` | Duplicate field |
| B.IMGGSD | `avg_gsd` | Example: `0.12` |
| IMGGSD | `avg_gsd` | Duplicate field |

### Fixed/Default Values for Pre-Event Data

| Column | Value | Reason |
|--------|-------|--------|
| METADATAVERSION | `"3.90.1"` | Current version |
| B.ORTHOVSNADIR | `"ortho"` | All graysky data is ortho |
| ORTHOVSNADIR | `"ortho"` | Duplicate |
| PRIMARYSTR | `"TRUE"` | All structures are primary |
| DETECTSCR | `1.0` | Full detection confidence |
| ROOFCONDIT | `1.0` | Excellent condition (pre-event) |
| ROOFMATSCR | `1.0` | Full material detection |
| ROOFSOLAR | `"NO SOLAR PANEL"` | Default (no detection) |

### All Damage-Related Fields → Zero/False

All damage assessment fields must be set to zero or false for pre-event data:

```python
# Damage scores
CATASTROPHESCORE = 0
HISTOSCORE = 0.0

# Roof condition percentages
ROOFCONDIT_MISSINGMATERIALPERCEN = 0.0
ROOFCONDIT_TARPPERCEN = 0.0
ROOFCONDIT_DEBRISPERCENT = 0.0
ROOFCONDIT_DISCOLORPERCEN = 0.0
ROOFCONDIT_DISCOLORSCORE = 0.0
ROOFCONDIT_STRUCTURALDAMAGEPERCEN = 0.0
ROOFCONDIT_DISCOLORDETECT = "FALSE"

# Distance scores
DST5 = DSB5 = DST30 = DSB30 = 0.0
DST100 = DSB100 = DST200 = DSB200 = 0.0

# Property features (all false)
TRAMPOLINE = DECK = POOL = ENCLOSURE = "FALSE"
DIVINGBOAR = WATERSLIDE = PLAYGROUND = SPORTCOURT = "FALSE"
POOLAREA = 0.0
TRAMPSCR = DECKSCR = POOLSCR = ENCLOSUSCR = 0.0
DIVINGSCR = WATSLIDSCR = PLAYGSCR = SPORTSCR = 0.0

# Tree overhang
ROOFTREE = 0.0

# Damage level
DAMAGE_LEVEL = NULL
```

### NULL Fields

These fields remain NULL for pre-event data:
- ROOFSHASCR
- GROUNDELEV (unless available from Arturo)
- DSKWT5, DSKWT30, DSKWT100, DSKWT200
- task_structures_info
- structures_count
- property_id
- DAMAGE_LEVEL

---

## Data Quality Requirements

### Required Fields (Must Not Be NULL)

1. **BUILDINGS_IDS** - Unique identifier
2. **PEID** - Property ID
3. **PARCELWKT** - Parcel geometry
4. **B.CAPTURE_PROJECT** - AOI collection
5. **METADATAVERSION** - Version string
6. **B.LAYERNAME** - Layer name
7. **B.IMAGEID** - Image ID
8. **B.CHILD_AOI** - Event AOI
9. **B.ORTHOVSNADIR** - Ortho/Nadir flag
10. **B.CAMERATECHNOLOGY** - Camera type
11. **B.IMGDATE** - Image date
12. **B.IMGGSD** - Image GSD
13. **ROOFTOPGEO** - Rooftop geometry
14. **ROOFSHAPE** - Roof shape
15. **ROOFMATERI** - Roof material
16. **PRIMARYSTR** - Primary structure flag
17. **ROOFSOLAR** - Solar panel flag
18. **geometry** - Building footprint
19. All duplicate metadata fields (CAPTURE_PROJECT, LAYERNAME, etc.)
20. All damage score fields (set to 0/false)

### Geometry Requirements

- **Type**: Polygon (not MultiPolygon in this schema!)
- **CRS**: EPSG:4326
- **Validity**: All geometries must be valid
- **No self-intersections**
- **Closed rings**

### Data Type Requirements

- **Boolean strings**: `"TRUE"` or `"FALSE"` (uppercase)
- **Integer scores**: CATASTROPHESCORE (0-100)
- **Real scores**: All other scores (0.0-100.0)
- **Dates**: ISO format or consistent string format
- **WKT**: Valid Well-Known Text format

---

## Example Record (Pre-Event)

```python
{
    'BUILDINGS_IDS': 's-vrelease-12345678-abcd-11ef-1234-1234567890ab',
    'PEID': 's-vrelease-12345678-abcd-11ef-1234-1234567890ab',
    'PARCELWKT': 'POLYGON ((153.227 -27.759, ...))',
    'B.CAPTURE_PROJECT': 'graydata-736',
    'METADATAVERSION': '3.90.1',
    'B.LAYERNAME': 'graysky-suncorp',
    'B.IMAGEID': 'graydata-736_001',
    'B.CHILD_AOI': 'au-qld-alfred-cyclone-224-2025',
    'B.ORTHOVSNADIR': 'ortho',
    'B.CAMERATECHNOLOGY': 'UltraCam Osprey',
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
    'PRIMARYSTR': 'TRUE',
    'B.IMGDATE': '2025-02-15',
    'B.IMGGSD': 0.12,
    'ROOFTOPGEO': 'POLYGON ((153.227 -27.759, ...))',
    'GROUNDELEV': None,
    'DETECTSCR': 1.0,
    'ROOFSHAPE': 'gable',
    'ROOFSHASCR': None,
    'ROOFMATERI': 'metal',
    'ROOFMATSCR': 1.0,
    'ROOFCONDIT': 1.0,
    'ROOFSOLAR': 'NO SOLAR PANEL',
    'ROOFTREE': 0.0,
    'DST5': 0.0, 'DSB5': 0.0, 'DST30': 0.0, 'DSB30': 0.0,
    'DST100': 0.0, 'DSB100': 0.0, 'DST200': 0.0, 'DSB200': 0.0,
    'CATASTROPHESCORE': 0,
    'ROOFCONDIT_MISSINGMATERIALPERCEN': 0.0,
    'ROOFCONDIT_TARPPERCEN': 0.0,
    'ROOFCONDIT_DEBRISPERCENT': 0.0,
    'ROOFCONDIT_DISCOLORDETECT': 'FALSE',
    'ROOFCONDIT_DISCOLORPERCEN': 0.0,
    'ROOFCONDIT_DISCOLORSCORE': 0.0,
    'DAMAGE_LEVEL': None,
    'HISTOSCORE': 0.0,
    'CAPTURE_PROJECT': 'graydata-736',
    'LAYERNAME': 'graysky-suncorp',
    'IMAGEID': 'graydata-736_001',
    'CHILD_AOI': 'au-qld-alfred-cyclone-224-2025',
    'ORTHOVSNADIR': 'ortho',
    'CAMERATECHNOLOGY': 'UltraCam Osprey',
    'IMGDATE': '2025-02-15',
    'IMGGSD': 0.12,
    'DSKWT5': None, 'DSKWT30': None, 'DSKWT100': None, 'DSKWT200': None,
    'task_structures_info': None,
    'structures_count': None,
    'property_id': None,
    'ROOFCONDIT_STRUCTURALDAMAGEPERCEN': 0.0,
    'geometry': <Polygon>
}
```

---

**Created:** 2025-10-27
**Based On:** graydata-736_DA_RomanFakeQA.gpkg (61,603 features)
**Status:** ✓ Complete schema documented, ready for implementation
