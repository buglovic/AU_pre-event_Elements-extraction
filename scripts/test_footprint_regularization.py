#!/usr/bin/env python3
"""
Test script for building footprint regularization using Building-Regulariser library.

This script loads an existing pre-event GeoPackage, applies orthogonal edge alignment
to building footprints, and generates comparison statistics and visualizations.

Usage:
    python test_footprint_regularization.py

Output:
    - {collection}_DA_pre-event_regularized.gpkg (regularized footprints)
    - regularization_report_{collection}.html (comparison report)
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely import wkt
import time
import json

# Import Building-Regulariser
try:
    from buildingregulariser import regularize_geodataframe
except ImportError:
    print("ERROR: buildingregulariser library not installed.")
    print("Install with: pip install git+https://github.com/DPIRD-DMA/Building-Regulariser.git")
    sys.exit(1)

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_available_files() -> list:
    """List all available pre-event GeoPackage files."""
    if not OUTPUT_DIR.exists():
        logger.error(f"Output directory not found: {OUTPUT_DIR}")
        return []

    files = sorted(OUTPUT_DIR.glob("*_DA_pre-event.gpkg"))
    return files


def count_orthogonal_edges(geom: Polygon, tolerance_degrees: float = 2.0) -> tuple:
    """
    Count orthogonal edges (0°, 45°, 90°, 135°) in a polygon.

    Args:
        geom: Shapely Polygon
        tolerance_degrees: Tolerance for angle matching

    Returns:
        (total_edges, orthogonal_edges, orthogonal_percentage)
    """
    if not isinstance(geom, Polygon):
        return (0, 0, 0.0)

    coords = list(geom.exterior.coords)
    if len(coords) < 3:
        return (0, 0, 0.0)

    total_edges = len(coords) - 1
    orthogonal_count = 0

    for i in range(total_edges):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            continue

        # Calculate angle in degrees
        angle = np.degrees(np.arctan2(dy, dx))
        angle = angle % 180  # Normalize to 0-180

        # Check if angle is close to 0°, 45°, 90°, or 135°
        target_angles = [0, 45, 90, 135]
        for target in target_angles:
            if abs(angle - target) <= tolerance_degrees:
                orthogonal_count += 1
                break

    orthogonal_pct = (orthogonal_count / total_edges * 100) if total_edges > 0 else 0.0
    return (total_edges, orthogonal_count, orthogonal_pct)


def regularize_buildings(gdf: gpd.GeoDataFrame, parallel_threshold: float = 1.0,
                         simplify_tolerance: float = 0.5) -> gpd.GeoDataFrame:
    """
    Regularize building footprints using Building-Regulariser.

    Args:
        gdf: Input GeoDataFrame with building geometries
        parallel_threshold: Distance threshold for merging parallel edges (meters)
        simplify_tolerance: Tolerance for polygon simplification (meters)

    Returns:
        GeoDataFrame with regularized geometries
    """
    logger.info("  Applying building regularization...")

    # Apply regularization with orthogonal edge alignment
    regularized_gdf = regularize_geodataframe(
        gdf,
        parallel_threshold=parallel_threshold,
        simplify=True,
        simplify_tolerance=simplify_tolerance,
        allow_45_degree=True,
        diagonal_threshold_reduction=15,
        allow_circles=False,  # Disable circle detection for now
        num_cores=0,  # Use all available cores
        include_metadata=True,  # Include metadata about regularization
        neighbor_alignment=False  # Don't align with neighbors
    )

    return regularized_gdf


def calculate_geometry_stats(original: gpd.GeoDataFrame, regularized: gpd.GeoDataFrame) -> dict:
    """
    Calculate comparison statistics between original and regularized geometries.

    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_buildings': len(original),
        'buildings_regularized': len(regularized),
        'buildings_dropped': len(original) - len(regularized),
        'vertex_reduction': {
            'mean': 0.0,
            'median': 0.0,
            'total_original': 0,
            'total_regularized': 0
        },
        'area_preservation': {
            'mean_change_pct': 0.0,
            'median_change_pct': 0.0,
            'max_change_pct': 0.0
        },
        'orthogonality': {
            'original_mean_pct': 0.0,
            'regularized_mean_pct': 0.0,
            'improvement': 0.0
        }
    }

    # Calculate vertex counts (for matching records only)
    original_vertices = original.iloc[:len(regularized)].geometry.apply(lambda g: len(g.exterior.coords) if isinstance(g, Polygon) else 0)
    regularized_vertices = regularized.geometry.apply(lambda g: len(g.exterior.coords) if isinstance(g, Polygon) else 0)

    stats['vertex_reduction']['total_original'] = int(original_vertices.sum())
    stats['vertex_reduction']['total_regularized'] = int(regularized_vertices.sum())

    vertex_diff = original_vertices.iloc[:len(regularized)] - regularized_vertices
    stats['vertex_reduction']['mean'] = float(vertex_diff.mean())
    stats['vertex_reduction']['median'] = float(vertex_diff.median())

    # Calculate area changes (for matching records only)
    original_areas = original.geometry.iloc[:len(regularized)].area
    regularized_areas = regularized.geometry.area
    area_change_pct = ((regularized_areas.values - original_areas.values) / original_areas.values * 100)
    area_change_pct = np.abs(area_change_pct)

    stats['area_preservation']['mean_change_pct'] = float(np.mean(area_change_pct))
    stats['area_preservation']['median_change_pct'] = float(np.median(area_change_pct))
    stats['area_preservation']['max_change_pct'] = float(np.max(area_change_pct))

    # Calculate orthogonality
    logger.info("  Calculating orthogonality metrics...")
    original_ortho = original.geometry.iloc[:len(regularized)].apply(lambda g: count_orthogonal_edges(g)[2])
    regularized_ortho = regularized.geometry.apply(lambda g: count_orthogonal_edges(g)[2])

    stats['orthogonality']['original_mean_pct'] = float(original_ortho.mean())
    stats['orthogonality']['regularized_mean_pct'] = float(regularized_ortho.mean())
    stats['orthogonality']['improvement'] = float(regularized_ortho.mean() - original_ortho.mean())

    return stats


