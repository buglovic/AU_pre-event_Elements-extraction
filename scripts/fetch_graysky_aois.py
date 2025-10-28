"""
Fetch Graysky-Suncorp AOIs from Vexcel Data Platform API
=========================================================

This script queries the Vexcel API for Graysky-Suncorp event AOIs covering
Australia and New Zealand, and saves them as a GeoPackage for further processing.

Environment Variables:
    VDP_USERNAME: Vexcel Data Platform username
    VDP_PASSWORD: Vexcel Data Platform password

Usage:
    python fetch_graysky_aois.py --output ../input/graysky_suncorp_aois.gpkg
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import shape

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VexcelAPIClient:
    """Simplified Vexcel API client for collection queries."""

    DEFAULT_API_BASE_URL = "https://api.vexcelgroup.com/v2"
    TOKEN_LIFETIME_HOURS = 24

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """Initialize API client with credentials."""
        self.api_base_url = self.DEFAULT_API_BASE_URL
        self.username = username or os.getenv("VDP_USERNAME")
        self.password = password or os.getenv("VDP_PASSWORD")
        self.token: Optional[str] = None

        if not self.username or not self.password:
            raise ValueError(
                "VDP_USERNAME and VDP_PASSWORD environment variables must be set"
            )

    def authenticate(self) -> str:
        """Authenticate and get API token."""
        logger.info(f"Authenticating as: {self.username}")

        url = f"{self.api_base_url}/auth/login"
        payload = {"username": self.username, "password": self.password}

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            self.token = data.get("token")

            if not self.token:
                raise ValueError("API response does not contain token")

            logger.info("Authentication successful")
            return self.token

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def get_graysky_collections(
        self,
        wkt: str,
        layers: str = "graysky, graysky-suncorp",
        max_records: int = 1000
    ) -> Dict:
        """
        Query Graysky collections for a given WKT geometry.

        Args:
            wkt: Well-Known Text geometry (polygon covering region)
            layers: Comma-separated layer names (default: "graysky, graysky-suncorp")
            max_records: Maximum number of records to return

        Returns:
            GeoJSON FeatureCollection with collection metadata
        """
        if not self.token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        url = f"{self.api_base_url}/ortho/collections"
        params = {
            "wkt": wkt,
            "srid": "4326",
            "layer": layers,
            "include": "layer, collection, graysky-event, graysky-event-pretty-name, avg-gsd, geometry, first-capture-date, last-capture-date",
            "max-records": max_records
        }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Querying Graysky collections with layers: {layers}")

        try:
            response = requests.get(url, params=params, headers=headers, timeout=120)
            response.raise_for_status()

            data = response.json()
            num_features = len(data.get('features', []))
            logger.info(f"Found {num_features} Graysky collections")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query collections: {e}")
            raise


def geojson_to_geopackage(geojson_data: Dict, output_path: Path) -> gpd.GeoDataFrame:
    """
    Convert GeoJSON data to GeoDataFrame and save as GeoPackage.

    Args:
        geojson_data: GeoJSON FeatureCollection dictionary
        output_path: Path to save GeoPackage

    Returns:
        GeoDataFrame with processed data
    """
    features = geojson_data.get('features', [])

    if not features:
        logger.warning("No features found in GeoJSON data")
        return None

    # Extract properties and geometries
    records = []
    for feature in features:
        props = feature.get('properties', {})
        geom = shape(feature.get('geometry'))

        record = {
            'collection': props.get('collection'),
            'layer': props.get('layer'),
            'event_id': props.get('graysky-event'),
            'event_name': props.get('graysky-event-pretty-name'),
            'avg_gsd': props.get('avg-gsd'),
            'first_capture_date': props.get('first-capture-date'),
            'last_capture_date': props.get('last-capture-date'),
            'geometry': geom
        }
        records.append(record)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")

    # Add metadata columns
    gdf['fetch_date'] = datetime.now().isoformat()
    gdf['area_km2'] = gdf.geometry.to_crs("EPSG:3857").area / 1e6

    # Convert capture dates to datetime for proper sorting
    gdf['last_capture_date'] = pd.to_datetime(gdf['last_capture_date'], errors='coerce')
    gdf['first_capture_date'] = pd.to_datetime(gdf['first_capture_date'], errors='coerce')

    # Sort by last capture date descending (newest first), then by event name
    gdf = gdf.sort_values(['last_capture_date', 'event_name'], ascending=[False, True]).reset_index(drop=True)

    # Save to GeoPackage
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver='GPKG', layer='graysky_aois')

    logger.info(f"Saved {len(gdf)} AOIs to: {output_path}")

    return gdf


def print_summary(gdf: gpd.GeoDataFrame):
    """Print summary statistics of fetched AOIs."""
    if gdf is None or len(gdf) == 0:
        logger.warning("No data to summarize")
        return

    print("\n" + "="*60)
    print("GRAYSKY-SUNCORP AOI SUMMARY")
    print("="*60)
    print(f"Total AOIs: {len(gdf)}")
    print(f"Total area: {gdf['area_km2'].sum():.2f} km²")
    print()

    print("By Layer:")
    print(gdf['layer'].value_counts().to_string())
    print()

    print("By Event (sorted by last capture date, newest first):")
    event_summary = gdf.groupby('event_name').agg({
        'collection': 'count',
        'area_km2': 'sum',
        'last_capture_date': 'max'
    }).rename(columns={'collection': 'count'})
    event_summary = event_summary.sort_values('last_capture_date', ascending=False)
    print(event_summary.to_string())
    print()

    print(f"Average GSD: {gdf['avg_gsd'].mean():.4f}")
    print(f"GSD range: {gdf['avg_gsd'].min():.4f} - {gdf['avg_gsd'].max():.4f}")
    print("="*60 + "\n")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Fetch Graysky-Suncorp AOIs from Vexcel API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        default="../input/graysky_suncorp_aois.gpkg",
        help="Output GeoPackage path (default: ../input/graysky_suncorp_aois.gpkg)"
    )

    parser.add_argument(
        "--wkt",
        type=str,
        default="POLYGON ((103.886629 -49.037847, 183.691316 -49.037847, 183.691316 -5.440991, 103.886629 -5.440991, 103.886629 -49.037847))",
        help="WKT geometry for query (default: AU/NZ bounding box)"
    )

    parser.add_argument(
        "--layers",
        type=str,
        default="graysky, graysky-suncorp",
        help="Comma-separated layer names (default: graysky, graysky-suncorp)"
    )

    parser.add_argument(
        "--max-records",
        type=int,
        default=1000,
        help="Maximum number of records to fetch (default: 1000)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate environment variables
    if not os.getenv("VDP_USERNAME") or not os.getenv("VDP_PASSWORD"):
        logger.error("VDP_USERNAME and VDP_PASSWORD environment variables must be set")
        return 1

    try:
        # Initialize client and authenticate
        client = VexcelAPIClient()
        client.authenticate()

        # Fetch Graysky collections
        geojson_data = client.get_graysky_collections(
            wkt=args.wkt,
            layers=args.layers,
            max_records=args.max_records
        )

        # Save raw GeoJSON for reference
        output_path = Path(args.output)
        json_path = output_path.with_suffix('.json')
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(geojson_data, f, indent=2)
        logger.info(f"Saved raw GeoJSON to: {json_path}")

        # Convert to GeoPackage
        gdf = geojson_to_geopackage(geojson_data, output_path)

        if gdf is not None:
            # Print summary
            print_summary(gdf)

            print(f"\n✓ Successfully fetched {len(gdf)} Graysky-Suncorp AOIs")
            print(f"✓ Saved to: {output_path}")
            print(f"✓ Layer name: graysky_aois")
            return 0
        else:
            logger.error("No AOIs found")
            return 1

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
