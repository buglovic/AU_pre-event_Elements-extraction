# Final Merged Arturo Property Details GeoPackages - Australia State Datasets
## Complete Property-Level Features with Vexcel Imagery Matching

## Overview

This directory contains the **final, production-ready** merged GeoPackage files for all Australian states and territories. Each file consolidates parcel-level extractions into a single unified dataset containing property boundaries, measurements, topography, and ground features from Arturo aerial imagery analysis, enriched with Vexcel collection metadata.

These datasets represent the complete output of the Arturo property details extraction pipeline, combining data from multiple regional batches with spatial-temporal Vexcel imagery matching.

## Contents

### File Inventory

| File | State/Territory | Size | Parcels | Total Features |
|------|----------------|------|---------|----------------|
| `arturo_NSW_property_details.gpkg` | New South Wales | 11 GB | 2,061,017 | 8,121,997 |
| `arturo_QLD_property_details.gpkg` | Queensland | 8.7 GB | 1,703,881 | 6,387,852 |
| `arturo_VIC_property_details.gpkg` | Victoria | 8.3 GB | 1,657,223 | 6,173,811 |
| `arturo_WA_property_details.gpkg` | Western Australia | 4.4 GB | 1,075,074 | 4,197,487 |
| `arturo_SA_property_details.gpkg` | South Australia | 3.3 GB | 813,657 | 3,180,152 |
| `arturo_TAS_property_details.gpkg` | Tasmania | 878 MB | 263,858 | 1,031,704 |
| `arturo_ACT_property_details.gpkg` | Australian Capital Territory | 811 MB | 149,431 | 628,038 |
| `arturo_NT_property_details.gpkg` | Northern Territory | 205 MB | 37,786 | 163,156 |

**Total Dataset Size:** ~37 GB
**Total Parcels:** 5,762,927
**Total Features (all layers):** 29,884,197
**Vexcel Match Rate:** ~85%

## Dataset Structure

### Layer Schema

Each GeoPackage contains **14 standardized layers** (8 populated for Australian data):

| Layer | Geometry Type | Description | Typical Feature Count |
|-------|---------------|-------------|---------------------|
| **parcels** ⭐ | Polygon | Property parcel boundaries with 48+ attributes | 100% (all properties) |
| **pools** | Point/Polygon | Swimming pool geometries | ~10-15% of parcels |
| **trampolines** | Point/Polygon | Trampoline features | ~5-10% of parcels |
| **sports_pitches** | Polygon | Sports pitch geometries | <1% of parcels |
| **solar_panels_ground** | Polygon | Ground-mounted solar panel installations | 50-80% of parcels |
| **wooden_decks** | Polygon | Wooden deck structures | ~3-5% of parcels |
| **driveways** | Polygon | Driveway geometries | 80-100% of parcels |
| **vehicles** | Point | Vehicle detections on property | 80-90% of parcels |

**Empty Layers** (not detected in Australian data):
- `sheds`, `garages`, `enclosures`, `accessory_dwelling_units`, `tennis_courts`, `basketball_courts`

### Coordinate Reference System (CRS)

- **Projection:** WGS 84 (EPSG:4326)
- All layers within each file share the same CRS
- Geographic coordinates (latitude, longitude)
- Suitable for global analysis and web mapping

### Attributes

#### Parcel Layer (Primary - 48 Fields)

**Identifiers:**
- `parcel_id`: Unique parcel identifier
- `gnaf_ids`: GNAF address IDs (comma-separated)
- `latitude`, `longitude`: Parcel centroid coordinates

**Location:**
- `address`: Normalized address
- `image_date`: Arturo imagery capture date
- `image_url`: Arturo image URL
- `image_provider`: Imagery source
- `image_attribution`: Attribution information

**Measurements:**
- `parcel_area`: Total parcel area (m²)
- `impervious_surface_pct`: Percentage impervious surface coverage

**Topography:**
- `ground_slope`: Slope in degrees
- `ground_slope_direction`: Cardinal direction (N, NE, E, etc.)
- `parcel_steep_slope`: Boolean flag for steep slopes
- `ground_slope_min_elevation`: Minimum elevation (m)
- `ground_slope_max_elevation`: Maximum elevation (m)
- `ground_slope_median_elevation`: Median elevation (m)

