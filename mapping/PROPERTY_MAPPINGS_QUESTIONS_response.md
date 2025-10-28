# Property Data Integration - Mapping Questions

## Overview

We need to integrate Arturo Property data (`arturo_{STATE}_property_details.gpkg`) with Structure data to correctly map property features and the **true PARCELWKT** (property boundary, not building footprint).

---

## Data Sources

### 1. Arturo Property Details
- **File**: `/Users/romanbuegler/dev/hail_damage/data/final/arturo_{STATE}_property_details.gpkg`
- **Layer**: `parcels` (63 columns)
- **Geometry**: Property boundary polygon (Polygon or MultiPolygon)
- **Key Field**: `parcel_id`

### 2. Arturo Structure Details (existing)
- **File**: `/Users/romanbuegler/dev/hail_damage/data/final/arturo_structuredetails_{STATE}_full.gpkg`
- **Layer**: `structures` (35 columns)
- **Geometry**: Building footprint polygon
- **Key Field**: `parcel_id`

### Join Strategy
```python
# Join on parcel_id
merged = structures.merge(properties, on='parcel_id', how='left', suffixes=('_structure', '_property'))
```

---

## ✅ CLEAR MAPPINGS (No Questions)

### Geometry Fields

| Target Field | Source | Transformation | Notes |
|--------------|--------|----------------|-------|
| **PARCELWKT** | `property.geometry.wkt` | Direct WKT conversion | ✓ TRUE property boundary (not building!) |
| **ROOFTOPGEO** | `structure.geometry.wkt` | Direct WKT conversion | ✓ Building footprint (unchanged) |
| **geometry** (output) | `structure.geometry` | Direct copy | ✓ Building as main geometry (unchanged) |

### Pool Features

| Target Field | Source | Transformation |
|--------------|--------|----------------|
| **POOL** | `property.has_pool` | `"TRUE"` if True else `"FALSE"` |
| **POOLAREA** | `property.pools_total_area` | Direct copy (float) |

### Trampoline Features

| Target Field | Source | Transformation |
|--------------|--------|----------------|
| **TRAMPOLINE** | `property.has_trampoline` | `"TRUE"` if True else `"FALSE"` |

### Wooden Deck Features

| Target Field | Source | Transformation |
|--------------|--------|----------------|
| **DECK** | `property.has_wooden_deck` | `"TRUE"` if True else `"FALSE"` |

### Enclosure Features

| Target Field | Source | Transformation |
|--------------|--------|----------------|
| **ENCLOSURE** | `property.has_enclosure` | `"TRUE"` if True else `"FALSE"` |

---

## ❓ QUESTIONS - Need Your Input

### Question 1: Score Fields - What do they represent?

The target schema has "score" fields for each property feature. What should these scores be?

**Target Fields:**
- `POOLSCR` (currently: 0.0)
- `TRAMPSCR` (currently: 0.0)
- `DECKSCR` (currently: 0.0)
- `ENCLOSUSCR` (currently: 0.0)
- `DIVINGSCR` (currently: 0.0)
- `WATSLIDSCR` (currently: 0.0)
- `PLAYGSCR` (currently: 0.0)
- `SPORTSCR` (currently: 0.0)

**Arturo provides:**
- `trampoline_ct` (count: int)
- `wooden_deck_area` (area: float)
- `enclosure_area` (area: float)
- `tennis_court_ct`, `basketball_court_ct` (counts: int)
- `pools_total_area` (area: float)

**Options:**
1. **Detection confidence** (0.0 = none, 1.0 = detected)
   - Example: `POOLSCR = 1.0 if has_pool else 0.0`
2. **Normalized area** (0.0-1.0 based on area)
3. **Count** (direct count of features)
4. **Leave as 0.0** (no score available)

**My Question:** What should these score fields represent?

"""SCR steht für model score. den haben wir schlicht von Arturo nicht, also setze alle auf NULL

---

### Question 2: Sport Courts - How to combine?

**Target Fields:**
- `SPORTCOURT` (TRUE/FALSE)
- `SPORTSCR` (score)

**Arturo provides:**
- `has_tennis_court` (bool)
- `has_basketball_court` (bool)
- `tennis_court_ct` (int)
- `basketball_court_ct` (int)
- `has_sport_pitch` (NULL in data)
- `sport_pitch_ct` (NULL in data)

**Options:**
1. **ANY court** → TRUE
   ```python
   SPORTCOURT = "TRUE" if (has_tennis_court OR has_basketball_court) else "FALSE"
   SPORTSCR = tennis_court_ct + basketball_court_ct
   ```
2. **Separate by type** (but target schema only has one field)
3. **Include sport_pitch** (but seems to be NULL)

**My Question:** How should we map sport courts?
"""fallse alle sports courts typen von Arturo in eine Klasse SPORTCOURT, SCR bleibt wieder leer (Siehe oben)

---

### Question 3: Missing Features - How to handle?

**These features exist in target schema but NOT in Arturo:**
- `DIVINGBOAR`, `DIVINGSCR` (diving board)
- `WATERSLIDE`, `WATSLIDSCR` (water slide)
- `PLAYGROUND`, `PLAYGSCR` (playground)

**Options:**
1. **Leave as FALSE/0.0** (assume not present)
2. **Set to NULL** (unknown/not detected)

**My Question:** Should these be FALSE or NULL?
""" NULL

---

### Question 4: Playground - Can we infer from sport_pitch?

**Arturo has:**
- `has_sport_pitch` (NULL in sample data)
- `sport_pitch_ct` (NULL in sample data)

**Could this be used for PLAYGROUND?**
- Sport pitch might include playground areas
- Or should PLAYGROUND remain FALSE/NULL?

**My Question:** Is sport_pitch related to playground, or completely separate?
"""do not infer, ignore this attribute

