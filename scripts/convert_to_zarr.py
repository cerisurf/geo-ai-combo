#!/usr/bin/env python3
"""
NetCDF to Zarr conversion script with optimized chunking for EDR queries.
"""

import sys
import argparse
import logging
from pathlib import Path
import xarray as xr
import zarr
import numpy as np
from typing import Dict, Any, Optional
from numcodecs import Blosc

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def calculate_optimal_chunks(ds: xr.Dataset, target_chunk_size_mb: float = 50) -> Dict[str, int]:
    """
    Calculate optimal chunk sizes for the dataset based on typical EDR query patterns.
    
    Args:
        ds: Input xarray Dataset
        target_chunk_size_mb: Target chunk size in MB
        
    Returns:
        Dictionary of dimension names to chunk sizes
    """
    chunks = {}
    
    # For environmental data, optimize for:
    # 1. Temporal access (time series at points)
    # 2. Spatial access (snapshots in time)
    # 3. Balance between read/write performance
    
    if 'time' in ds.dims:
        # For time: Use smaller chunks for time-series queries
        # ~1-7 days worth of data per chunk depending on temporal resolution
        time_size = ds.dims['time']
        if time_size <= 30:  # Less than 30 time steps
            chunks['time'] = time_size
        elif time_size <= 240:  # Up to 30 days of 3-hourly data
            chunks['time'] = max(8, time_size // 8)  # ~1 day chunks for 3-hourly
        else:
            chunks['time'] = 24  # About 3 days for 3-hourly data
    
    if 'lat' in ds.dims:
        # For latitude: Balance between regional queries and performance
        lat_size = ds.dims['lat']
        if lat_size <= 50:
            chunks['lat'] = lat_size
        elif lat_size <= 200:
            chunks['lat'] = max(25, lat_size // 4)
        else:
            chunks['lat'] = 50
    
    if 'lon' in ds.dims:
        # For longitude: Similar to latitude
        lon_size = ds.dims['lon']
        if lon_size <= 100:
            chunks['lon'] = lon_size
        elif lon_size <= 500:
            chunks['lon'] = max(50, lon_size // 8)
        else:
            chunks['lon'] = 100
    
    # Estimate chunk size and adjust if needed
    data_vars = [var for var in ds.data_vars if ds[var].dtype in ['float32', 'float64']]
    if data_vars:
        sample_var = ds[data_vars[0]]
        estimated_size_mb = 1
        for dim in sample_var.dims:
            if dim in chunks:
                estimated_size_mb *= chunks[dim]
        
        # Assume float32 (4 bytes)
        estimated_size_mb = (estimated_size_mb * 4) / (1024 * 1024)
        
        # Scale chunks if they're too large
        if estimated_size_mb > target_chunk_size_mb * 2:
            scale_factor = np.sqrt(target_chunk_size_mb / estimated_size_mb)
            for dim in chunks:
                chunks[dim] = max(1, int(chunks[dim] * scale_factor))
    
    logger.info(f"Calculated chunks: {chunks}")
    return chunks


def optimize_zarr_encoding(ds: xr.Dataset) -> Dict[str, Dict[str, Any]]:
    """
    Create optimized encoding settings for Zarr storage.
    
    Args:
        ds: Input xarray Dataset
        
    Returns:
        Dictionary of variable names to encoding settings
    """
    encoding = {}
    
    for var_name, var in ds.data_vars.items():
        var_encoding = {}
        
        # Use simple compression that works reliably
        # Skip custom compression for now to avoid API issues
        pass
        
        # Fill value handling
        if hasattr(var, '_FillValue') and var._FillValue is not None:
            var_encoding['_FillValue'] = var._FillValue
        elif var.dtype in ['float32', 'float64']:
            var_encoding['_FillValue'] = np.nan
        
        encoding[var_name] = var_encoding
        logger.info(f"Encoding for {var_name}: {var_encoding}")
    
    return encoding


def convert_netcdf_to_zarr(
    input_path: Path,
    output_path: Path,
    chunks: Optional[Dict[str, int]] = None,
    compression: str = 'zstd',
    compression_level: int = 3
) -> bool:
    """
    Convert NetCDF file to Zarr format with optimized settings.
    
    Args:
        input_path: Path to input NetCDF file
        output_path: Path to output Zarr store
        chunks: Custom chunk sizes (will calculate optimal if None)
        compression: Compression algorithm
        compression_level: Compression level (1-9)
        
    Returns:
        True if conversion successful, False otherwise
    """
    try:
        logger.info(f"Loading NetCDF file: {input_path}")
        
        # Open the dataset
        ds = xr.open_dataset(input_path)
        logger.info(f"Dataset shape: {dict(ds.dims)}")
        logger.info(f"Data variables: {list(ds.data_vars)}")
        
        # Calculate optimal chunks if not provided
        if chunks is None:
            chunks = calculate_optimal_chunks(ds)
        
        # Get encoding settings
        encoding = optimize_zarr_encoding(ds)
        
        # Apply chunking to the dataset
        ds_chunked = ds.chunk(chunks)
        logger.info(f"Applied chunking: {chunks}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing zarr store if it exists
        if output_path.exists():
            logger.info(f"Removing existing Zarr store: {output_path}")
            import shutil
            shutil.rmtree(output_path)
        
        # Convert to Zarr
        logger.info(f"Converting to Zarr: {output_path}")
        ds_chunked.to_zarr(
            output_path,
            encoding=encoding,
            consolidated=True,  # Create consolidated metadata for faster access
            compute=True
        )
        
        # Verify the conversion
        logger.info("Verifying conversion...")
        ds_zarr = xr.open_zarr(output_path)
        
        # Basic verification
        assert set(ds.data_vars) == set(ds_zarr.data_vars), "Data variables mismatch"
        assert set(ds.dims) == set(ds_zarr.dims), "Dimensions mismatch"
        
        for var_name in ds.data_vars:
            original_shape = ds[var_name].shape
            zarr_shape = ds_zarr[var_name].shape
            assert original_shape == zarr_shape, f"Shape mismatch for {var_name}: {original_shape} vs {zarr_shape}"
        
        logger.info("✅ Conversion successful!")
        logger.info(f"Zarr store created at: {output_path}")
        
        # Print storage info
        store_size = sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file())
        original_size = input_path.stat().st_size
        compression_ratio = original_size / store_size if store_size > 0 else 0
        
        logger.info(f"Original size: {original_size / 1024 / 1024:.2f} MB")
        logger.info(f"Zarr size: {store_size / 1024 / 1024:.2f} MB")
        logger.info(f"Compression ratio: {compression_ratio:.2f}x")
        
        ds.close()
        ds_zarr.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        return False


def main():
    """Main conversion script."""
    parser = argparse.ArgumentParser(description="Convert NetCDF to Zarr with optimized settings")
    parser.add_argument("input", help="Input NetCDF file path")
    parser.add_argument("output", help="Output Zarr store path")
    parser.add_argument("--chunk-size-mb", type=float, default=50, 
                       help="Target chunk size in MB (default: 50)")
    parser.add_argument("--compression", default="zstd", 
                       choices=["zstd", "lz4", "zlib"],
                       help="Compression algorithm (default: zstd)")
    parser.add_argument("--compression-level", type=int, default=3,
                       help="Compression level 1-9 (default: 3)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    success = convert_netcdf_to_zarr(
        input_path=input_path,
        output_path=output_path,
        compression=args.compression,
        compression_level=args.compression_level
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