**Feature Summaries** (Boolean flags + counts + areas):
- Outbuildings: `has_shed`, `shed_ct`, `shed_area` (+ garage, enclosure, ADU)
- Recreation: `has_pool`, `pools_total_ct`, `pools_total_area` (+ trampoline, courts, pitches)
- Ground Features: `has_solar_panels_ground`, `has_wooden_deck`, `has_driveway`
- Vehicles: `has_vehicle`, `vehicle_ct`

**Vexcel Imagery Metadata (8 Fields):**
- `vexcel_collection_name`: Collection identifier (e.g., "au-nsw-sydney-2024_3101320")
- `vexcel_first_capture_date`: Collection start date
- `vexcel_last_capture_date`: Collection end date
- `vexcel_capture_date_str`: Midpoint date (YYYY-MM-DD)
- `vexcel_layer`: Vexcel layer name
- `vexcel_product_type`: Product type (Ortho, DSM, etc.)
- `vexcel_graysky_event`: Graysky event identifier (if applicable)
- `vexcel_date_diff_days`: Days between Arturo and Vexcel capture
- `vexcel_match_method`: "30day" or "60day" (matching window used)

#### Ground Feature Layers

All ground feature layers share this structure:
- `parcel_id`: Links back to parcels layer
- `feature_area`: Feature area (m²)
- `feature_type`: Feature type/subclass
- `geometry`: Feature geometry
- **+ Same 8 Vexcel metadata fields as parcels**

## Data Provenance

### Source Data
- **Imagery:** Arturo aerial imagery (2023-2024)
- **Extraction:** Arturo AI platform batch processing
- **Vexcel Collections:** Vexcel Imaging aerial collections (2023-2024)
- **Processing:** Custom Python pipeline with GeoPandas

### Processing Pipeline
1. **CSV Import:** Load Arturo batch CSV files (parcel geometries + JSON feature arrays)
2. **Vexcel Matching:** Spatial-temporal matching (±30/60 day windows)
   - Spatial: Point-in-polygon (parcel centroid → collection boundary)
   - Temporal: Best match within date window
   - Caching: ~60-70% cache hit rate for performance
3. **Feature Extraction:** Parse 14 feature types from JSON arrays
4. **Chunked Writing:** Incremental GeoPackage creation (10k-row chunks)
5. **Regional Merging:** Consolidate multi-chunk states
   - NSW: 3 chunks → 1 file
   - QLD: 2 chunks → 1 file
   - VIC: 3 chunks → 1 file
6. **Quality Validation:** Feature counts, geometry validation, Vexcel match rates

### Quality Metrics
- **Vexcel Match Rate:** ~85% (±30 day: 75-85%, ±60 day fallback: 10-15%)
- **Geometry Validity:** All features validated during extraction
- **Completeness:** Comprehensive coverage for each state
- **Processing Speed:** 150-210 parcels/second
- **Memory Efficiency:** Constant ~300MB RAM usage (chunked processing)

## Usage Examples

### QGIS / Desktop GIS

**Open in QGIS:**
```bash
# Open entire GeoPackage (all layers)
qgis arturo_NSW_property_details.gpkg

# Open specific layer
qgis arturo_NSW_property_details.gpkg|layername=parcels
```

**Add to existing QGIS project:**
1. Layer → Add Layer → Add Vector Layer
2. Select GeoPackage file
3. Choose which layers to add (select all or specific layers)

**Styling recommendations:**
- **Parcels:** Categorize by `vexcel_match_method` (30day = green, 60day = yellow, null = red)
- **Pools:** Blue fill with semi-transparency
- **Solar Panels:** Yellow/gold fill
- **Driveways:** Gray fill
- **Vehicles:** Small point symbols

### Python / GeoPandas

**Read parcels layer:**
```python
import geopandas as gpd

# Read parcels
parcels = gpd.read_file(
    'arturo_NSW_property_details.gpkg',
    layer='parcels'
)

print(f"Loaded {len(parcels):,} parcels")
print(f"CRS: {parcels.crs}")
print(f"Columns: {len(parcels.columns)}")

# Check Vexcel matches
matched = parcels['vexcel_collection_name'].notna()
print(f"Vexcel matches: {matched.sum():,} ({matched.sum()/len(parcels)*100:.1f}%)")

# Analyze by match method
match_stats = parcels['vexcel_match_method'].value_counts()
print("\nMatch methods:")
print(match_stats)
```