---

### Question 5: Pool Heater - Existing logic or Property data?

**Current implementation:**
- Uses spatial join with `pool_heaters` layer
- Result: `ROOFWATERHEATER` field

**Arturo Property has:**
- No direct `has_pool_heater` field
- But we have separate `pool_heaters` layer in property GeoPackage

**Options:**
1. **Keep existing logic** (spatial join with pool_heaters layer)
2. **Check if pool_heaters layer has better data** in property GeoPackage
3. **Both** (use property layer if available, else structure layer)

**My Question:** Should we keep the existing pool_heater logic or update it?
"""this one is strange, there should be no pool heaters present outside the structure so should only be present in the arturo_structuredetails_STATE_full.gpkg datasets on a strcture level. Let's treat this seperate, I think this is a false attribute in the property layer. 

---

### Question 6: Null Handling - Property not found

**What if structure.parcel_id doesn't match any property?**

This can happen if:
- Property data is missing
- parcel_id mismatch
- Data extraction issues

**Options:**
1. **Skip structure** (don't include in output)
2. **Use structure geometry as PARCELWKT** (fallback to current behavior)
3. **Set PARCELWKT to NULL** (but field is mandatory!)
4. **Use structure geometry + log warning**

**My Question:** What should we do if property data is missing for a structure?
""" 1 skip structure

---

### Question 7: Accuracy Metrics - Should we use them?

**Arturo Property has:**
```python
accuracy_metrics = {
    "property": {
        "hasPool": {"recall": 1, "accuracy": 0.99, "precision": 0.98},
        "hasTrampoline": {...},
        # ... etc
    }
}
```

**Could these be used for score fields?**
- Example: `POOLSCR = accuracy_metrics['property']['hasPool']['accuracy']`

**My Question:** Should we use accuracy metrics for score fields? Or is this overcomplicating?
""" fully skip them

---

### Question 8: Additional Property Layers - Should we integrate?

**Arturo Property GeoPackage has these additional layers:**
- `pools` (individual pool geometries)
- `trampolines` (individual trampoline geometries)
- `sports_pitches` (individual pitch geometries)
- `solar_panels_ground` (ground-mounted solar panels)
- `wooden_decks` (individual deck geometries)
- `driveways`
- `vehicles`

**Current output has 3 layers:**
- `pre_event_structures`
- `solar_panels` (roof-mounted, from structure data)
- `water_heaters`

**Should we add more layers to output?**
1. **pools** layer
2. **trampolines** layer
3. **wooden_decks** layer
4. **solar_panels_ground** layer

**My Question:** Should we include these additional geometry layers in the output GeoPackage?
""" we DO NOT include these geometry layers

---

### Question 9: Ground Slope - Should we add to output?

**Arturo Property has:**
- `ground_slope` (float)
- `ground_slope_direction` (degrees)
- `parcel_steep_slope` (bool)
- `ground_slope_min_elevation` (float, mostly NULL)
- `ground_slope_max_elevation` (float, mostly NULL)
- `ground_slope_median_elevation` (float, mostly NULL)

**Target schema has:**
- `GROUNDELEV` (currently NULL)

**Options:**
1. **Map ground_slope_median_elevation → GROUNDELEV**
2. **Leave as NULL** (mostly NULL in Arturo anyway)
3. **Add new fields** for slope data (but not in target schema)

**My Question:** Should we use ground elevation data if available?
""" we do not add this attribte

---

## Summary of Questions

1. **Score fields**: Detection confidence (0/1), area, count, or 0.0?
2. **Sport courts**: Combine tennis+basketball as TRUE/FALSE?
3. **Missing features** (diving board, water slide, playground): FALSE or NULL?
4. **Playground**: Related to sport_pitch or separate?
5. **Pool heater**: Keep existing logic or update?
6. **Missing property**: Fallback to structure geometry or skip?
7. **Accuracy metrics**: Use for scores or ignore?
8. **Additional layers**: Include pools, trampolines, decks geometries?
9. **Ground elevation**: Use if available or leave NULL?

---

## Proposed Mapping (Pending Answers)

```python
# After joining structures with properties on parcel_id:

record = {
    # Geometry (UPDATED)
    'PARCELWKT': property_geom.wkt if property_geom else structure_geom.wkt,  # Q6
    'ROOFTOPGEO': structure_geom.wkt,

    # Pool (UPDATED)
    'POOL': 'TRUE' if property.has_pool else 'FALSE',
    'POOLAREA': property.pools_total_area or 0.0,
    'POOLSCR': ???,  # Q1, Q7

    # Trampoline (UPDATED)
    'TRAMPOLINE': 'TRUE' if property.has_trampoline else 'FALSE',
    'TRAMPSCR': ???,  # Q1

    # Deck (UPDATED)
    'DECK': 'TRUE' if property.has_wooden_deck else 'FALSE',
    'DECKSCR': ???,  # Q1

    # Enclosure (UPDATED)
    'ENCLOSURE': 'TRUE' if property.has_enclosure else 'FALSE',
    'ENCLOSUSCR': ???,  # Q1

    # Sport Court (UPDATED)
    'SPORTCOURT': ???,  # Q2
    'SPORTSCR': ???,  # Q2

    # Missing features
    'DIVINGBOAR': ???,  # Q3
    'DIVINGSCR': ???,  # Q3
    'WATERSLIDE': ???,  # Q3
    'WATSLIDSCR': ???,  # Q3
    'PLAYGROUND': ???,  # Q3, Q4
    'PLAYGSCR': ???,  # Q3, Q4

    # Ground elevation
    'GROUNDELEV': ???,  # Q9

    # ... (rest unchanged)
}
```

---

**Status**: Awaiting user input on 9 questions before implementing property data integration.

**Created**: 2025-10-27
