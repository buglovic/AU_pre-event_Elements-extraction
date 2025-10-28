# Final Mapping Decisions - CONFIRMED

## ✅ All Questions Answered

---

### 1. Building Identifiers ✓
**DECISION:** Use `arturo.structure_id` for both BUILDINGS_IDS and PEID

```python
BUILDINGS_IDS = arturo.structure_id
PEID = arturo.structure_id  # Same value
```

---

### 2. Image Metadata ✓
**DECISION:** Leave **empty/NULL**

```python
B.IMAGEID = None  # Leave empty
IMAGEID = None    # Leave empty
```

---

### 3. Camera Technology ✓
**DECISION:** Hardcode `"UltraCam_Osprey_4.1_f120"`

```python
B.CAMERATECHNOLOGY = "UltraCam_Osprey_4.1_f120"
CAMERATECHNOLOGY = "UltraCam_Osprey_4.1_f120"
```

---

### 4. Image Date Format ✓
**DECISION:** Leave **empty/NULL**

```python
B.IMGDATE = None  # Leave empty
IMGDATE = None    # Leave empty
```

---

### 5. Roof Material Mapping ✓
**DECISION:** Map to 5 categories: gravel, membrane, metal, shake, shingle

**Mapping Table:**
```python
ROOF_MATERIAL_MAP = {
    'metal': 'metal',
    'tile': 'tile',  # Keep tile if present
    'concrete tile': 'tile',
    'clay tile': 'tile',
    'asphalt shingle': 'shingle',
    'composite shingle': 'shingle',
    'shingle': 'shingle',
    'flat': 'membrane',
    'membrane': 'membrane',
    'wood shake': 'shake',
    'shake': 'shake',
    'gravel': 'gravel',
    # Default to closest match or 'Unknown'
}
```

**Note:** Need to verify exact Arturo values and map accordingly

---

### 6. Roof Shape Mapping ✓
**DECISION:** Map to 3 categories: flat, gable, hip

**Mapping Table:**
```python
ROOF_SHAPE_MAP = {
    'flat': 'flat',
    'gable': 'gable',
    'hip': 'hip',
    'hipped': 'hip',
    'complex': 'hip',  # Default complex to hip?
    'shed': 'gable',   # Single slope -> gable?
    # Need to verify Arturo values
}
```

**Note:** Need to verify exact Arturo values and decide on complex roof handling

---

### 7. Roof Condition Score ✓
**DECISION:** Map Arturo condition (INVERTED scale!)

**Mapping Table:**
```python
ROOF_CONDITION_MAP = {
    'Excellent': 5.0,
    'Good': 4.0,
    'Fair': 3.0,
    'Poor': 2.0,
    'Very Poor': 1.0
}
```

**⚠️ IMPORTANT:** Scale is inverted!
- 5.0 = Best condition
- 1.0 = Worst condition

---

### 8. Ground Elevation ✓
**DECISION:** Leave NULL

```python
GROUNDELEV = None
```

---

### 9. Duplicate Fields (B.* vs normal) ✓
**DECISION:** Different sources!

```python
# B.* fields = Building capture metadata (pre-event/Arturo)
B.LAYERNAME = "bluesky-ultra-oceania"  # Fixed for all
B.CAPTURE_PROJECT = ???  # Need clarification
B.CHILD_AOI = ???  # Need clarification

# Non-B.* fields = Damage assessment metadata (from Graysky AOI)
LAYERNAME = graysky_aoi.layer  # "graysky" or "graysky-suncorp"
CAPTURE_PROJECT = graysky_aoi.collection  # e.g., "graydata-736"
CHILD_AOI = graysky_aoi.event_id  # e.g., "au-qld-alfred-cyclone-224-2025"
```

**⚠️ QUESTION:** What should B.CAPTURE_PROJECT and B.CHILD_AOI be?
- Same as non-B versions?
- Different values?

---

### 10. Solar Panel Detection ✓
**DECISION:** Spatial join with solar_panels layer + ADD NEW WATER HEATER FIELD

**Implementation:**
```python
# 1. Load solar_panels layer from Arturo GeoPackage
solar_panels = gpd.read_file(arturo_gpkg, layer='solar_panels', bbox=aoi_bounds)

# 2. Spatial intersection with structures
structures['ROOFSOLAR'] = structures.geometry.apply(
    lambda geom: 'SOLAR PANEL' if solar_panels.intersects(geom).any() else 'NO SOLAR PANEL'
)

# 3. Load pool_heaters layer (water heaters)
water_heaters = gpd.read_file(arturo_gpkg, layer='pool_heaters', bbox=aoi_bounds)

# 4. NEW FIELD: ROOFWATERHEATER
structures['ROOFWATERHEATER'] = structures.geometry.apply(
    lambda geom: 'WATER HEATER' if water_heaters.intersects(geom).any() else 'NO WATER HEATER'
)

# 5. Add geometry layers to output GeoPackage
output_layers = {
    'pre_event_structures': structures,
    'solar_panels': solar_panels_in_aoi,
    'water_heaters': water_heaters_in_aoi
}
```