**Filter parcels with specific features:**
```python
import geopandas as gpd

# Load parcels
parcels = gpd.read_file(
    'arturo_QLD_property_details.gpkg',
    layer='parcels'
)

# Find parcels with pool
with_pool = parcels[parcels['has_pool'] == True]
print(f"Parcels with pool: {len(with_pool):,}")

# Find parcels with solar panels
with_solar = parcels[parcels['has_solar_panels_ground'] == True]
print(f"Parcels with solar: {len(with_solar):,}")

# Find parcels with both
both = parcels[(parcels['has_pool'] == True) &
               (parcels['has_solar_panels_ground'] == True)]
print(f"Parcels with both: {len(both):,}")
```

**Spatial analysis with ground features:**
```python
import geopandas as gpd

# Load parcels and pools
parcels = gpd.read_file('arturo_VIC_property_details.gpkg', layer='parcels')
pools = gpd.read_file('arturo_VIC_property_details.gpkg', layer='pools')

# Spatial join: which parcels have pools
parcels_with_pools = gpd.sjoin(
    parcels,
    pools,
    how='inner',
    predicate='contains'
)

# Analyze pool density by Vexcel collection
pool_by_collection = parcels_with_pools.groupby('vexcel_collection_name').size()
print(pool_by_collection.sort_values(ascending=False).head(10))
```

**Temporal analysis:**
```python
import geopandas as gpd
import matplotlib.pyplot as plt

# Load parcels
parcels = gpd.read_file('arturo_NSW_property_details.gpkg', layer='parcels')

# Filter to Vexcel matches
vexcel_matched = parcels[parcels['vexcel_date_diff_days'].notna()]

# Plot date difference distribution
plt.figure(figsize=(10, 6))
vexcel_matched['vexcel_date_diff_days'].hist(bins=50)
plt.xlabel('Days between Arturo and Vexcel capture')
plt.ylabel('Number of parcels')
plt.title('Temporal Match Quality')
plt.axvline(0, color='red', linestyle='--', label='Perfect match')
plt.axvline(-30, color='orange', linestyle='--', alpha=0.5)
plt.axvline(30, color='orange', linestyle='--', alpha=0.5)
plt.legend()
plt.savefig('temporal_match_analysis.png', dpi=300)
```

### GDAL / OGR Command Line

**List layers:**
```bash
ogrinfo arturo_NSW_property_details.gpkg
```

**Get layer statistics:**
```bash
ogrinfo -al -so arturo_NSW_property_details.gpkg parcels
```

**Query parcels with SQL:**
```bash
# Count parcels by Vexcel collection
ogrinfo arturo_NSW_property_details.gpkg \
  -sql "SELECT vexcel_collection_name, COUNT(*) as count
        FROM parcels
        GROUP BY vexcel_collection_name
        ORDER BY count DESC
        LIMIT 10"

# Find parcels with steep slopes
ogrinfo arturo_QLD_property_details.gpkg \
  -sql "SELECT parcel_id, address, ground_slope
        FROM parcels
        WHERE parcel_steep_slope = 1
        LIMIT 20"

# Find parcels with high impervious surface
ogrinfo arturo_VIC_property_details.gpkg \
  -sql "SELECT parcel_id, address, impervious_surface_pct
        FROM parcels
        WHERE impervious_surface_pct > 80.0
        LIMIT 20"
```

**Export to other formats:**
```bash
# Export parcels to GeoJSON
ogr2ogr -f GeoJSON \
  nsw_parcels.geojson \
  arturo_NSW_property_details.gpkg \
  parcels

# Export pools to Shapefile
ogr2ogr -f "ESRI Shapefile" \
  qld_pools.shp \
  arturo_QLD_property_details.gpkg \
  pools

# Export to PostGIS
ogr2ogr -f "PostgreSQL" \
  PG:"dbname=arturo user=postgres" \
  arturo_VIC_property_details.gpkg \
  -nln vic_parcels \
  parcels
```

**Filter and extract:**
```bash
# Extract parcels with Vexcel matches
ogr2ogr -f GPKG \
  nsw_vexcel_matched.gpkg \
  arturo_NSW_property_details.gpkg \
  -sql "SELECT * FROM parcels WHERE vexcel_collection_name IS NOT NULL" \
  -nln parcels_matched

# Extract large parcels (>5000 m²)
ogr2ogr -f GPKG \
  large_parcels.gpkg \
  arturo_QLD_property_details.gpkg \
  -sql "SELECT * FROM parcels WHERE parcel_area > 5000" \
  -nln large_parcels
```

