#!/usr/bin/env python3
"""
GFS Wave Data Downloader for EDR Publisher

Downloads wave forecast data from NOAA's NOMADS GrADS Data Server.
This script downloads GFS Wave model data and saves it locally for processing.

Usage:
    python download_gfs_wave.py [options]

Author: EDR Publisher Team
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin
import requests
import xarray as xr
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gfs_wave_download.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GFSWaveDownloader:
    """Downloads GFS Wave data from NOAA NOMADS server."""
    
    def __init__(self, base_url: str = "https://nomads.ncep.noaa.gov/dods/wave/gfswave"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EDR-Publisher/1.0 (Marine Data Pipeline)'
        })
        # Allow redirects and add timeout defaults
        self.session.max_redirects = 5
    
    def get_available_dates(self, days_back: int = 7) -> List[str]:
        """Get list of available forecast dates from the server."""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            # Parse HTML to extract available directories
            # For now, generate dates based on current date
            dates = []
            today = datetime.now()
            
            for i in range(days_back):
                date = today - timedelta(days=i)
                date_str = date.strftime("%Y%m%d")
                dates.append(date_str)
            
            logger.info(f"Found {len(dates)} potential dates: {dates}")
            return dates
            
        except Exception as e:
            logger.error(f"Failed to get available dates: {e}")
            return []
    
    def get_forecast_runs(self, date: str) -> List[str]:
        """Get available forecast runs for a given date (00, 06, 12, 18Z)."""
        runs = ["00", "06", "12", "18"]
        available_runs = []
        
        for run in runs:
            # Check if this run is available using OPeNDAP endpoint
            test_url = f"{self.base_url}/{date}/gfswave.global.0p25_{run}z"
            try:
                response = self.session.head(test_url, timeout=10)
                if response.status_code == 200:
                    available_runs.append(run)
            except:
                continue
                
        logger.info(f"Available runs for {date}: {available_runs}")
        return available_runs
    
    def download_grib2_file(self, date: str, run: str, forecast_hour: str, 
                           output_dir: Path, region: Optional[str] = None) -> Optional[Path]:
        """
        Download a specific GRIB2 file.
        
        Args:
            date: Date in YYYYMMDD format
            run: Forecast run (00, 06, 12, 18)
            forecast_hour: Forecast hour (000, 003, 006, ..., 384)
            output_dir: Directory to save the file
            region: Region subset (global, atlantic, pacific, etc.)
        """
        # GRIB2 files use a different naming convention
        if region is None:
            region = "global.0p25"
            
        filename = f"gfswave.t{run}z.{region}.f{forecast_hour}.grib2"
        # Note: GRIB2 files may use different URL structure than OPeNDAP
        url = f"{self.base_url}/{date}/{filename}"
        
        output_path = output_dir / f"{date}_{run}z_{forecast_hour}.grib2"
        
        try:
            logger.info(f"Downloading: {url}")
            
            response = self.session.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            # Get file size for progress tracking
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rProgress: {progress:.1f}%", end='', flush=True)
            
            print()  # New line after progress
            logger.info(f"Downloaded: {output_path} ({downloaded / 1024 / 1024:.1f} MB)")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if output_path.exists():
                output_path.unlink()
            return None
    
    def download_netcdf_via_dods(self, date: str, run: str, output_dir: Path,
                                variables: List[str] = None, 
                                time_range: tuple = None,
                                spatial_bounds: dict = None) -> Optional[Path]:
        """
        Download data via OPeNDAP (DODS) as NetCDF.
        
        Args:
            date: Date in YYYYMMDD format  
            run: Forecast run (00, 06, 12, 18)
            output_dir: Directory to save the file
            variables: List of variables to download
            time_range: (start_idx, end_idx) for time dimension
            spatial_bounds: {'lat': (min, max), 'lon': (min, max)}
        """
        
        # Default variables for wave data
        if variables is None:
            variables = [
                'htsgwsfc',  # Significant wave height
                'perpwsfc',  # Primary wave mean period  
                'dirpwsfc',  # Primary wave direction
                'wvhgtsfc',  # Wave height
                'wvpersfc',  # Wave period
                'wvdirsfc',  # Wave direction
                'swellsfc',  # Swell wave height
                'swpersfc',  # Swell wave period
                'swdirsfc'   # Swell wave direction
            ]
        
        # Construct OPeNDAP URL
        dataset_name = f"gfswave{run}_{date}"
        resolution = "25"  # 0.25 degree resolution
        dods_url = f"{self.base_url}/{date}/gfswave.global.0p{resolution}_{run}z"
        
        output_path = output_dir / f"{dataset_name}.nc"
        
        try:
            logger.info(f"Accessing OPeNDAP dataset: {dods_url}")
            
            # Test URL accessibility first with a simple request
            test_response = self.session.get(dods_url + ".das", timeout=30)
            if test_response.status_code != 200:
                logger.error(f"Dataset not accessible (HTTP {test_response.status_code})")
                return None
            
            # Add delay to be respectful to server
            time.sleep(2)
            
            # Open the dataset via OPeNDAP
            ds = xr.open_dataset(dods_url, engine='netcdf4')
            
            logger.info(f"Dataset info:")
            logger.info(f"  Variables: {list(ds.variables.keys())}")
            logger.info(f"  Dimensions: {ds.dims}")
            logger.info(f"  Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
            
            # Filter variables
            available_vars = [var for var in variables if var in ds.variables]
            if not available_vars:
                logger.error("No requested variables found in dataset")
                return None
                
            logger.info(f"Downloading variables: {available_vars}")
            
            # Apply spatial subset if specified
            if spatial_bounds:
                lat_min, lat_max = spatial_bounds.get('lat', (-90, 90))
                lon_min, lon_max = spatial_bounds.get('lon', (-180, 180))
                
                ds = ds.sel(
                    lat=slice(lat_min, lat_max),
                    lon=slice(lon_min, lon_max)
                )
                logger.info(f"Applied spatial subset: lat({lat_min}, {lat_max}), lon({lon_min}, {lon_max})")
            
            # Apply time subset if specified
            if time_range:
                start_idx, end_idx = time_range
                ds = ds.isel(time=slice(start_idx, end_idx))
                logger.info(f"Applied time subset: {start_idx} to {end_idx}")
            
            # Select only the variables we want
            ds_subset = ds[available_vars]
            
            # Add metadata
            ds_subset.attrs.update({
                'title': 'GFS Wave Model Forecast Data',
                'source': 'NOAA/NCEP Global Forecast System Wave Model',
                'downloaded_by': 'EDR Publisher Data Pipeline',
                'download_time': datetime.now().isoformat(),
                'original_url': dods_url,
                'forecast_date': date,
                'forecast_run': f"{run}Z"
            })
            
            # Save to NetCDF
            logger.info(f"Saving to: {output_path}")
            ds_subset.to_netcdf(output_path, engine='netcdf4')
            
            # Close dataset
            ds.close()
            ds_subset.close()
            
            file_size = output_path.stat().st_size / 1024 / 1024
            logger.info(f"Downloaded: {output_path} ({file_size:.1f} MB)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download via OPeNDAP: {e}")
            if output_path.exists():
                output_path.unlink()
            return None

def main():
    """Main function to handle command line arguments and run the downloader."""
    
    parser = argparse.ArgumentParser(description='Download GFS Wave data from NOAA NOMADS')
    parser.add_argument('--date', type=str, help='Date in YYYYMMDD format (default: latest)')
    parser.add_argument('--run', type=str, choices=['00', '06', '12', '18'], 
                       help='Forecast run (default: latest available)')
    parser.add_argument('--output-dir', type=str, default='./data/raw',
                       help='Output directory (default: ./data/raw)')
    parser.add_argument('--method', choices=['dods', 'grib2'], default='dods',
                       help='Download method (default: dods)')
    parser.add_argument('--variables', nargs='+', 
                       help='Variables to download (default: wave height variables)')
    parser.add_argument('--region', type=str, 
                       help='Spatial bounds as lat_min,lat_max,lon_min,lon_max')
    parser.add_argument('--hours', type=int, default=48,
                       help='Number of forecast hours to download (default: 48)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be downloaded without downloading')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize downloader
    downloader = GFSWaveDownloader()
    
    # Get date and run
    if args.date:
        date = args.date
    else:
        available_dates = downloader.get_available_dates(days_back=3)
        if not available_dates:
            logger.error("No available dates found")
            return 1
        date = available_dates[0]
    
    if args.run:
        run = args.run
    else:
        available_runs = downloader.get_forecast_runs(date)
        if not available_runs:
            logger.error(f"No available runs found for {date}")
            return 1
        run = available_runs[-1]  # Get latest run
    
    logger.info(f"Downloading GFS Wave data for {date} {run}Z")
    
    if args.dry_run:
        logger.info("DRY RUN - Would download:")
        logger.info(f"  Date: {date}")
        logger.info(f"  Run: {run}Z")
        logger.info(f"  Method: {args.method}")
        logger.info(f"  Hours: {args.hours}")
        return 0
    
    # Parse spatial bounds
    spatial_bounds = None
    if args.region:
        try:
            lat_min, lat_max, lon_min, lon_max = map(float, args.region.split(','))
            spatial_bounds = {
                'lat': (lat_min, lat_max),
                'lon': (lon_min, lon_max)
            }
        except ValueError:
            logger.error("Invalid region format. Use: lat_min,lat_max,lon_min,lon_max")
            return 1
    
    # Download data
    if args.method == 'dods':
        # Calculate time range based on hours
        max_time_steps = args.hours // 3  # GFS output every 3 hours
        time_range = (0, max_time_steps) if args.hours else None
        
        output_path = downloader.download_netcdf_via_dods(
            date=date,
            run=run,
            output_dir=output_dir,
            variables=args.variables,
            time_range=time_range,
            spatial_bounds=spatial_bounds
        )
    else:
        # GRIB2 download (for specific forecast hours)
        forecast_hours = [f"{h:03d}" for h in range(0, args.hours + 1, 3)]
        logger.info(f"Downloading forecast hours: {forecast_hours}")
        
        downloaded_files = []
        for hour in forecast_hours:
            output_path = downloader.download_grib2_file(
                date=date,
                run=run,
                forecast_hour=hour,
                output_dir=output_dir
            )
            if output_path:
                downloaded_files.append(output_path)
            time.sleep(1)  # Be nice to the server
        
        logger.info(f"Downloaded {len(downloaded_files)} files")
    
    if output_path:
        logger.info(f"Download completed successfully: {output_path}")
        return 0
    else:
        logger.error("Download failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
