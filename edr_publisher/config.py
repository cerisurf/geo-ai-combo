"""
Configuration management for EDR Publisher.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class EDRConfig:
    """Configuration manager for EDR API."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.data_dir = Path(__file__).parent.parent / "data"
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or use defaults."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
                self._config = {}
        else:
            self._config = {}
        
        # Set defaults
        self._config.setdefault("data_directory", str(self.data_dir))
        self._config.setdefault("default_collection", "latest")
        self._config.setdefault("auto_discover", True)
    
    def get_available_datasets(self) -> List[Dict[str, Any]]:
        """Discover all available Zarr datasets in the data directory."""
        datasets = []
        
        for zarr_path in self.data_dir.glob("*.zarr"):
            metadata_path = self.data_dir / f"{zarr_path.stem}_edr_metadata.json"
            
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Get modification time for sorting
                    mod_time = zarr_path.stat().st_mtime
                    
                    datasets.append({
                        "id": metadata.get("id", zarr_path.stem),
                        "path": str(zarr_path),
                        "metadata_path": str(metadata_path),
                        "metadata": metadata,
                        "modified": mod_time,
                        "modified_iso": datetime.fromtimestamp(mod_time).isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to load metadata for {zarr_path}: {e}")
        
        # Sort by modification time (newest first)
        datasets.sort(key=lambda x: x["modified"], reverse=True)
        
        logger.info(f"Found {len(datasets)} available datasets")
        for ds in datasets:
            logger.info(f"  - {ds['id']} (modified: {ds['modified_iso']})")
        
        return datasets
    
    def get_active_dataset(self) -> Optional[Dict[str, Any]]:
        """Get the currently active dataset."""
        datasets = self.get_available_datasets()
        
        if not datasets:
            logger.warning("No datasets found in data directory")
            return None
        
        # Check if a specific collection is configured
        collection_id = self._config.get("active_collection")
        if collection_id and collection_id != "latest":
            for dataset in datasets:
                if dataset["id"] == collection_id:
                    logger.info(f"Using configured dataset: {collection_id}")
                    return dataset
            logger.warning(f"Configured dataset '{collection_id}' not found, using latest")
        
        # Use the most recent dataset
        latest = datasets[0]
        logger.info(f"Using latest dataset: {latest['id']}")
        return latest
    
    def set_active_collection(self, collection_id: str):
        """Set the active collection and save to config."""
        self._config["active_collection"] = collection_id
        self._save_config()
    
    def _save_config(self):
        """Save current configuration to file."""
        if self.config_path:
            try:
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self._config, f, indent=2)
                logger.info(f"Saved configuration to {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to save config: {e}")
    
    def get_data_directory(self) -> Path:
        """Get the data directory path."""
        return Path(self._config["data_directory"])
    
    def reload(self):
        """Reload configuration from file."""
        self._load_config()


# Global configuration instance
config = EDRConfig()