### PostgreSQL / PostGIS

**Import to PostGIS:**
```bash
ogr2ogr -f "PostgreSQL" \
  PG:"host=localhost dbname=arturo user=postgres password=yourpass" \
  arturo_NSW_property_details.gpkg \
  -lco SCHEMA=property_details \
  -lco OVERWRITE=YES \
  -nln nsw_parcels \
  parcels
```

**SQL queries:**
```sql
-- Count parcels by Vexcel collection
SELECT vexcel_collection_name, COUNT(*) as count,
       AVG(parcel_area) as avg_area
FROM property_details.nsw_parcels
WHERE vexcel_collection_name IS NOT NULL
GROUP BY vexcel_collection_name
ORDER BY count DESC
LIMIT 10;

-- Find parcels with multiple features
SELECT p.parcel_id, p.address,
       p.has_pool, p.has_trampoline,
       p.has_solar_panels_ground,
       p.vexcel_collection_name
FROM property_details.nsw_parcels p
WHERE p.has_pool = TRUE
  AND p.has_trampoline = TRUE
  AND p.has_solar_panels_ground = TRUE;

-- Spatial query: parcels near a point
SELECT parcel_id, address,
       ST_Distance(geom, ST_SetSRID(ST_MakePoint(151.2, -33.8), 4326)) as distance_deg
FROM property_details.nsw_parcels
WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(151.2, -33.8), 4326), 0.01)
ORDER BY distance_deg
LIMIT 20;
```

## Analysis Use Cases

### 1. Hail Damage Risk Assessment
- **Primary Layer:** `parcels`
- **Key Attributes:** `parcel_area`, `impervious_surface_pct`, topography
- **Supporting Layers:** `pools`, `solar_panels_ground` (vulnerable assets)
- **Workflow:**
  1. Identify at-risk properties by area and features
  2. Link to Vexcel imagery for pre/post damage comparison
  3. Calculate potential damage costs based on features

### 2. Property Features Inventory
- **Primary Layer:** `parcels`
- **Analysis:**
  - Pool distribution and density
  - Solar panel adoption rates
  - Driveway coverage
  - Vehicle ownership patterns
  - Feature correlation analysis

### 3. Renewable Energy Mapping
- **Primary Layer:** `solar_panels_ground`
- **Applications:**
  - Total installed capacity estimation
  - Geographic distribution patterns
  - Adoption rates by region
  - Correlation with property characteristics

### 4. Vexcel Imagery Matching Quality
- **Primary Layer:** `parcels`
- **Key Attributes:** `vexcel_match_method`, `vexcel_date_diff_days`
- **Analysis:**
  - Match rate by collection
  - Temporal accuracy distribution
  - Coverage gap identification
  - Collection quality assessment

### 5. Property Characteristics Analysis
- **Primary Layer:** `parcels`
- **Multi-attribute Analysis:**
  - Parcel size distribution
  - Impervious surface patterns
  - Topography analysis (slope, elevation)
  - Feature co-occurrence (pool + solar, etc.)

### 6. Spatial-Temporal Analysis
- **Layers:** `parcels` + all ground features
- **Applications:**
  - Change detection (requires multiple time periods)
  - Feature evolution over time
  - Imagery collection timeline analysis
  - Capture date quality assessment

## Performance Considerations

### File Size and Loading Times
- **Large datasets (NSW, QLD, VIC):** 8-11 GB files
  - Initial load (parcels layer): 20-40 seconds depending on hardware
  - Filtering recommended for large-scale analysis
  - Use bounding box queries for regional analysis
  - Consider spatial indexing for repeated queries

### Recommended Workflows

**For large files:**
```python
# Use bounding box to load only needed area
bbox = (xmin, ymin, xmax, ymax)
parcels = gpd.read_file(
    'arturo_NSW_property_details.gpkg',
    layer='parcels',
    bbox=bbox
)
```

**For memory-constrained environments:**
```python
# Read in chunks using fiona
import fiona
import geopandas as gpd

chunk_size = 10000
chunks = []

with fiona.open('arturo_VIC_property_details.gpkg', layer='parcels') as src:
    for i, feature in enumerate(src):
        chunks.append(feature)
        if len(chunks) >= chunk_size:
            # Process chunk
            chunk_gdf = gpd.GeoDataFrame.from_features(chunks, crs=src.crs)
            # ... do analysis ...
            chunks = []
```