**⚠️ NEW REQUIREMENT:** Add ROOFWATERHEATER field to schema!

---

### 11. Tree Overhang ✓
**DECISION:** Use `roof_tree_overlap_pct` rounded to whole numbers

```python
ROOFTREE = round(arturo.roof_tree_overlap_pct)  # 5.42 -> 5
```

---

### 12. Primary Structure Flag ✓
**DECISION:** Include ALL structures

```python
# Extract all structures (primary and secondary)
structures = arturo_structures  # No filtering

# Map is_primary flag
PRIMARYSTR = "TRUE" if arturo.is_primary else "FALSE"
```

---

### 13. WKT Format ✓
**DECISION:** Plain WKT without SRID prefix

```python
PARCELWKT = geometry.wkt  # "POLYGON ((x y, ...))"
ROOFTOPGEO = geometry.wkt  # No SRID prefix
```

---

### 14. Boolean String Format ✓
**CONFIRMED:** Uppercase `"TRUE"` / `"FALSE"`

```python
# All boolean strings
PRIMARYSTR = "TRUE" or "FALSE"
POOL = "TRUE" or "FALSE"
TRAMPOLINE = "TRUE" or "FALSE"
# etc.
```

---

### 15. Distance Scores ✓
**DECISION:** Leave **empty/NULL** (Arturo doesn't have this data)

**Meaning:**
- DST5, DST30, DST100, DST200 = Distance to nearest **TREE** in feet
- DSB5, DSB30, DSB100, DSB200 = Distance to nearest **BUILDING** in feet

```python
DST5 = DST30 = DST100 = DST200 = None
DSB5 = DSB30 = DSB100 = DSB200 = None
```

---

### 16. Property Features ✓
**DECISION:** All FALSE except Pool Heater (see #10)

```python
# All FALSE
POOLAREA = 0.0
TRAMPOLINE = "FALSE"
DECK = "FALSE"
POOL = "FALSE"
ENCLOSURE = "FALSE"
DIVINGBOAR = "FALSE"
WATERSLIDE = "FALSE"
PLAYGROUND = "FALSE"
SPORTCOURT = "FALSE"

# All scores = 0.0
TRAMPSCR = DECKSCR = POOLSCR = ENCLOSUSCR = 0.0
DIVINGSCR = WATSLIDSCR = PLAYGSCR = SPORTSCR = 0.0

# Exception: Pool heater detection (see #10)
# Handled via spatial join with pool_heaters layer
```

---

## ⚠️ REMAINING QUESTIONS

### Question A: B.CAPTURE_PROJECT and B.CHILD_AOI values?

**Options:**
1. Same as non-B versions (from Graysky AOI)
2. Leave empty/NULL
3. Use different values (what source?)

**Current understanding:**
- B.* fields = Pre-event building capture metadata
- Non-B.* fields = Post-event damage assessment metadata

**For pre-event data, what should B.CAPTURE_PROJECT and B.CHILD_AOI be?**

---

### Question B: Exact Arturo roof material/shape values?

Need to query actual values to create accurate mapping:

```python
# Check actual values in Arturo data
arturo.roof_material_majority.unique()
arturo.roof_shape_majority.unique()
```

**Action:** Query sample Arturo data to verify values

---

### Question C: Target schema ROOFWATERHEATER field?

**New requirement from #10:**
- Add ROOFWATERHEATER field to target schema
- Values: `"WATER HEATER"` or `"NO WATER HEATER"`

**Where does this fit in the 74-column schema?**
- Replace existing field?
- Add as 75th column?

---

## 📋 IMPLEMENTATION CHECKLIST

### Data Sources:
- [x] Arturo structures layer
- [x] Arturo solar_panels layer
- [x] Arturo pool_heaters layer (for water heaters)
- [x] Graysky AOI metadata

### Transformations:
- [x] ID mapping (structure_id → BUILDINGS_IDS, PEID)
- [x] Geometry to WKT (PARCELWKT, ROOFTOPGEO)
- [x] Roof material mapping (5 categories)
- [x] Roof shape mapping (3 categories)
- [x] Roof condition mapping (inverted scale)
- [x] Tree overhang rounding
- [x] Primary structure flag mapping
- [x] Solar panel spatial join
- [x] Water heater spatial join
- [x] All damage fields → 0/FALSE
- [x] All property features → FALSE
- [x] Camera technology → hardcoded
- [x] B.LAYERNAME → "bluesky-ultra-oceania"
- [x] LAYERNAME → from AOI
- [x] Empty fields → NULL

### Output Layers:
- [x] pre_event_structures (main layer)
- [x] solar_panels (separate geometry layer)
- [x] water_heaters (separate geometry layer)

---

## 🎯 READY FOR IMPLEMENTATION

**Status:** 95% clear, 3 minor clarifications needed

**Next steps:**
1. Clarify B.CAPTURE_PROJECT and B.CHILD_AOI values
2. Query Arturo for exact roof material/shape values
3. Confirm ROOFWATERHEATER field location in schema
4. Implement extraction script

---

**Created:** 2025-10-27
**Status:** ✅ Decisions documented, ready for implementation