def generate_html_report(stats: dict, collection: str, processing_time: float, output_path: Path):
    """Generate HTML comparison report."""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Building Footprint Regularization Report - {collection}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2 {{
            color: #333;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: bold;
            color: #555;
        }}
        .metric-value {{
            color: #007bff;
        }}
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>Building Footprint Regularization Report</h1>
    <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Collection:</strong> {collection}</p>
    <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>

    <div class="section">
        <h2>Overview</h2>
        <div class="metric">
            <span class="metric-label">Total Buildings:</span>
            <span class="metric-value">{stats['total_buildings']:,}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Buildings Regularized:</span>
            <span class="metric-value positive">{stats['buildings_regularized']:,}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Buildings Dropped:</span>
            <span class="metric-value {'negative' if stats['buildings_dropped'] > 0 else ''}">{stats['buildings_dropped']:,}</span>
        </div>
    </div>

    <div class="section">
        <h2>Vertex Reduction</h2>
        <div class="metric">
            <span class="metric-label">Original Total Vertices:</span>
            <span class="metric-value">{stats['vertex_reduction']['total_original']:,}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Regularized Total Vertices:</span>
            <span class="metric-value">{stats['vertex_reduction']['total_regularized']:,}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Mean Reduction per Building:</span>
            <span class="metric-value positive">{stats['vertex_reduction']['mean']:.2f} vertices</span>
        </div>
        <div class="metric">
            <span class="metric-label">Median Reduction per Building:</span>
            <span class="metric-value positive">{stats['vertex_reduction']['median']:.2f} vertices</span>
        </div>
    </div>

    <div class="section">
        <h2>Area Preservation</h2>
        <div class="metric">
            <span class="metric-label">Mean Area Change:</span>
            <span class="metric-value">{stats['area_preservation']['mean_change_pct']:.3f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Median Area Change:</span>
            <span class="metric-value">{stats['area_preservation']['median_change_pct']:.3f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Maximum Area Change:</span>
            <span class="metric-value">{stats['area_preservation']['max_change_pct']:.3f}%</span>
        </div>
    </div>

    <div class="section">
        <h2>Orthogonality (Edge Alignment)</h2>
        <div class="metric">
            <span class="metric-label">Original Mean Orthogonal Edges:</span>
            <span class="metric-value">{stats['orthogonality']['original_mean_pct']:.2f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Regularized Mean Orthogonal Edges:</span>
            <span class="metric-value">{stats['orthogonality']['regularized_mean_pct']:.2f}%</span>
        </div>
        <div class="metric">
            <span class="metric-label">Improvement:</span>
            <span class="metric-value positive">+{stats['orthogonality']['improvement']:.2f}%</span>
        </div>
    </div>

    <div class="section">
        <h2>Interpretation</h2>
        <p><strong>Vertex Reduction:</strong> Regularization simplified building footprints by reducing the number of vertices,
        making geometries cleaner and more efficient to process.</p>

        <p><strong>Area Preservation:</strong> Low area change percentages indicate that regularization maintains the original
        building footprint size while improving geometry quality.</p>

        <p><strong>Orthogonality:</strong> Higher percentage of orthogonal edges means more buildings have edges aligned to
        cardinal directions (0°, 45°, 90°, 135°), which is more realistic for most building types.</p>
    </div>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    logger.info(f"  Report saved to: {output_path}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("Building Footprint Regularization Test")
    print("=" * 80)

    # List available files
    available_files = list_available_files()
    if not available_files:
        logger.error("No pre-event GeoPackage files found in output directory.")
        return

    print(f"\nFound {len(available_files)} pre-event GeoPackage files:\n")
    for idx, file_path in enumerate(available_files, 1):
        collection = file_path.stem.replace("_DA_pre-event", "")
        print(f"{idx:2d}. {collection}")

    # Get user selection
    while True:
        try:
            selection = input(f"\nSelect file to test (1-{len(available_files)}): ").strip()
            file_idx = int(selection) - 1
            if 0 <= file_idx < len(available_files):
                break
            print(f"Please enter a number between 1 and {len(available_files)}")
        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return

    selected_file = available_files[file_idx]
    collection = selected_file.stem.replace("_DA_pre-event", "")

    print(f"\n{'=' * 80}")
    print(f"Processing: {collection}")
    print(f"{'=' * 80}\n")

    # Load structures
    logger.info("Loading building structures...")
    try:
        structures = gpd.read_file(selected_file, layer='pre_event_structures')
        logger.info(f"  Loaded {len(structures):,} structures")
        logger.info(f"  CRS: {structures.crs}")

        # If in geographic CRS, convert to projected CRS for better regularization
        if structures.crs and structures.crs.is_geographic:
            # Use appropriate UTM zone based on centroid
            centroid = structures.geometry.union_all().centroid
            utm_zone = int((centroid.x + 180) / 6) + 1
            hemisphere = 'north' if centroid.y >= 0 else 'south'
            target_crs = f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84"
            logger.info(f"  Converting from geographic to projected CRS: UTM Zone {utm_zone}{' N' if hemisphere == 'north' else ' S'}")
            structures_original_crs = structures.crs
            structures = structures.to_crs(target_crs)
        else:
            structures_original_crs = None

    except Exception as e:
        logger.error(f"Failed to load structures: {e}")
        return

    # Apply regularization
    logger.info("Applying regularization to footprints...")
    logger.info("  This may take several minutes for large datasets...")
    logger.info("  Using parallel processing with all available cores...")

    start_time = time.time()
    regularized_gdf = regularize_buildings(
        structures,
        parallel_threshold=1.0,
        simplify_tolerance=0.5
    )
    processing_time = time.time() - start_time
    logger.info(f"  Regularization complete in {processing_time:.2f} seconds")

    # Calculate statistics
    logger.info("Calculating comparison statistics...")
    stats = calculate_geometry_stats(structures, regularized_gdf)

    # Convert back to original CRS if we converted earlier
    if structures_original_crs:
        logger.info(f"  Converting back to original CRS: {structures_original_crs}")
        regularized_gdf = regularized_gdf.to_crs(structures_original_crs)

    # Save regularized output
    output_gpkg = OUTPUT_DIR / f"{collection}_DA_pre-event_regularized.gpkg"
    logger.info(f"Saving regularized geometries to: {output_gpkg}")

    try:
        regularized_gdf.to_file(output_gpkg, driver='GPKG', layer='pre_event_structures_regularized')
        logger.info("  ✓ Regularized structures saved")

        # Copy solar panels and water heaters layers if they exist
        for layer_name in ['solar_panels', 'water_heaters']:
            try:
                layer_gdf = gpd.read_file(selected_file, layer=layer_name)
                layer_gdf.to_file(output_gpkg, driver='GPKG', layer=layer_name)
                logger.info(f"  ✓ {layer_name} layer copied")
            except Exception:
                pass  # Layer doesn't exist, skip

    except Exception as e:
        logger.error(f"Failed to save regularized output: {e}")
        return

    # Generate HTML report
    report_path = OUTPUT_DIR / f"regularization_report_{collection}.html"
    logger.info("Generating comparison report...")
    generate_html_report(stats, collection, processing_time, report_path)

    # Print summary
    print(f"\n{'=' * 80}")
    print("REGULARIZATION SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Buildings:              {stats['total_buildings']:,}")
    print(f"Buildings Regularized:        {stats['buildings_regularized']:,}")
    print(f"Buildings Dropped:            {stats['buildings_dropped']:,}")
    print(f"\nVertex Reduction:")
    print(f"  Mean per building:          {stats['vertex_reduction']['mean']:.2f} vertices")
    print(f"  Total reduction:            {stats['vertex_reduction']['total_original'] - stats['vertex_reduction']['total_regularized']:,} vertices")
    print(f"\nArea Preservation:")
    print(f"  Mean change:                {stats['area_preservation']['mean_change_pct']:.3f}%")
    print(f"  Max change:                 {stats['area_preservation']['max_change_pct']:.3f}%")
    print(f"\nOrthogonality Improvement:")
    print(f"  Original:                   {stats['orthogonality']['original_mean_pct']:.2f}%")
    print(f"  Regularized:                {stats['orthogonality']['regularized_mean_pct']:.2f}%")
    print(f"  Improvement:                +{stats['orthogonality']['improvement']:.2f}%")
    print(f"\nProcessing Time:              {processing_time:.2f} seconds")
    print(f"  Rate:                       {len(structures)/processing_time:.1f} buildings/sec")
    print(f"\nOutputs:")
    print(f"  GeoPackage:                 {output_gpkg.name}")
    print(f"  Report:                     {report_path.name}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