**For specific attribute filtering:**
```python
# Use SQL to filter before loading (very efficient)
query = "SELECT * FROM parcels WHERE has_pool = 1"
pool_parcels = gpd.read_file(
    'arturo_QLD_property_details.gpkg',
    sql=query
)
```

## Data Quality Notes

### Known Limitations
1. **Vexcel Match Coverage:** ~85% match rate (some areas lack temporal coverage)
2. **Empty Layers:** 6 layers empty for Australian data (sheds, garages, etc.)
3. **Small Feature Detection:** Very small features may be missed by Arturo
4. **Temporal Accuracy:** Capture dates approximate (±30-60 days)
5. **Occlusion:** Tree cover or structures may affect ground feature detection

### Validation Recommendations
- Cross-reference Vexcel matches with actual imagery
- Visual validation against source Arturo imagery
- Compare feature counts with expected density
- Check for geometric anomalies (self-intersections, invalid polygons)
- Verify CRS consistency across layers

### Quality Checks Performed
✅ Geometry validation (no invalid polygons)
✅ CRS consistency (EPSG:4326 across all layers)
✅ Attribute completeness (critical fields populated)
✅ Feature count verification (chunk merges validated)
✅ Vexcel collection matching (~85% success rate)
✅ Spatial index creation for performance
✅ Checkpoint/resume capability during extraction

## Maintenance and Updates

### Version Information
- **Created:** 2024-10-24
- **Source Period:** Arturo extractions from 2023-2024 imagery
- **Processing Version:** v1.0
- **Extraction Duration:** ~11.4 hours (all 8 states)
- **Merge Duration:** ~7 minutes (3 multi-chunk states)

### Update Procedure
New extractions or updated imagery require:
1. Re-run chunked extraction pipeline
2. Re-match Vexcel collections
3. Re-merge regional chunks (if applicable)
4. Validate feature counts and geometry
5. Update this README with new statistics

### File Naming Convention
```
arturo_{STATE}_property_details.gpkg
```
- `arturo`: Source platform
- `{STATE}`: Australian state/territory abbreviation (ACT, NSW, NT, QLD, SA, TAS, VIC, WA)
- `property_details`: Dataset type (parcel-level features)
- `.gpkg`: GeoPackage format

## Related Documentation

### Main Documentation
- **Complete Guide:** `../../PROPERTY_DETAILS_DOCUMENTATION.md` (comprehensive technical documentation)
- **Quick Reference:** `../../README_PROPERTY_DETAILS.md` (quick start guide)
- **Documentation Index:** `../../DOCS_INDEX.md` (navigation guide)

### Scripts
- **Extraction:** `../../scripts/extraction/extract_arturo_property_details_chunked.py`
- **Extraction Docs:** `../../scripts/extraction/README_PROPERTY_EXTRACTION.md`
- **Merge Scripts:** `../../scripts/merging/merge_state_geopackages.py`
- **Merge Docs:** `../../scripts/merging/README.md`
- **Quick Start:** `../../scripts/merging/QUICKSTART.md`
- **Master Workflow:** `../../scripts/merging/run_complete_merge_workflow.sh`

### Logs
- **Extraction Logs:** `../../logs/extraction/property_*.log`
- **Merge Logs:** `../../logs/merge_workflow_*.log`
- **Checkpoints:** `../../logs/checkpoints/*_property_checkpoint.json`

## Support and Questions

For questions about:
- **Data Content:** Review Arturo platform documentation
- **Vexcel Matching:** See `PROPERTY_DETAILS_DOCUMENTATION.md` → Vexcel Matching Logic
- **Processing Pipeline:** See extraction and merge script documentation
- **GeoPackage Format:** https://www.geopackage.org/
- **GeoPandas Usage:** https://geopandas.org/

### Troubleshooting
- **Empty layers:** Normal for Australian data (sheds, garages, tennis courts, basketball courts)
- **No Vexcel match:** Some properties outside Vexcel collection coverage
- **Large file sizes:** Use bounding box queries or SQL filters to reduce memory usage
- **Slow loading:** Consider spatial indexing or regional extraction

## License

Internal use - Hail Damage Assessment Project

---

**Last Updated:** 2024-10-24
**Maintained By:** Roman Buegler
**Project:** Hail Damage Assessment - Property Details with Vexcel Matching
**Total Processing Time:** ~12 hours (extraction + merge + validation)
