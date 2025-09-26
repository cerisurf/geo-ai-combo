#!/usr/bin/env python3
"""
Script to analyze the provided NetCDF file structure and content.
"""

import xarray as xr
import numpy as np
import sys

def analyze_netcdf(file_path):
    """Analyze NetCDF file structure and content."""
    print(f"Analyzing NetCDF file: {file_path}")
    print("=" * 50)
    
    try:
        # Open the dataset
        ds = xr.open_dataset(file_path)
        
        print("Dataset Overview:")
        print(ds)
        print("\n" + "=" * 50)
        
        print("Dataset Info:")
        print(f"Dimensions: {dict(ds.dims)}")
        print(f"Data variables: {list(ds.data_vars)}")
        print(f"Coordinates: {list(ds.coords)}")
        print(f"Attributes: {list(ds.attrs.keys())}")
        
        print("\n" + "=" * 50)
        print("Variable Details:")
        
        for var_name in ds.data_vars:
            var = ds[var_name]
            print(f"\n{var_name}:")
            print(f"  Shape: {var.shape}")
            print(f"  Dimensions: {var.dims}")
            print(f"  Data type: {var.dtype}")
            print(f"  Attributes: {dict(var.attrs)}")
            
            # Check for valid data
            if np.isfinite(var).any():
                print(f"  Data range: {float(var.min())} to {float(var.max())}")
                print(f"  Mean: {float(var.mean())}")
            else:
                print("  No valid data found")
        
        print("\n" + "=" * 50)
        print("Coordinate Details:")
        
        for coord_name in ds.coords:
            coord = ds[coord_name]
            print(f"\n{coord_name}:")
            print(f"  Shape: {coord.shape}")
            print(f"  Data type: {coord.dtype}")
            print(f"  Range: {float(coord.min())} to {float(coord.max())}")
            if coord_name == 'time':
                print(f"  Start time: {coord.values[0]}")
                print(f"  End time: {coord.values[-1]}")
                print(f"  Time steps: {len(coord)}")
        
        print("\n" + "=" * 50)
        print("Spatial/Temporal Coverage:")
        
        if 'lat' in ds.coords:
            lat_min, lat_max = float(ds.lat.min()), float(ds.lat.max())
            print(f"Latitude range: {lat_min}° to {lat_max}°")
        
        if 'lon' in ds.coords:
            lon_min, lon_max = float(ds.lon.min()), float(ds.lon.max())
            print(f"Longitude range: {lon_min}° to {lon_max}°")
        
        if 'time' in ds.coords:
            time_range = ds.time.max() - ds.time.min()
            print(f"Time span: {time_range}")
            print(f"Number of time steps: {len(ds.time)}")
        
        # Check data quality
        print("\n" + "=" * 50)
        print("Data Quality Assessment:")
        
        for var_name in ds.data_vars:
            var = ds[var_name]
            total_points = var.size
            valid_points = np.isfinite(var).sum().item()
            missing_points = total_points - valid_points
            missing_percent = (missing_points / total_points) * 100
            
            print(f"\n{var_name}:")
            print(f"  Total points: {total_points:,}")
            print(f"  Valid points: {valid_points:,}")
            print(f"  Missing points: {missing_points:,} ({missing_percent:.2f}%)")
        
        ds.close()
        return True
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        return False

if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "sig_wwave_swell-20240623.nc"
    analyze_netcdf(file_path)

