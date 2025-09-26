#!/usr/bin/env python3
"""
NetCDF to GeoTIFF Raster Converter for Wave Data

Converts NetCDF wave data to daily GeoTIFF rasters for automated GeoServer publishing.
"""

import logging
import argparse
import xarray as xr
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NetCDFToRasterConverter:
    """Converts NetCDF wave data to GeoTIFF rasters."""
    
    def __init__(self, output_dir: str = "data/rasters"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Wave parameter mapping to human-readable names and descriptions
        self.parameter_mapping = {
            'htsgwsfc': {
                'name': 'wave_height',
                'title': 'Significant Wave Height',
                'description': 'Combined wind waves and swell height',
                'units': 'meters',
                'color_scale': 'viridis',
                'value_range': [0, 8]
            },
            'dirpwsfc': {
                'name': 'wave_direction',
                'title': 'Primary Wave Direction',
                'description': 'Direction of primary wave component',
                'units': 'degrees',
                'color_scale': 'hsv',
                'value_range': [0, 360]
            },
            'perpwsfc': {
                'name': 'wave_period',
                'title': 'Primary Wave Period',
                'description': 'Period of primary wave component',
                'units': 'seconds',
                'color_scale': 'plasma',
                'value_range': [2, 20]
            },
            'wvhgtsfc': {
                'name': 'wind_wave_height',
                'title': 'Wind Wave Height',
                'description': 'Height of wind-generated waves',
                'units': 'meters',
                'color_scale': 'viridis',
                'value_range': [0, 6]
            },
            'wvpersfc': {
                'name': 'wind_wave_period',
                'title': 'Wind Wave Period',
                'description': 'Period of wind-generated waves',
                'units': 'seconds',
                'color_scale': 'plasma',
                'value_range': [2, 15]
            },
            'wvdirsfc': {
                'name': 'wind_wave_direction',
                'title': 'Wind Wave Direction',
                'description': 'Direction of wind-generated waves',
                'units': 'degrees',
                'color_scale': 'hsv',
                'value_range': [0, 360]
            }
        }
    
    def convert_netcdf_to_rasters(self, netcdf_path: str, aggregation: str = "daily_avg") -> List[str]:
        """
        Convert NetCDF file to daily GeoTIFF rasters.
        
        Args:
            netcdf_path: Path to input NetCDF file
            aggregation: Aggregation method ('daily_avg', 'daily_max', 'hourly')
            
        Returns:
            List of created GeoTIFF file paths
        """
        logger.info(f"Converting {netcdf_path} to GeoTIFF rasters")
        
        # Load NetCDF dataset
        ds = xr.open_dataset(netcdf_path)
        logger.info(f"Loaded dataset with dimensions: {dict(ds.dims)}")
        logger.info(f"Variables: {list(ds.data_vars)}")
        
        # Get spatial information
        lats = ds.lat.values
        lons = ds.lon.values
        times = ds.time.values
        
        # Create geotransform
        transform = from_bounds(
            lons.min(), lats.min(), lons.max(), lats.max(),
            len(lons), len(lats)
        )
        
        # Set CRS (WGS84)
        crs = CRS.from_epsg(4326)
        
        created_files = []
        
        if aggregation == "daily_avg":
            created_files.extend(self._create_daily_aggregates(
                ds, transform, crs, "mean"
            ))
        elif aggregation == "daily_max":
            created_files.extend(self._create_daily_aggregates(
                ds, transform, crs, "max"
            ))
        elif aggregation == "hourly":
            created_files.extend(self._create_hourly_rasters(
                ds, transform, crs
            ))
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
        
        logger.info(f"Created {len(created_files)} GeoTIFF files")
        
        # Create metadata file
        metadata_file = self._create_raster_metadata(ds, created_files)
        created_files.append(metadata_file)
        
        return created_files
    
    def _create_daily_aggregates(self, ds: xr.Dataset, transform, crs, method: str) -> List[str]:
        """Create daily aggregate rasters."""
        created_files = []
        
        # Group by day
        daily_groups = ds.groupby('time.date')
        
        for date, daily_data in daily_groups:
            date_str = date.strftime('%Y-%m-%d')
            date_dir = self.output_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            logger.info(f"Processing {date_str} with {len(daily_data.time)} time steps")
            
            # Process each parameter
            for param, config in self.parameter_mapping.items():
                if param not in ds.data_vars:
                    continue
                
                # Aggregate daily data
                if method == "mean":
                    daily_aggregate = daily_data[param].mean(dim='time')
                elif method == "max":
                    daily_aggregate = daily_data[param].max(dim='time')
                else:
                    continue
                
                # Create filename
                filename = f"{config['name']}_{date_str}_{method}.tif"
                filepath = date_dir / filename
                
                # Convert to raster
                self._write_geotiff(
                    daily_aggregate.values,
                    filepath,
                    transform,
                    crs,
                    config
                )
                
                created_files.append(str(filepath))
        
        return created_files
    
    def _create_hourly_rasters(self, ds: xr.Dataset, transform, crs) -> List[str]:
        """Create individual hourly rasters."""
        created_files = []
        
        for i, time_val in enumerate(ds.time.values):
            timestamp = datetime.fromisoformat(str(time_val)[:19])
            date_str = timestamp.strftime('%Y-%m-%d')
            hour_str = timestamp.strftime('%H')
            
            date_dir = self.output_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Process each parameter
            for param, config in self.parameter_mapping.items():
                if param not in ds.data_vars:
                    continue
                
                # Get data for this time step
                time_data = ds[param].isel(time=i)
                
                # Create filename
                filename = f"{config['name']}_{date_str}_{hour_str}00.tif"
                filepath = date_dir / filename
                
                # Convert to raster
                self._write_geotiff(
                    time_data.values,
                    filepath,
                    transform,
                    crs,
                    config
                )
                
                created_files.append(str(filepath))
        
        return created_files
    
    def _write_geotiff(self, data: np.ndarray, filepath: Path, transform, crs, config: Dict):
        """Write data array to GeoTIFF file."""
        # Handle NaN values
        data = np.flipud(data)  # Flip latitude for proper orientation
        
        # Set nodata value
        nodata_value = -9999.0
        data = np.where(np.isnan(data), nodata_value, data)
        
        # Write GeoTIFF
        with rasterio.open(
            filepath,
            'w',
            driver='GTiff',
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype=data.dtype,
            crs=crs,
            transform=transform,
            nodata=nodata_value,
            compress='lzw',
            tiled=True,
            blockxsize=256,
            blockysize=256
        ) as dst:
            dst.write(data, 1)
            
            # Add metadata
            dst.update_tags(
                TITLE=config['title'],
                DESCRIPTION=config['description'],
                UNITS=config['units'],
                VALUE_RANGE=f"{config['value_range'][0]}-{config['value_range'][1]}",
                COLOR_SCALE=config['color_scale']
            )
        
        logger.debug(f"Created {filepath}")
    
    def _create_raster_metadata(self, ds: xr.Dataset, created_files: List[str]) -> str:
        """Create metadata file for the raster collection."""
        metadata = {
            "dataset_info": {
                "title": "GFS Wave Model Rasters",
                "description": "Daily raster files converted from NOAA GFS Wave NetCDF data",
                "source": "NOAA Global Forecast System Wave Model",
                "spatial_extent": {
                    "lat_min": float(ds.lat.min()),
                    "lat_max": float(ds.lat.max()),
                    "lon_min": float(ds.lon.min()),
                    "lon_max": float(ds.lon.max())
                },
                "temporal_extent": {
                    "start": str(ds.time.values[0])[:19],
                    "end": str(ds.time.values[-1])[:19]
                },
                "created": datetime.now().isoformat()
            },
            "parameters": self.parameter_mapping,
            "files": {
                "count": len(created_files),
                "paths": created_files
            }
        }
        
        metadata_file = self.output_dir / "raster_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Created metadata file: {metadata_file}")
        return str(metadata_file)
    
    def create_geoserver_datastore_config(self, workspace: str = "edr_data") -> Dict:
        """Create GeoServer datastore configuration for the raster directory."""
        config = {
            "coverageStore": {
                "name": "wave_rasters",
                "workspace": workspace,
                "type": "ImageMosaic",
                "url": f"file:///opt/data/rasters",
                "description": "Daily wave raster mosaics from GFS model"
            }
        }
        return config


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Convert NetCDF wave data to GeoTIFF rasters")
    parser.add_argument("input_file", help="Input NetCDF file path")
    parser.add_argument("--output-dir", default="data/rasters", help="Output directory for rasters")
    parser.add_argument("--aggregation", choices=["daily_avg", "daily_max", "hourly"], 
                       default="daily_avg", help="Aggregation method")
    
    args = parser.parse_args()
    
    # Create converter
    converter = NetCDFToRasterConverter(args.output_dir)
    
    # Convert NetCDF to rasters
    created_files = converter.convert_netcdf_to_rasters(
        args.input_file, 
        args.aggregation
    )
    
    logger.info(f"Conversion complete! Created {len(created_files)} files")
    logger.info(f"Output directory: {args.output_dir}")
    
    # Print GeoServer configuration
    geoserver_config = converter.create_geoserver_datastore_config()
    logger.info("GeoServer datastore configuration:")
    print(json.dumps(geoserver_config, indent=2))


if __name__ == "__main__":
    main()
