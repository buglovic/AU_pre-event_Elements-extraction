# Arturo Data Directory

This directory should contain the Arturo building and property data files downloaded from AWS S3.

The internal path is s3://vexcel-platform-properties/arturo_delivery/

property data: s3://vexcel-platform-properties/arturo_delivery/property_geometries_perstate/
structure data: s3://vexcel-platform-properties/arturo_delivery/structure_and_roof_geometries_perstate/

## Required Files

Download the following GeoPackage files from AWS S3 and place them in this directory:

### Structure Data
- `arturo_structuredetails_NSW_full.gpkg`
- `arturo_structuredetails_VIC_full.gpkg`
- `arturo_structuredetails_QLD_full.gpkg`
- `arturo_structuredetails_WA_full.gpkg`
- `arturo_structuredetails_SA_full.gpkg`
- `arturo_structuredetails_TAS_full.gpkg`
- `arturo_structuredetails_NT_full.gpkg`
- `arturo_structuredetails_ACT_full.gpkg`

### Property Data
- `arturo_propertydetails_NSW_full.gpkg`
- `arturo_propertydetails_VIC_full.gpkg`
- `arturo_propertydetails_QLD_full.gpkg`
- `arturo_propertydetails_WA_full.gpkg`
- `arturo_propertydetails_SA_full.gpkg`
- `arturo_propertydetails_TAS_full.gpkg`
- `arturo_propertydetails_NT_full.gpkg`
- `arturo_propertydetails_ACT_full.gpkg`

### Solar Panels (Optional)
- `arturo_solarpanels_NSW_full.gpkg`
- `arturo_solarpanels_VIC_full.gpkg`
- `arturo_solarpanels_QLD_full.gpkg`
- `arturo_solarpanels_WA_full.gpkg`
- `arturo_solarpanels_SA_full.gpkg`
- `arturo_solarpanels_TAS_full.gpkg`
- `arturo_solarpanels_NT_full.gpkg`
- `arturo_solarpanels_ACT_full.gpkg`

### Water Heaters (Optional)
- `arturo_waterheaters_NSW_full.gpkg`
- `arturo_waterheaters_VIC_full.gpkg`
- `arturo_waterheaters_QLD_full.gpkg`
- `arturo_waterheaters_WA_full.gpkg`
- `arturo_waterheaters_SA_full.gpkg`
- `arturo_waterheaters_TAS_full.gpkg`
- `arturo_waterheaters_NT_full.gpkg`
- `arturo_waterheaters_ACT_full.gpkg`

## Data Source

Contact your team administrator for:
- AWS S3 bucket location
- Access credentials
- Download instructions

## File Sizes

Typical file sizes (approximate):
- Structure files: 500 MB - 2 GB per state
- Property files: 300 MB - 1.5 GB per state
- Solar/Water heater files: 50 MB - 200 MB per state

**Total required disk space: ~15-20 GB for all states**

## Note

These files are **NOT included in the GitHub repository** due to their size. They must be downloaded separately from AWS S3.

The `.gitignore` file in this directory ensures these large data files are not accidentally committed to version control.
