# Final Merged Arturo GeoPackages - Australia State Datasets
## Complete Structure Details Export

## Overview

This directory contains the **final, production-ready** merged GeoPackage files for all Australian states and territories. Each file consolidates regional extractions into a single unified dataset containing building structures and related features from Arturo aerial imagery analysis.

These datasets represent the complete output of the Arturo extraction pipeline, combining data from multiple regional batches with matched Vexcel collection metadata.

## Contents

### File Inventory

| File | State/Territory | Size | Structures | Total Features |
|------|----------------|------|------------|----------------|
| `arturo_structuredetails_NSW_full.gpkg` | New South Wales | 6.1 GB | 3,283,957 | 8,902,814 |
| `arturo_structuredetails_VIC_full.gpkg` | Victoria | 6.5 GB | 3,345,201 | 9,973,461 |
| `arturo_structuredetails_QLD_full.gpkg` | Queensland | 3.8 GB | 2,339,286 | 6,058,215 |
| `arturo_structuredetails_WA_full.gpkg` | Western Australia | 2.6 GB | ~837,520 | ~2.5M |
| `arturo_structuredetails_SA_full.gpkg` | South Australia | 1.7 GB | ~648,073 | ~2.0M |
| `arturo_structuredetails_ACT_full.gpkg` | Australian Capital Territory | 604 MB | ~149,431 | ~450K |
| `arturo_structuredetails_TAS_full.gpkg` | Tasmania | 461 MB | ~184,056 | ~550K |
| `arturo_structuredetails_NT_full.gpkg` | Northern Territory | 107 MB | ~56,250 | ~170K |

**Total Dataset Size:** ~22 GB
**Total Structures:** ~10.8 Million
**Total Features (all layers):** ~30+ Million

## Dataset Structure

### Layer Schema

Each GeoPackage contains **9 standardized layers**:

| Layer | Geometry Type | Description | Typical Use Case |
|-------|---------------|-------------|------------------|
| **structures** | Polygon | Building footprints with attributes (area, perimeter, etc.) | Primary building inventory, spatial analysis |
| **verandas** | Polygon | Veranda and porch structures | Secondary structure analysis, roof coverage |
| **ac_units** | Polygon | Air conditioning unit locations | HVAC infrastructure mapping |
| **chimneys** | Polygon | Chimney structures | Heating infrastructure, building age indicators |
| **skylights** | Polygon | Skylight features | Natural lighting analysis, roof features |
| **pool_heaters** | Polygon | Pool heating equipment | Amenity mapping, energy usage indicators |
| **solar_panels** | Polygon | Solar panel installations | Renewable energy mapping, sustainability analysis |
| **roof_conditions** | Multi Polygon | Roof condition assessments | Maintenance prioritization, damage assessment |
| **roof_extensions** | Polygon | Additional roof structures | Complex roof analysis |

### Coordinate Reference System (CRS)

- **Projection:** WGS 84 / Pseudo-Mercator (EPSG:3857)
- All layers within each file share the same CRS
- Suitable for web mapping and spatial analysis

### Attributes

Each feature includes:
- **Geometry:** Polygon or Multi Polygon
- **arturo_id:** Unique Arturo identifier
- **parcel_id:** Property parcel identifier
- **Geometric attributes:** Area, perimeter, bounds
- **vexcel_collection:** Matched Vexcel imagery collection name
- **capture_date:** Approximate date of imagery capture
- **Additional layer-specific attributes**

## Data Provenance

### Source Data
- **Imagery:** Vexcel aerial imagery (2023-2024)
- **Extraction:** Arturo AI platform
- **Processing:** Custom Python pipeline with GeoPandas

### Processing Pipeline
1. **Extraction:** Arturo batch processing of aerial imagery
2. **Geometry Extraction:** Conversion of Arturo JSON to GeoPackage
3. **Vexcel Matching:** Temporal matching of structures to imagery collections (±30/60 day windows)
4. **Regional Merging:** Consolidation of regional extractions (e.g., NSW_1 + NSW_2 + NSW_3)
5. **Quality Validation:** Feature count verification, geometry validation

### Quality Metrics
- **Vexcel Match Rate:** 99.7-100% for most states
- **Geometry Validity:** All features validated during extraction
- **Completeness:** Comprehensive coverage for each state

