#!/usr/bin/env python3
"""
NetCDF to Zarr Converter with Enhanced Metadata for EDR Publisher

Converts downloaded GFS Wave NetCDF files to optimized Zarr format with
human-readable metadata for the EDR API and frontend.

Usage:
    python convert_to_zarr.py input.nc output.zarr [options]

Author: EDR Publisher Team  
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import xarray as xr
import numpy as np
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zarr_conversion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WaveDataConverter:
    """Converts GFS Wave NetCDF data to Zarr format with enhanced metadata."""
    
    def __init__(self):
        # Enhanced metadata mapping for wave variables
        self.variable_metadata = {
            'htsgwsfc': {
                'standard_name': 'sea_surface_wave_significant_height',
                'long_name': 'Significant Height of Combined Wind Waves and Swell',
                'display_name': 'Significant Wave Height',
                'units': 'm',
                'description': 'The significant wave height is the average height of the highest one-third of waves. This represents combined wind waves and swell.',
                'typical_range': [0, 20],
                'color_map': 'viridis',
                'measurement_type': 'wave_height'
            },
            'perpwsfc': {
                'standard_name': 'sea_surface_wave_mean_period_from_variance_spectral_density_first_frequency_moment',
                'long_name': 'Primary Wave Mean Period',
                'display_name': 'Primary Wave Period',
                'units': 's',
                'description': 'The mean period of the primary wave component, representing the time between successive wave crests.',
                'typical_range': [2, 20],
                'color_map': 'plasma',
                'measurement_type': 'wave_period'
            },
            'dirpwsfc': {
                'standard_name': 'sea_surface_wave_from_direction',
                'long_name': 'Primary Wave Direction',
                'display_name': 'Primary Wave Direction',  
                'units': 'degrees',
                'description': 'Direction from which the primary waves are coming, measured clockwise from north (0°=North, 90°=East, 180°=South, 270°=West).',
                'typical_range': [0, 360],
                'color_map': 'hsv',
                'measurement_type': 'wave_direction'
            },
            'wvhgtsfc': {
                'standard_name': 'sea_surface_wave_height',
                'long_name': 'Wave Height',
                'display_name': 'Wave Height',
                'units': 'm',
                'description': 'Height of wind-generated waves at the sea surface.',
                'typical_range': [0, 15],
                'color_map': 'Blues',
                'measurement_type': 'wave_height'
            },
            'wvpersfc': {
                'standard_name': 'sea_surface_wave_period',
                'long_name': 'Wave Period',
                'display_name': 'Wave Period',
                'units': 's',
                'description': 'Period of wind-generated waves at the sea surface.',
                'typical_range': [2, 15],
                'color_map': 'Oranges',
                'measurement_type': 'wave_period'
            },
            'wvdirsfc': {
                'standard_name': 'sea_surface_wave_from_direction',
                'long_name': 'Wave Direction',
                'display_name': 'Wave Direction',
                'units': 'degrees',
                'description': 'Direction from which wind waves are coming.',
                'typical_range': [0, 360],
                'color_map': 'hsv',
                'measurement_type': 'wave_direction'
            },
            'swellsfc': {
                'standard_name': 'sea_surface_swell_wave_height',
                'long_name': 'Swell Wave Height',
                'display_name': 'Swell Height',
                'units': 'm',
                'description': 'Height of swell waves - long-period waves that have traveled far from their generation area.',
                'typical_range': [0, 10],
                'color_map': 'Purples',
                'measurement_type': 'wave_height'
            },
            'swpersfc': {
                'standard_name': 'sea_surface_swell_wave_period',
                'long_name': 'Swell Wave Period',
                'display_name': 'Swell Period',
                'units': 's',
                'description': 'Period of swell waves, typically longer than wind wave periods.',
                'typical_range': [8, 25],
                'color_map': 'Greens',
                'measurement_type': 'wave_period'
            },
            'swdirsfc': {
                'standard_name': 'sea_surface_swell_wave_from_direction',
                'long_name': 'Swell Wave Direction',
                'display_name': 'Swell Direction',
                'units': 'degrees',
                'description': 'Direction from which swell waves are coming.',
                'typical_range': [0, 360],
                'color_map': 'hsv',
                'measurement_type': 'wave_direction'
            }
        }
        
        # Coordinate metadata
        self.coordinate_metadata = {
            'time': {
                'standard_name': 'time',
                'long_name': 'Forecast Time',
                'description': 'Time of forecast validity'
            },
            'lat': {
                'standard_name': 'latitude',
                'long_name': 'Latitude',
                'units': 'degrees_north',
                'description': 'Latitude coordinate'
            },
            'lon': {
                'standard_name': 'longitude', 
                'long_name': 'Longitude',
                'units': 'degrees_east',
                'description': 'Longitude coordinate'
            }
        }
    
    def enhance_metadata(self, ds: xr.Dataset) -> xr.Dataset:
        """Add enhanced metadata to the dataset."""
        
        logger.info("Enhancing dataset metadata...")
        
        # Update global attributes
        ds.attrs.update({
            'title': 'GFS Wave Model Forecast Data - Enhanced for EDR',
            'summary': 'Global wave forecast data from NOAA GFS Wave model, optimized for Environmental Data Retrieval (EDR) API',
            'source': 'NOAA/NCEP Global Forecast System (GFS) Wave Model',
            'institution': 'National Centers for Environmental Prediction (NCEP)',
            'creator_name': 'NOAA/NWS/NCEP',
            'creator_url': 'https://www.ncep.noaa.gov/',
            'license': 'Public Domain',
            'processing_level': 'L3',
            'keywords': 'ocean waves, wave height, wave period, wave direction, swell, weather forecast',
            'conventions': 'CF-1.8, ACDD-1.3',
            'standard_name_vocabulary': 'CF Standard Name Table v79',
            'geospatial_lat_min': float(ds.lat.min()),
            'geospatial_lat_max': float(ds.lat.max()),
            'geospatial_lon_min': float(ds.lon.min()),
            'geospatial_lon_max': float(ds.lon.max()),
            'time_coverage_start': str(ds.time.min().values),
            'time_coverage_end': str(ds.time.max().values),
            'processing_timestamp': datetime.now().isoformat(),
            'format_version': 'Zarr optimized for EDR API v1.0'
        })
        
        # Enhance variable metadata
        for var_name in ds.data_vars:
            if var_name in self.variable_metadata:
                metadata = self.variable_metadata[var_name]
                
                # Update variable attributes
                ds[var_name].attrs.update({
                    'standard_name': metadata['standard_name'],
                    'long_name': metadata['long_name'],
                    'display_name': metadata['display_name'],
                    'units': metadata['units'],
                    'description': metadata['description'],
                    'typical_range': metadata['typical_range'],
                    'visualization': {
                        'color_map': metadata['color_map'],
                        'measurement_type': metadata['measurement_type']
                    }
                })
                
                # Add data quality attributes
                data = ds[var_name].values
                if not np.isnan(data).all():
                    ds[var_name].attrs.update({
                        'actual_range': [float(np.nanmin(data)), float(np.nanmax(data))],
                        'valid_min': float(np.nanmin(data)),
                        'valid_max': float(np.nanmax(data))
                    })
        
        # Enhance coordinate metadata
        for coord_name in ds.coords:
            if coord_name in self.coordinate_metadata:
                metadata = self.coordinate_metadata[coord_name]
                ds[coord_name].attrs.update(metadata)
        
        return ds
    
    def optimize_for_zarr(self, ds: xr.Dataset, chunk_size: Dict[str, int] = None) -> xr.Dataset:
        """Optimize dataset structure for Zarr storage and EDR queries."""
        
        if chunk_size is None:
            # Default chunking strategy optimized for EDR position queries
            chunk_size = {
                'time': min(48, len(ds.time)),  # 2 days worth of 3-hourly data
                'lat': min(200, len(ds.lat)),   # ~50 degree chunks  
                'lon': min(400, len(ds.lon))    # ~100 degree chunks
            }
        
        logger.info(f"Applying chunking strategy: {chunk_size}")
        
        # Apply chunking
        ds_chunked = ds.chunk(chunk_size)
        
        # Ensure time is properly sorted
        if not ds_chunked.time.to_pandas().is_monotonic_increasing:
            logger.info("Sorting by time coordinate...")
            ds_chunked = ds_chunked.sortby('time')
        
        # Convert longitude to -180 to 180 if needed
        if ds_chunked.lon.max() > 180:
            logger.info("Converting longitude from 0-360 to -180-180...")
            ds_chunked = ds_chunked.assign_coords(
                lon=(ds_chunked.lon + 180) % 360 - 180
            ).sortby('lon')
        
        return ds_chunked
    
    def create_edr_metadata(self, ds: xr.Dataset, output_path: Path) -> Dict[str, Any]:
        """Create EDR-specific metadata file."""
        
        # Extract parameter information for EDR API
        parameters = {}
        for var_name in ds.data_vars:
            if var_name in self.variable_metadata:
                metadata = self.variable_metadata[var_name]
                parameters[var_name] = {
                    'type': 'number',
                    'description': metadata['description'],
                    'display_name': metadata['display_name'],
                    'unit': {
                        'label': metadata['units'],
                        'symbol': metadata['units']
                    },
                    'observedProperty': {
                        'id': var_name,
                        'label': metadata['display_name']
                    },
                    'visualization': metadata.get('visualization', {}),
                    'typical_range': metadata['typical_range']
                }
        
        # Create collection metadata
        edr_metadata = {
            'id': output_path.stem,
            'title': 'GFS Wave Model Forecast',
            'description': 'Global wave forecast data from NOAA GFS Wave model',
            'extent': {
                'spatial': {
                    'bbox': [[
                        float(ds.lon.min()),
                        float(ds.lat.min()),
                        float(ds.lon.max()),
                        float(ds.lat.max())
                    ]],
                    'crs': ['WGS84']
                },
                'temporal': {
                    'interval': [[
                        str(ds.time.min().values),
                        str(ds.time.max().values)
                    ]],
                    'trs': ['http://www.opengis.net/def/uom/ISO-8601/0/Gregorian']
                }
            },
            'parameter_names': parameters,
            'crs': ['CRS84'],
            'output_formats': ['GeoJSON', 'CoverageJSON'],
            'data_queries': {
                'position': {
                    'link': {
                        'href': f'/collections/{output_path.stem}/position',
                        'rel': 'data',
                        'variables': {'query_type': 'position'}
                    }
                },
                'area': {
                    'link': {
                        'href': f'/collections/{output_path.stem}/area', 
                        'rel': 'data',
                        'variables': {'query_type': 'area'}
                    }
                }
            }
        }
        
        # Save metadata file
        metadata_path = output_path.parent / f"{output_path.stem}_edr_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(edr_metadata, f, indent=2, default=str)
        
        logger.info(f"EDR metadata saved to: {metadata_path}")
        return edr_metadata
    
    def convert(self, input_path: Path, output_path: Path, 
                chunk_size: Dict[str, int] = None,
                compression_level: int = 3) -> bool:
        """Convert NetCDF to Zarr with enhanced metadata."""
        
        try:
            logger.info(f"Loading NetCDF file: {input_path}")
            
            # Load dataset
            ds = xr.open_dataset(input_path, engine='netcdf4')
            
            logger.info(f"Dataset info:")
            logger.info(f"  Variables: {list(ds.data_vars.keys())}")
            logger.info(f"  Dimensions: {dict(ds.dims)}")
            logger.info(f"  Size: {ds.nbytes / 1024 / 1024:.1f} MB")
            
            # Apply enhancements
            ds_enhanced = self.enhance_metadata(ds)
            ds_optimized = self.optimize_for_zarr(ds_enhanced, chunk_size)
            
            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove existing zarr store if it exists
            if output_path.exists():
                import shutil
                shutil.rmtree(output_path)
            
            # Save to Zarr with compression
            logger.info(f"Saving to Zarr: {output_path}")
            
            # Save with basic compression (xarray will handle encoding properly)
            ds_optimized.to_zarr(
                output_path,
                mode='w',
                consolidated=True
            )
            
            # Create EDR metadata
            self.create_edr_metadata(ds_optimized, output_path)
            
            # Calculate compression ratio
            output_size = sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file())
            compression_ratio = ds.nbytes / output_size if output_size > 0 else 0
            
            logger.info(f"Conversion completed successfully!")
            logger.info(f"  Input size: {ds.nbytes / 1024 / 1024:.1f} MB")
            logger.info(f"  Output size: {output_size / 1024 / 1024:.1f} MB")
            logger.info(f"  Compression ratio: {compression_ratio:.1f}x")
            
            # Cleanup
            ds.close()
            ds_optimized.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return False

def main():
    """Main function to handle command line arguments and run the converter."""
    
    parser = argparse.ArgumentParser(description='Convert GFS Wave NetCDF to Zarr format with EDR metadata')
    parser.add_argument('input', type=str, help='Input NetCDF file path')
    parser.add_argument('output', type=str, help='Output Zarr directory path')
    parser.add_argument('--time-chunks', type=int, default=48,
                       help='Time dimension chunk size (default: 48)')
    parser.add_argument('--lat-chunks', type=int, default=200,
                       help='Latitude dimension chunk size (default: 200)')
    parser.add_argument('--lon-chunks', type=int, default=400,
                       help='Longitude dimension chunk size (default: 400)')
    parser.add_argument('--compression', type=int, default=3, choices=range(1, 10),
                       help='Compression level 1-9 (default: 3)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show conversion info without converting')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    chunk_size = {
        'time': args.time_chunks,
        'lat': args.lat_chunks, 
        'lon': args.lon_chunks
    }
    
    if args.dry_run:
        logger.info("DRY RUN - Conversion info:")
        ds = xr.open_dataset(input_path)
        logger.info(f"  Input: {input_path}")
        logger.info(f"  Output: {output_path}")
        logger.info(f"  Variables: {list(ds.data_vars.keys())}")
        logger.info(f"  Dimensions: {dict(ds.dims)}")
        logger.info(f"  Chunk size: {chunk_size}")
        ds.close()
        return 0
    
    # Initialize converter and run conversion
    converter = WaveDataConverter()
    
    success = converter.convert(
        input_path=input_path,
        output_path=output_path,
        chunk_size=chunk_size,
        compression_level=args.compression
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
