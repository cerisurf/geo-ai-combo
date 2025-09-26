#!/usr/bin/env python3
"""
GeoServer Raster Publisher

Automates publishing of wave raster files to GeoServer via REST API.
"""

import requests
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeoServerRasterPublisher:
    """Automates GeoServer raster layer publishing."""
    
    def __init__(self, geoserver_url: str = "http://localhost:8081/geoserver", 
                 username: str = "admin", password: str = "geoserver123"):
        self.base_url = geoserver_url.rstrip('/')
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        
        # Wave parameter styling configurations
        self.parameter_styles = {
            'wave_height': {
                'colormap': 'viridis',
                'min_value': 0,
                'max_value': 8,
                'units': 'meters'
            },
            'wave_direction': {
                'colormap': 'hsv',
                'min_value': 0,
                'max_value': 360,
                'units': 'degrees'
            },
            'wave_period': {
                'colormap': 'plasma',
                'min_value': 2,
                'max_value': 20,
                'units': 'seconds'
            },
            'wind_wave_height': {
                'colormap': 'viridis',
                'min_value': 0,
                'max_value': 6,
                'units': 'meters'
            },
            'wind_wave_period': {
                'colormap': 'plasma',
                'min_value': 2,
                'max_value': 15,
                'units': 'seconds'
            },
            'wind_wave_direction': {
                'colormap': 'hsv',
                'min_value': 0,
                'max_value': 360,
                'units': 'degrees'
            }
        }
    
    def create_workspace(self, workspace_name: str = "wave_data") -> bool:
        """Create workspace if it doesn't exist."""
        url = f"{self.base_url}/rest/workspaces"
        
        # Check if workspace exists
        response = self.session.get(f"{url}/{workspace_name}")
        if response.status_code == 200:
            logger.info(f"Workspace '{workspace_name}' already exists")
            return True
        
        # Create workspace
        workspace_config = {
            "workspace": {
                "name": workspace_name
            }
        }
        
        response = self.session.post(
            url,
            json=workspace_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            logger.info(f"Created workspace: {workspace_name}")
            return True
        else:
            logger.error(f"Failed to create workspace: {response.status_code} - {response.text}")
            return False
    
    def publish_raster_directory(self, raster_dir: str, workspace: str = "wave_data") -> List[str]:
        """
        Publish all GeoTIFF files in a directory as individual layers.
        
        Args:
            raster_dir: Path to directory containing GeoTIFF files
            workspace: GeoServer workspace name
            
        Returns:
            List of successfully published layer names
        """
        published_layers = []
        raster_path = Path(raster_dir)
        
        if not raster_path.exists():
            logger.error(f"Raster directory not found: {raster_dir}")
            return published_layers
        
        # Ensure workspace exists
        self.create_workspace(workspace)
        
        # Find all GeoTIFF files
        tiff_files = list(raster_path.rglob("*.tif"))
        logger.info(f"Found {len(tiff_files)} GeoTIFF files to publish")
        
        for tiff_file in tiff_files:
            # Create layer name from filename
            layer_name = tiff_file.stem
            
            # Publish individual raster
            if self.publish_single_raster(str(tiff_file), layer_name, workspace):
                published_layers.append(f"{workspace}:{layer_name}")
        
        logger.info(f"Successfully published {len(published_layers)} layers")
        return published_layers
    
    def publish_single_raster(self, tiff_path: str, layer_name: str, workspace: str) -> bool:
        """Publish a single GeoTIFF file as a coverage layer."""
        
        # Step 1: Create coverage store
        store_name = f"{layer_name}_store"
        if not self.create_coverage_store(tiff_path, store_name, workspace):
            return False
        
        # Step 2: Publish coverage layer
        if not self.create_coverage_layer(store_name, layer_name, workspace):
            return False
        
        # Step 3: Apply styling
        self.apply_layer_styling(layer_name, workspace)
        
        return True
    
    def create_coverage_store(self, tiff_path: str, store_name: str, workspace: str) -> bool:
        """Create a GeoTIFF coverage store."""
        url = f"{self.base_url}/rest/workspaces/{workspace}/coveragestores"
        
        # Use container path
        container_path = tiff_path.replace('/Users/ceriwhitmore/code/edr-publisher/data', '/opt')
        
        store_config = {
            "coverageStore": {
                "name": store_name,
                "type": "GeoTIFF",
                "url": f"file://{container_path}"
            }
        }
        
        response = self.session.post(
            url,
            json=store_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            logger.debug(f"Created coverage store: {store_name}")
            return True
        else:
            logger.error(f"Failed to create coverage store {store_name}: {response.status_code}")
            return False
    
    def create_coverage_layer(self, store_name: str, layer_name: str, workspace: str) -> bool:
        """Create a coverage layer from the store."""
        url = f"{self.base_url}/rest/workspaces/{workspace}/coveragestores/{store_name}/coverages"
        
        # Determine parameter type for metadata
        param_type = self._get_parameter_type(layer_name)
        style_config = self.parameter_styles.get(param_type, {})
        
        layer_config = {
            "coverage": {
                "name": layer_name,
                "title": self._format_layer_title(layer_name),
                "description": f"Wave data: {layer_name}",
                "keywords": {
                    "string": ["wave", "ocean", "forecast", param_type]
                },
                "srs": "EPSG:4326",
                "enabled": True
            }
        }
        
        response = self.session.post(
            url,
            json=layer_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            logger.info(f"Published layer: {workspace}:{layer_name}")
            return True
        else:
            logger.error(f"Failed to create layer {layer_name}: {response.status_code}")
            return False
    
    def apply_layer_styling(self, layer_name: str, workspace: str):
        """Apply appropriate styling to the layer."""
        param_type = self._get_parameter_type(layer_name)
        
        if param_type not in self.parameter_styles:
            return
        
        style_config = self.parameter_styles[param_type]
        
        # For now, just log the styling that should be applied
        # Full SLD creation would be more complex
        logger.debug(f"Layer {layer_name} should use {style_config['colormap']} colormap "
                    f"with range {style_config['min_value']}-{style_config['max_value']} {style_config['units']}")
    
    def _get_parameter_type(self, layer_name: str) -> str:
        """Extract parameter type from layer name."""
        for param in self.parameter_styles.keys():
            if param in layer_name:
                return param
        return 'wave_height'  # default
    
    def _format_layer_title(self, layer_name: str) -> str:
        """Format a human-readable layer title."""
        # Extract date and parameter
        parts = layer_name.split('_')
        if len(parts) >= 4:  # e.g., wave_height_2025-09-25_mean
            param = '_'.join(parts[:-2])
            date = parts[-2]
            agg = parts[-1]
            return f"{param.replace('_', ' ').title()} - {date} ({agg})"
        return layer_name.replace('_', ' ').title()
    
    def list_published_layers(self, workspace: str = "wave_data") -> List[str]:
        """List all published layers in workspace."""
        url = f"{self.base_url}/rest/workspaces/{workspace}/layers"
        
        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'layers' in data and 'layer' in data['layers']:
                return [layer['name'] for layer in data['layers']['layer']]
        
        return []
    
    def get_wms_capabilities_url(self) -> str:
        """Get WMS GetCapabilities URL."""
        return f"{self.base_url}/wms?service=WMS&version=1.1.0&request=GetCapabilities"


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Publish wave rasters to GeoServer")
    parser.add_argument("raster_dir", help="Directory containing GeoTIFF raster files")
    parser.add_argument("--workspace", default="wave_data", help="GeoServer workspace name")
    parser.add_argument("--geoserver-url", default="http://localhost:8081/geoserver", 
                       help="GeoServer base URL")
    parser.add_argument("--username", default="admin", help="GeoServer username")
    parser.add_argument("--password", default="geoserver123", help="GeoServer password")
    
    args = parser.parse_args()
    
    # Create publisher
    publisher = GeoServerRasterPublisher(
        args.geoserver_url, 
        args.username, 
        args.password
    )
    
    # Publish rasters
    published_layers = publisher.publish_raster_directory(args.raster_dir, args.workspace)
    
    logger.info(f"Publishing complete!")
    logger.info(f"Published layers: {published_layers}")
    logger.info(f"WMS Capabilities: {publisher.get_wms_capabilities_url()}")


if __name__ == "__main__":
    main()