## Usage Examples

### QGIS / Desktop GIS

**Open in QGIS:**
```bash
# Open entire GeoPackage (all layers)
qgis arturo_structuredetails_NSW_full.gpkg

# Open specific layer
qgis arturo_structuredetails_NSW_full.gpkg|layername=structures
```

**Add to existing QGIS project:**
1. Layer → Add Layer → Add Vector Layer
2. Select GeoPackage file
3. Choose which layers to add

### Python / GeoPandas

**Read specific layer:**
```python
import geopandas as gpd

# Read structures layer
gdf = gpd.read_file(
    'arturo_structuredetails_NSW_full.gpkg',
    layer='structures'
)

print(f"Loaded {len(gdf):,} structures")
print(f"CRS: {gdf.crs}")
print(f"Columns: {gdf.columns.tolist()}")

# Basic analysis
total_area = gdf.geometry.area.sum()
print(f"Total structure area: {total_area/1e6:.2f} sq km")
```

**Read multiple layers:**
```python
import geopandas as gpd

layers = ['structures', 'solar_panels', 'ac_units']
data = {}

for layer in layers:
    data[layer] = gpd.read_file(
        'arturo_structuredetails_VIC_full.gpkg',
        layer=layer
    )
    print(f"{layer}: {len(data[layer]):,} features")
```

**Spatial queries:**
```python
import geopandas as gpd
from shapely.geometry import Point

# Read structures
structures = gpd.read_file(
    'arturo_structuredetails_QLD_full.gpkg',
    layer='structures'
)

# Find structures near a point
point = Point(153.0, -27.5)  # Brisbane area
buffer = point.buffer(0.01)  # ~1km buffer

nearby = structures[structures.intersects(buffer)]
print(f"Found {len(nearby)} structures nearby")
```

### GDAL / OGR Command Line

**List layers:**
```bash
ogrinfo arturo_structuredetails_NSW_full.gpkg
```

**Get layer info:**
```bash
ogrinfo -al -so arturo_structuredetails_NSW_full.gpkg structures
```

**Export to other formats:**
```bash
# Export structures to GeoJSON
ogr2ogr -f GeoJSON \
  nsw_structures.geojson \
  arturo_structuredetails_NSW_full.gpkg \
  structures

# Export to Shapefile
ogr2ogr -f "ESRI Shapefile" \
  nsw_structures.shp \
  arturo_structuredetails_NSW_full.gpkg \
  structures

# Export to PostGIS
ogr2ogr -f "PostgreSQL" \
  PG:"dbname=mydb user=myuser" \
  arturo_structuredetails_NSW_full.gpkg \
  -nln arturo_structures
```

**Filter and extract:**
```bash
# Extract structures larger than 1000 sq meters
ogr2ogr -f GPKG \
  large_structures.gpkg \
  arturo_structuredetails_NSW_full.gpkg \
  -sql "SELECT * FROM structures WHERE area > 1000" \
  -nln large_structures
```

### PostgreSQL / PostGIS

**Import to PostGIS:**
```bash
ogr2ogr -f "PostgreSQL" \
  PG:"host=localhost dbname=arturo user=postgres password=yourpass" \
  arturo_structuredetails_NSW_full.gpkg \
  -lco SCHEMA=arturo \
  -lco OVERWRITE=YES \
  -nln nsw_structures \
  structures
```

**SQL queries:**
```sql
-- Count structures by Vexcel collection
SELECT vexcel_collection, COUNT(*) as count
FROM arturo.nsw_structures
GROUP BY vexcel_collection
ORDER BY count DESC;

-- Find structures with solar panels
SELECT s.arturo_id, s.area, s.vexcel_collection
FROM arturo.nsw_structures s
WHERE EXISTS (
  SELECT 1 FROM arturo.nsw_solar_panels sp
  WHERE ST_Intersects(s.geom, sp.geom)
);
```

## Analysis Use Cases

### 1. Hail Damage Assessment
- **Primary Layer:** `roof_conditions`
- **Supporting Layers:** `structures`, `roof_extensions`
- **Workflow:**
  1. Identify damaged roof areas from `roof_conditions`
  2. Cross-reference with `structures` for building size/value
  3. Calculate damage severity and repair estimates

