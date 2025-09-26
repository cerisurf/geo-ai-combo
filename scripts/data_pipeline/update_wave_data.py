#!/usr/bin/env python3
"""
GFS Wave Data Update Workflow for EDR Publisher

Complete workflow script that downloads the latest GFS Wave data,
converts it to Zarr format, and updates the EDR API data store.

Usage:
    python update_wave_data.py [options]

Author: EDR Publisher Team
"""

import argparse
import logging
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json
import shutil
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wave_data_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WaveDataUpdater:
    """Manages the complete workflow for updating wave data."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent
        
        # Paths
        self.raw_data_dir = Path(config.get('raw_data_dir', './data/raw'))
        self.zarr_data_dir = Path(config.get('zarr_data_dir', './data'))
        self.backup_dir = Path(config.get('backup_dir', './data/backup'))
        
        # Create directories
        for dir_path in [self.raw_data_dir, self.zarr_data_dir, self.backup_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def cleanup_old_files(self, directory: Path, days_to_keep: int = 7):
        """Remove files older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for file_path in directory.glob('*'):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    logger.info(f"Removing old file: {file_path}")
                    file_path.unlink()
    
    def backup_existing_data(self, zarr_path: Path) -> Optional[Path]:
        """Backup existing Zarr data before replacement."""
        if not zarr_path.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{zarr_path.name}_{timestamp}"
        
        logger.info(f"Backing up existing data to: {backup_path}")
        shutil.copytree(zarr_path, backup_path)
        return backup_path
    
    def download_latest_data(self, **kwargs) -> Optional[Path]:
        """Download the latest GFS Wave data."""
        logger.info("Starting data download...")
        
        # Prepare download command
        download_script = self.script_dir / "download_gfs_wave.py"
        cmd = [
            sys.executable, str(download_script),
            "--output-dir", str(self.raw_data_dir),
            "--method", "dods"
        ]
        
        # Add optional arguments
        if kwargs.get('date'):
            cmd.extend(["--date", kwargs['date']])
        if kwargs.get('run'):
            cmd.extend(["--run", kwargs['run']])
        if kwargs.get('region'):
            cmd.extend(["--region", kwargs['region']])
        if kwargs.get('hours'):
            cmd.extend(["--hours", str(kwargs['hours'])])
        if kwargs.get('variables'):
            cmd.extend(["--variables"] + kwargs['variables'])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Download completed successfully")
            
            # Find the downloaded file
            nc_files = list(self.raw_data_dir.glob("*.nc"))
            if nc_files:
                # Return the most recent file
                latest_file = max(nc_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Downloaded file: {latest_file}")
                return latest_file
            else:
                logger.error("No NetCDF file found after download")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Download failed: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return None
    
    def convert_to_zarr(self, input_file: Path, output_name: str = "gfs_wave_data") -> Optional[Path]:
        """Convert NetCDF to Zarr format."""
        logger.info(f"Converting {input_file} to Zarr...")
        
        output_path = self.zarr_data_dir / f"{output_name}.zarr"
        
        # Prepare conversion command
        convert_script = self.script_dir / "convert_to_zarr.py"
        cmd = [
            sys.executable, str(convert_script),
            str(input_file),
            str(output_path),
            "--compression", str(self.config.get('compression_level', 3))
        ]
        
        # Add chunking parameters if specified
        if self.config.get('time_chunks'):
            cmd.extend(["--time-chunks", str(self.config['time_chunks'])])
        if self.config.get('lat_chunks'):
            cmd.extend(["--lat-chunks", str(self.config['lat_chunks'])])
        if self.config.get('lon_chunks'):
            cmd.extend(["--lon-chunks", str(self.config['lon_chunks'])])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Conversion completed successfully")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Conversion failed: {e}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return None
    
    def update_edr_config(self, zarr_path: Path, metadata_file: Path):
        """Update EDR API configuration with new dataset."""
        logger.info("Updating EDR API configuration...")
        
        # Load EDR metadata
        with open(metadata_file, 'r') as f:
            edr_metadata = json.load(f)
        
        # Update configuration file (if exists)
        config_file = self.project_root / "edr_publisher" / "config.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {"collections": {}}
        
        # Update collection info
        collection_id = edr_metadata['id']
        config['collections'][collection_id] = {
            'data_path': str(zarr_path),
            'metadata': edr_metadata,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Updated EDR config for collection: {collection_id}")
    
    def validate_zarr_data(self, zarr_path: Path) -> bool:
        """Validate the Zarr data by performing basic checks."""
        try:
            import xarray as xr
            
            logger.info(f"Validating Zarr data: {zarr_path}")
            
            # Open and check the dataset
            ds = xr.open_zarr(zarr_path)
            
            # Basic validation checks
            checks = {
                'has_time_dimension': 'time' in ds.dims,
                'has_spatial_dimensions': 'lat' in ds.dims and 'lon' in ds.dims,
                'has_data_variables': len(ds.data_vars) > 0,
                'time_is_sorted': ds.time.to_pandas().is_monotonic_increasing,
                'no_all_nan_variables': all(not ds[var].isnull().all() for var in ds.data_vars)
            }
            
            # Log validation results
            all_passed = True
            for check, passed in checks.items():
                status = "✓" if passed else "✗"
                logger.info(f"  {status} {check}: {passed}")
                if not passed:
                    all_passed = False
            
            # Additional info
            logger.info(f"  Variables: {list(ds.data_vars.keys())}")
            logger.info(f"  Time range: {ds.time.min().values} to {ds.time.max().values}")
            logger.info(f"  Spatial extent: {ds.lat.min().values:.2f}°N to {ds.lat.max().values:.2f}°N, {ds.lon.min().values:.2f}°E to {ds.lon.max().values:.2f}°E")
            
            ds.close()
            return all_passed
            
        except Exception as e:
            logger.error(f"Zarr validation failed: {e}")
            return False
    
    def restart_edr_service(self):
        """Restart the EDR API service if running in Docker."""
        try:
            # Check if we're in a Docker environment
            compose_file = self.project_root / "docker-compose.yml"
            if compose_file.exists():
                logger.info("Restarting EDR API service...")
                cmd = ["docker-compose", "restart", "edr-api"]
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("EDR API service restarted successfully")
                else:
                    logger.warning(f"Failed to restart EDR service: {result.stderr}")
            else:
                logger.info("Not in Docker environment, skipping service restart")
                
        except Exception as e:
            logger.warning(f"Could not restart EDR service: {e}")
    
    def run_update(self, **kwargs) -> bool:
        """Run the complete update workflow."""
        logger.info("Starting GFS Wave data update workflow...")
        
        try:
            # 1. Clean up old files
            if self.config.get('cleanup_old_files', True):
                self.cleanup_old_files(self.raw_data_dir, self.config.get('days_to_keep', 7))
                self.cleanup_old_files(self.backup_dir, self.config.get('backup_retention_days', 30))
            
            # 2. Download latest data
            nc_file = self.download_latest_data(**kwargs)
            if not nc_file:
                logger.error("Failed to download data")
                return False
            
            # 3. Backup existing Zarr data
            zarr_name = kwargs.get('output_name', 'gfs_wave_data')
            zarr_path = self.zarr_data_dir / f"{zarr_name}.zarr"
            backup_path = self.backup_existing_data(zarr_path)
            
            # 4. Convert to Zarr
            new_zarr_path = self.convert_to_zarr(nc_file, zarr_name)
            if not new_zarr_path:
                logger.error("Failed to convert to Zarr")
                return False
            
            # 5. Validate new Zarr data
            if not self.validate_zarr_data(new_zarr_path):
                logger.error("Zarr validation failed")
                # Restore backup if available
                if backup_path and backup_path.exists():
                    logger.info("Restoring backup data...")
                    if new_zarr_path.exists():
                        shutil.rmtree(new_zarr_path)
                    shutil.copytree(backup_path, new_zarr_path)
                return False
            
            # 6. Update EDR configuration
            metadata_file = new_zarr_path.parent / f"{new_zarr_path.stem}_edr_metadata.json"
            if metadata_file.exists():
                self.update_edr_config(new_zarr_path, metadata_file)
            
            # 7. Restart EDR service
            if self.config.get('restart_service', True):
                self.restart_edr_service()
            
            # 8. Clean up raw NetCDF file
            if self.config.get('cleanup_raw_files', True):
                logger.info(f"Cleaning up raw file: {nc_file}")
                nc_file.unlink()
            
            logger.info("Update workflow completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Update workflow failed: {e}")
            return False

def load_config(config_file: Optional[Path] = None) -> Dict:
    """Load configuration from file or use defaults."""
    
    default_config = {
        'raw_data_dir': './data/raw',
        'zarr_data_dir': './data',
        'backup_dir': './data/backup',
        'compression_level': 3,
        'time_chunks': 48,
        'lat_chunks': 200,
        'lon_chunks': 400,
        'cleanup_old_files': True,
        'cleanup_raw_files': True,
        'days_to_keep': 7,
        'backup_retention_days': 30,
        'restart_service': True
    }
    
    if config_file and config_file.exists():
        with open(config_file, 'r') as f:
            user_config = json.load(f)
        default_config.update(user_config)
    
    return default_config

def main():
    """Main function to handle command line arguments and run the updater."""
    
    parser = argparse.ArgumentParser(description='Update GFS Wave data for EDR Publisher')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--date', type=str, help='Specific date to download (YYYYMMDD)')
    parser.add_argument('--run', type=str, choices=['00', '06', '12', '18'],
                       help='Specific forecast run')
    parser.add_argument('--region', type=str,
                       help='Spatial bounds as lat_min,lat_max,lon_min,lon_max')
    parser.add_argument('--hours', type=int, default=120,
                       help='Number of forecast hours (default: 120)')
    parser.add_argument('--variables', nargs='+',
                       help='Specific variables to download')
    parser.add_argument('--output-name', type=str, default='gfs_wave_data',
                       help='Output Zarr dataset name')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without doing it')
    
    args = parser.parse_args()
    
    # Load configuration
    config_file = Path(args.config) if args.config else None
    config = load_config(config_file)
    
    if args.dry_run:
        logger.info("DRY RUN - Update workflow:")
        logger.info(f"  Config: {config}")
        logger.info(f"  Date: {args.date or 'latest'}")
        logger.info(f"  Run: {args.run or 'latest'}")
        logger.info(f"  Hours: {args.hours}")
        logger.info(f"  Output: {args.output_name}")
        return 0
    
    # Initialize updater
    updater = WaveDataUpdater(config)
    
    # Prepare keyword arguments
    kwargs = {
        'output_name': args.output_name,
        'hours': args.hours
    }
    
    if args.date:
        kwargs['date'] = args.date
    if args.run:
        kwargs['run'] = args.run
    if args.region:
        kwargs['region'] = args.region
    if args.variables:
        kwargs['variables'] = args.variables
    
    # Run the update
    success = updater.run_update(**kwargs)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
