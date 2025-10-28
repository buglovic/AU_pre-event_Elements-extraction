# Mapping Questions & Uncertainties

## ⚠️ CRITICAL QUESTIONS - Need User Input

### 1. Building Identifiers

**Question:** What should be used for `BUILDINGS_IDS` and `PEID`?

**Options:**
- A) `arturo.structure_id` (unique Arturo structure identifier)
- B) `arturo.parcel_id` (property-level identifier)
- C) Generate new UUID for each structure
- D) Concatenate: `{collection}_{structure_id}`

**Current Assumption:** Use `structure_id` for both (they seem to be duplicates)

**Example from target:**
- BUILDINGS_IDS: `s-vrelease-55366d12-fff4-11ef-a841-8a9839e66595`
- PEID: `s-vrelease-55366d12-fff4-11ef-a841-8a9839e66595` (identical!)

**Arturo has:**
- `structure_id`: Unique per structure
- `parcel_id`: Groups structures on same property

**→ USER DECISION NEEDED**: Which ID scheme to use?

---

### 2. Image Metadata

**Question:** What values for `B.IMAGEID` and `IMAGEID`?

**Available from:**
- AOI: `collection` (e.g., `"graydata-736"`)
- Arturo: `vexcel_collection_name` (e.g., specific imagery collection)
- Arturo: `image_date`

**Options:**
- A) Use AOI `collection` directly
- B) Use Arturo `vexcel_collection_name`
- C) Concatenate: `{collection}_{image_date}`
- D) Generate sequential: `{collection}_001`, `{collection}_002`, etc.

**Current Assumption:** Use `vexcel_collection_name` from Arturo

**→ USER DECISION NEEDED**: What format for IMAGEID?

---

### 3. Camera Technology

**Question:** What value for `B.CAMERATECHNOLOGY` and `CAMERATECHNOLOGY`?

**Example from target:** `"UltraCam Osprey"`, `"Unknown"`

**Available from:**
- Arturo: `vexcel_product_type` (e.g., `"ortho"`, `"oblique"`)
- Arturo: `image_provider` (e.g., `"Vexcel"`)
- AOI: Not directly available

**Options:**
- A) Hardcode `"UltraCam Osprey"` for all
- B) Use `image_provider` from Arturo
- C) Map `vexcel_product_type` to camera names
- D) Leave as `"Unknown"`

**Current Assumption:** Use `"Unknown"` as default

**→ USER DECISION NEEDED**: How to determine camera technology?

---

### 4. Image Date Format

**Question:** What date format for `B.IMGDATE` and `IMGDATE`?

**Example from target:** Various formats seen (need to check)

**Available from Arturo:**
- `image_date`: String format (need to verify format)
- `vexcel_first_capture_date`: DateTime
- `vexcel_last_capture_date`: DateTime
- `vexcel_capture_date_str`: String

**Options:**
- A) ISO format: `"2025-02-15"`
- B) US format: `"02/15/2025"`
- C) Other format: `"15-Feb-2025"`

**→ USER DECISION NEEDED**: Required date format?

---

### 5. Roof Material Mapping

**Question:** How to map Arturo roof materials to target schema?

**Target schema uses:**
- `"metal"`, `"tile"`, `"shingle"`, `"membrane"`, `"shake"`, `"Unknown"`

**Arturo has:**
- `roof_material_majority`: String (need to verify values)

**Potential mapping needed:**
- Arturo `"metal"` → Target `"metal"` ✓
- Arturo `"concrete tile"` → Target `"tile"` ?
- Arturo `"clay tile"` → Target `"tile"` ?
- Arturo `"asphalt shingle"` → Target `"shingle"` ?
- Arturo `"composite shingle"` → Target `"shingle"` ?
- Arturo `"flat"` → Target `"membrane"` ?
- Arturo `"wood shake"` → Target `"shake"` ?

**→ USER DECISION NEEDED**: Provide exact mapping table for roof materials

---

### 6. Roof Shape Mapping

**Question:** How to map Arturo roof shapes to target schema?

**Arturo has:**
- `roof_shape_majority`: String (values unknown)

**Target uses:** (need to verify from target data)
- Examples: `"gable"`, `"hip"`, `"flat"`, `"complex"`, etc.?

**→ USER DECISION NEEDED**: Provide exact mapping table for roof shapes

---

### 7. Roof Condition Score

**Question:** How to derive `ROOFCONDIT` value?

**Target range:** 1.0 (excellent) to 5.0 (poor)

**Arturo has:**
- `roof_condition_general`: String (e.g., `"Good"`, `"Fair"`, `"Poor"`)

**Potential mapping:**
- `"Excellent"` → 1.0
- `"Good"` → 2.0
- `"Fair"` → 3.0
- `"Poor"` → 4.0
- `"Very Poor"` → 5.0

**Pre-Event assumption:** Always 1.0 (excellent condition before event)?

**→ USER DECISION NEEDED**: Should we use Arturo condition or always 1.0?

---

### 8. Ground Elevation

**Question:** Should we populate `GROUNDELEV` or leave NULL?

**Arturo has:**
- No ground elevation field directly visible

**Target allows NULL** (95.4% NULL in example)

**→ USER DECISION NEEDED**: Leave as NULL or try to derive?

---

### 9. Duplicate Fields - Different Values?