### 2. Solar Panel Deployment Analysis
- **Primary Layer:** `solar_panels`
- **Analysis:**
  - Total installed capacity estimation
  - Geographic distribution patterns
  - Correlation with building characteristics
  - Renewable energy potential assessment

### 3. Building Inventory & Census
- **Primary Layer:** `structures`
- **Attributes:**
  - Building count per region
  - Total built-up area
  - Structure size distribution
  - Density mapping

### 4. Infrastructure Mapping
- **Layers:** `ac_units`, `pool_heaters`, `chimneys`
- **Applications:**
  - HVAC infrastructure assessment
  - Energy demand estimation
  - Amenity distribution analysis

### 5. Property Insurance Risk Assessment
- **Multi-layer Analysis:**
  - Structure footprint (replacement value proxy)
  - Roof conditions (maintenance risk)
  - Additional structures (coverage requirements)
  - Solar panels (valuable assets)

## Performance Considerations

### File Size and Loading Times
- **Large datasets (NSW, VIC):** 6+ GB files
  - Initial load: 10-30 seconds depending on hardware
  - Filtering recommended for large-scale analysis
  - Consider spatial indexing for repeated queries

### Recommended Workflows

**For large files:**
```python
# Use bounding box to load only needed area
bbox = (xmin, ymin, xmax, ymax)
gdf = gpd.read_file(
    'arturo_structuredetails_NSW_full.gpkg',
    layer='structures',
    bbox=bbox
)
```

**For memory-constrained environments:**
```python
# Process in chunks
import fiona

with fiona.open('arturo_structuredetails_VIC_full.gpkg', layer='structures') as src:
    for i, feature in enumerate(src):
        if i % 10000 == 0:
            print(f"Processed {i} features")
        # Process feature
```

## Data Quality Notes

### Known Limitations
1. **Coverage Gaps:** Some remote areas may have incomplete coverage
2. **Temporal Accuracy:** Capture dates approximate (±30-60 days)
3. **Small Structure Detection:** Very small structures (<5 sq m) may be missed
4. **Occlusion:** Tree cover or clouds may affect detection

### Validation Recommendations
- Cross-reference with cadastral data for parcel-level accuracy
- Visual validation against source imagery recommended
- Edge cases near state boundaries may require manual review

### Quality Checks Performed
✅ Geometry validation (no self-intersections, invalid polygons)
✅ CRS consistency across layers
✅ Attribute completeness (non-null critical fields)
✅ Feature count verification against source data
✅ Vexcel collection matching (>99% success rate)

## Maintenance and Updates

### Version Information
- **Created:** 2024-10-23 to 2024-10-24
- **Source Period:** Arturo extractions from 2023-2024 imagery
- **Processing Version:** v1.0

### Update Procedure
New extractions or updated imagery require:
1. Re-run extraction pipeline
2. Re-match Vexcel collections
3. Re-merge regional datasets
4. Validate against previous version
5. Update this README with new statistics

### File Naming Convention
```
arturo_structuredetails_{STATE}_full.gpkg
```
- `arturo`: Source platform
- `structuredetails`: Dataset type
- `{STATE}`: Australian state/territory abbreviation (NSW, VIC, QLD, etc.)
- `full`: Indicates complete merged dataset
- `.gpkg`: GeoPackage format

## Related Documentation

- **Extraction Pipeline:** `../extract_arturo_geometries.py`
- **Merge Scripts:** `../merge_nsw_geopackages.py`, `../merge_vic_geopackages.py`
- **Merge Documentation:** `../MERGE_SCRIPTS_README.md`
- **Extraction Logs:** `../output/*.log`

## Support and Questions

For questions about:
- **Data Content:** Review Arturo documentation
- **Processing Pipeline:** See extraction and merge script documentation
- **GeoPackage Format:** https://www.geopackage.org/
- **GeoPandas Usage:** https://geopandas.org/

## License

Internal use - Hail Damage Assessment Project

---

**Last Updated:** 2024-10-24
**Maintained By:** Roman Buegler
**Project:** Hail Damage Assessment - Australian Building Inventory
