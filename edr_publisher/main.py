"""
FastAPI application for EDR Publisher.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from .api import router, initialize_data_accessor
from .config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EDR Publisher",
    description="OGC Environmental Data Retrieval API with Zarr backend",
    version="0.1.0",
    docs_url="/api",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include EDR routes
app.include_router(router, tags=["EDR API"])


@app.on_event("startup")
async def startup_event():
    """Initialize the application."""
    logger.info("Starting EDR Publisher API")
    
    # Get the active dataset dynamically
    active_dataset = config.get_active_dataset()
    
    if active_dataset:
        zarr_path = active_dataset["path"]
        logger.info(f"Initializing data accessor with latest dataset: {active_dataset['id']}")
        logger.info(f"Dataset path: {zarr_path}")
        logger.info(f"Last modified: {active_dataset['modified_iso']}")
        
        try:
            initialize_data_accessor(zarr_path)
            logger.info("Data accessor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize data accessor: {e}")
    else:
        logger.warning("No datasets found in data directory")
        logger.warning("Run the data pipeline first: bash scripts/update_gfs_wave.sh")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    logger.info("Shutting down EDR Publisher API")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
