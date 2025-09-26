#!/usr/bin/env python3
"""
Simple GeoServer Raster Publisher

Publishes wave raster files to GeoServer automatically.
"""

import requests
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def publish_wave_rasters(geoserver_url="http://localhost:8081/geoserver", 
                        username="admin", password="geoserver123",
                        workspace="wave_data"):
    """Publish all wave rasters to GeoServer."""
    
    auth = (username, password)
    base_url = geoserver_url.rstrip('/')
    
    # Ensure workspace exists
    resp = requests.post(
        f"{base_url}/rest/workspaces",
        json={"workspace": {"name": workspace}},
        auth=auth
    )
    # 409 = already exists, which is fine
    if resp.status_code not in [201, 409]:
        logger.error(f"Failed to create workspace: {resp.status_code}")
        return []
    
    published_layers = []
    
    # Define rasters to publish (representative sample)
    rasters_to_publish = [
        {
            "file": "/opt/geoserver_data/rasters/2025-09-25/wave_height_2025-09-25_mean.tif",
            "store_name": "wave_height_20250925",
            "layer_name": "wave_height_20250925", 
            "title": "Wave Height - Sep 25, 2025"
        },
        {
            "file": "/opt/geoserver_data/rasters/2025-09-25/wave_direction_2025-09-25_mean.tif",
            "store_name": "wave_direction_20250925",
            "layer_name": "wave_direction_20250925",
            "title": "Wave Direction - Sep 25, 2025"
        },
        {
            "file": "/opt/geoserver_data/rasters/2025-09-25/wave_period_2025-09-25_mean.tif", 
            "store_name": "wave_period_20250925",
            "layer_name": "wave_period_20250925",
            "title": "Wave Period - Sep 25, 2025"
        }
    ]
    
    for raster in rasters_to_publish:
        # Create coverage store
        store_resp = requests.post(
            f"{base_url}/rest/workspaces/{workspace}/coveragestores",
            json={
                "coverageStore": {
                    "name": raster["store_name"],
                    "type": "GeoTIFF",
                    "url": f"file://{raster['file']}"
                }
            },
            auth=auth
        )
        
        if store_resp.status_code == 201:
            logger.info(f"Created store: {raster['store_name']}")
            
            # Create coverage layer
            layer_resp = requests.post(
                f"{base_url}/rest/workspaces/{workspace}/coveragestores/{raster['store_name']}/coverages",
                json={
                    "coverage": {
                        "name": raster["layer_name"],
                        "title": raster["title"],
                        "enabled": True
                    }
                },
                auth=auth
            )
            
            if layer_resp.status_code == 201:
                logger.info(f"Published layer: {workspace}:{raster['layer_name']}")
                published_layers.append(f"{workspace}:{raster['layer_name']}")
            else:
                logger.error(f"Failed to create layer {raster['layer_name']}: {layer_resp.status_code}")
        else:
            logger.warning(f"Store {raster['store_name']} might already exist or failed: {store_resp.status_code}")
    
    return published_layers

if __name__ == "__main__":
    published = publish_wave_rasters()
    print(f"Published {len(published)} layers: {published}")