**Question:** Should `B.LAYERNAME` and `LAYERNAME` have DIFFERENT values?

**Analysis shows:**
- `B.LAYERNAME == LAYERNAME: False` (they are NOT equal!)

**Example from target:**
- `B.LAYERNAME`: `"bluesky-ultra-oceania"` (building layer)
- `LAYERNAME`: Different value? (damage assessment layer?)

**Options:**
- A) B.LAYERNAME = Pre-event layer (from Arturo/Vexcel)
- B) LAYERNAME = Post-event/damage layer (from AOI)
- C) Both use same value from AOI

**Current data shows:**
- B.LAYERNAME: `"bluesky-ultra-oceania"` (building capture)
- LAYERNAME: Something else? (damage assessment capture)

**→ USER DECISION NEEDED**: What distinguishes B.* fields from non-B.* fields?

---

### 10. Solar Panel Detection

**Question:** Can we detect solar panels from Arturo data?

**Target uses:**
- `"SOLAR PANEL"` or `"NO SOLAR PANEL"`

**Arturo may have:**
- Separate solar_panels layer in GeoPackage?
- Need to spatial join structures with solar panels layer

**Options:**
- A) Always use `"NO SOLAR PANEL"` (conservative)
- B) Spatial join with solar_panels layer to detect presence
- C) Check if structure intersects any solar panel geometry

**→ USER DECISION NEEDED**: Should we detect solar panels or default to "NO SOLAR PANEL"?

---

### 11. Tree Overhang

**Question:** How to populate `ROOFTREE` field?

**Target type:** Real (0.0 to ?)

**Arturo has:**
- `has_roof_tree_overlap`: Real (boolean-like?)
- `roof_tree_overlap_pct`: Real (percentage)

**Options:**
- A) Use `roof_tree_overlap_pct` directly
- B) Convert boolean to 0.0/1.0
- C) Always use 0.0 (no tree overhang)

**→ USER DECISION NEEDED**: How to map tree overhang data?

---

### 12. Primary Structure Flag

**Question:** Should `PRIMARYSTR` always be `"TRUE"`?

**Arturo has:**
- `is_primary`: Boolean (distinguishes main building from outbuildings)

**Options:**
- A) Always `"TRUE"` (only extract primary structures)
- B) Map `is_primary` → `"TRUE"/"FALSE"`
- C) Extract all structures, set based on Arturo flag

**→ USER DECISION NEEDED**: Filter to primary only or include all?

---

## 🔍 MEDIUM PRIORITY QUESTIONS

### 13. WKT Format

**Question:** Should WKT include SRID prefix?

**Options:**
- A) `POLYGON ((x y, ...))`
- B) `SRID=4326;POLYGON ((x y, ...))`

**Target examples show:** Plain WKT without SRID prefix

**→ ASSUMED**: Use plain WKT without SRID

---

### 14. Boolean String Format

**Question:** Confirmed uppercase `"TRUE"` / `"FALSE"`?

**Target shows:** Uppercase strings

**→ CONFIRMED**: Use `"TRUE"` and `"FALSE"` (uppercase)

---

### 15. Distance Scores Context

**Question:** What do DST/DSB scores represent?

**Fields:**
- DST5, DSB5 (top/bottom 5m?)
- DST30, DSB30 (top/bottom 30m?)
- DST100, DSB100
- DST200, DSB200

**Pre-event:** All set to 0.0

**→ ASSUMED**: Distance-based damage metrics, not relevant for pre-event

---

### 16. Property Features

**Question:** Can any property features be detected from Arturo?

**Arturo may have separate layers:**
- pool_heaters
- ac_units
- Other amenities?

**Target fields:**
- POOL, DECK, TRAMPOLINE, PLAYGROUND, SPORTCOURT, etc.

**Options:**
- A) Always set to `"FALSE"` (no detection)
- B) Try to detect from other Arturo layers

**→ USER DECISION NEEDED**: Attempt feature detection or all FALSE?

---

## 📋 SUMMARY OF DECISIONS NEEDED

### High Priority (Blocking Implementation):

1. **BUILDINGS_IDS / PEID**: Which ID scheme?
2. **B.IMAGEID / IMAGEID**: What format?
3. **B.CAMERATECHNOLOGY**: How to determine?
4. **Date format**: Required format string?
5. **Roof material mapping**: Exact translation table
6. **Roof shape mapping**: Exact translation table
7. **B.* vs non-B.* fields**: Why duplicated, what's the difference?
8. **ROOFCONDIT**: Use Arturo condition or always 1.0?

### Medium Priority (Can Use Defaults):

9. **GROUNDELEV**: Populate or NULL?
10. **Solar panel detection**: Attempt or default?
11. **ROOFTREE**: Map tree overhang or 0.0?
12. **PRIMARYSTR**: Filter primary only or all structures?
13. **Property features**: Detect or all FALSE?

---

## 🎯 RECOMMENDED APPROACH

**Option A - Conservative (Safest):**
- Use only directly mappable fields
- Set unknowns to defaults/NULL
- Minimal data transformation
- Fast implementation

**Option B - Comprehensive (Best Quality):**
- Attempt all possible mappings
- Detect features from multiple Arturo layers
- Complex transformations
- Slower but more complete data

**→ USER DECISION NEEDED**: Which approach?

---

**Created:** 2025-10-27
**Status:** Awaiting user input on critical decisions
