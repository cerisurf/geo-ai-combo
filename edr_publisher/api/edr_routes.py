"""
EDR API route handlers.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging

from ..models.edr_models import (
    LandingPage, ConformanceClasses, Collections, Collection,
    Link, LinkRel, PositionQuery, AreaQuery, ErrorResponse
)
from ..data.zarr_accessor import ZarrDataAccessor
from ..config import config

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Global data accessor - in a production system, this would be dependency-injected
_data_accessor: Optional[ZarrDataAccessor] = None


def get_data_accessor() -> ZarrDataAccessor:
    """Get the global data accessor."""
    global _data_accessor
    if _data_accessor is None:
        raise HTTPException(status_code=500, detail="Data accessor not initialized")
    return _data_accessor


def initialize_data_accessor(zarr_path: str):
    """Initialize the global data accessor."""
    global _data_accessor
    _data_accessor = ZarrDataAccessor(zarr_path)


@router.get("/", response_model=LandingPage)
async def landing_page():
    """OGC API Landing Page."""
    return LandingPage(
        title="EDR Publisher API",
        description="OGC Environmental Data Retrieval API with Zarr backend",
        links=[
            Link(href="/", rel=LinkRel.SELF, type="application/json", title="Landing page"),
            Link(href="/conformance", rel=LinkRel.ALTERNATE, type="application/json", title="Conformance"),
            Link(href="/collections", rel=LinkRel.ALTERNATE, type="application/json", title="Collections"),
            Link(href="/api", rel=LinkRel.DESCRIBEDBY, type="application/vnd.oai.openapi+json;version=3.0", title="API definition"),
        ]
    )


@router.get("/conformance", response_model=ConformanceClasses)
async def conformance():
    """OGC API Conformance classes."""
    return ConformanceClasses(
        conformsTo=[
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/landing-page",
            "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/json",
            "http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core",
            "http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/position",
            "http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/area",
        ]
    )


@router.get("/collections", response_model=Collections)
async def get_collections(data_accessor: ZarrDataAccessor = Depends(get_data_accessor)):
    """Get available collections."""
    try:
        metadata = data_accessor.get_collection_metadata()
        
        collection = Collection(
            id=metadata["id"],
            title=metadata["title"],
            description=metadata["description"],
            links=[
                Link(
                    href=f"/collections/{metadata['id']}", 
                    rel=LinkRel.SELF, 
                    type="application/json",
                    title="Collection metadata"
                ),
                Link(
                    href=f"/collections/{metadata['id']}/position", 
                    rel=LinkRel.DATA, 
                    type="application/json",
                    title="Position queries"
                ),
                Link(
                    href=f"/collections/{metadata['id']}/area", 
                    rel=LinkRel.DATA, 
                    type="application/json",
                    title="Area queries"
                ),
            ],
            extent=metadata["extent"],
            parameter_names=metadata["parameter_names"],
            data_queries=metadata["data_queries"],
            crs=metadata["crs"],
            output_formats=metadata["output_formats"]
        )
        
        return Collections(
            links=[
                Link(href="/collections", rel=LinkRel.SELF, type="application/json", title="Collections")
            ],
            collections=[collection]
        )
        
    except Exception as e:
        logger.error(f"Error getting collections: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve collections")


@router.get("/collections/{collection_id}", response_model=Collection)
async def get_collection(
    collection_id: str,
    data_accessor: ZarrDataAccessor = Depends(get_data_accessor)
):
    """Get collection metadata."""
    try:
        metadata = data_accessor.get_collection_metadata()
        
        if collection_id != metadata["id"]:
            raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found")
        
        return Collection(
            id=metadata["id"],
            title=metadata["title"],
            description=metadata["description"],
            links=[
                Link(
                    href=f"/collections/{metadata['id']}", 
                    rel=LinkRel.SELF, 
                    type="application/json",
                    title="Collection metadata"
                ),
                Link(
                    href=f"/collections/{metadata['id']}/position", 
                    rel=LinkRel.DATA, 
                    type="application/json",
                    title="Position queries"
                ),
                Link(
                    href=f"/collections/{metadata['id']}/area", 
                    rel=LinkRel.DATA, 
                    type="application/json",
                    title="Area queries"
                ),
            ],
            extent=metadata["extent"],
            parameter_names=metadata["parameter_names"],
            data_queries=metadata["data_queries"],
            crs=metadata["crs"],
            output_formats=metadata["output_formats"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection {collection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve collection")


@router.get("/collections/{collection_id}/position")
async def position_query(
    collection_id: str,
    coords: str = Query(..., description="Point coordinates as POINT(lon lat) or lon,lat"),
    datetime: Optional[str] = Query(None, description="ISO 8601 datetime or interval"),
    parameter_name: Optional[str] = Query(None, alias="parameter-name", description="Parameter name"),
    f: str = Query("GeoJSON", description="Output format"),
    crs: Optional[str] = Query("CRS84", description="Coordinate reference system"),
    data_accessor: ZarrDataAccessor = Depends(get_data_accessor)
):
    """Position query endpoint."""
    try:
        # Validate collection
        metadata = data_accessor.get_collection_metadata()
        if collection_id != metadata["id"]:
            raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found")
        
        # Parse coordinates
        try:
            lon, lat = data_accessor.parse_coordinates(coords, "position")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid coordinates: {e}")
        
        # Parse datetime
        try:
            datetime_slice = data_accessor.parse_datetime(datetime)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid datetime: {e}")
        
        # Validate parameter name
        if parameter_name and parameter_name not in metadata["parameter_names"]:
            available_params = list(metadata["parameter_names"].keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Parameter {parameter_name} not available. Available: {available_params}"
            )
        
        # Execute query
        result = data_accessor.query_position(
            lon=lon, 
            lat=lat, 
            datetime_slice=datetime_slice,
            parameter_name=parameter_name
        )
        
        # Return based on format
        if f.upper() == "GEOJSON":
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {f}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in position query: {e}")
        raise HTTPException(status_code=500, detail="Query execution failed")


@router.get("/collections/{collection_id}/area")
async def area_query(
    collection_id: str,
    coords: str = Query(..., description="Area coordinates as POLYGON(...) or bbox"),
    datetime: Optional[str] = Query(None, description="ISO 8601 datetime or interval"),
    parameter_name: Optional[str] = Query(None, alias="parameter-name", description="Parameter name"),
    f: str = Query("GeoJSON", description="Output format"),
    crs: Optional[str] = Query("CRS84", description="Coordinate reference system"),
    data_accessor: ZarrDataAccessor = Depends(get_data_accessor)
):
    """Area query endpoint."""
    try:
        # Validate collection
        metadata = data_accessor.get_collection_metadata()
        if collection_id != metadata["id"]:
            raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found")
        
        # Parse coordinates
        try:
            polygon_coords = data_accessor.parse_coordinates(coords, "area")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid coordinates: {e}")
        
        # Parse datetime
        try:
            datetime_slice = data_accessor.parse_datetime(datetime)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid datetime: {e}")
        
        # Validate parameter name
        if parameter_name and parameter_name not in metadata["parameter_names"]:
            available_params = list(metadata["parameter_names"].keys())
            raise HTTPException(
                status_code=400, 
                detail=f"Parameter {parameter_name} not available. Available: {available_params}"
            )
        
        # Execute query
        result = data_accessor.query_area(
            polygon_coords=polygon_coords,
            datetime_slice=datetime_slice,
            parameter_name=parameter_name
        )
        
        # Return based on format
        if f.upper() == "GEOJSON":
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {f}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in area query: {e}")
        raise HTTPException(status_code=500, detail="Query execution failed")


# Administrative endpoints
@router.get("/admin/datasets")
async def list_datasets():
    """List all available datasets."""
    try:
        datasets = config.get_available_datasets()
        return {
            "datasets": [
                {
                    "id": ds["id"],
                    "modified": ds["modified_iso"],
                    "title": ds["metadata"].get("title", "Unknown"),
                    "description": ds["metadata"].get("description", ""),
                    "variables": list(ds["metadata"].get("parameter_names", {}).keys())
                }
                for ds in datasets
            ],
            "active": config.get_active_dataset()["id"] if config.get_active_dataset() else None
        }
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        raise HTTPException(status_code=500, detail="Failed to list datasets")


@router.post("/admin/reload")
async def reload_datasets():
    """Reload datasets and reinitialize data accessor with latest."""
    try:
        global _data_accessor
        
        # Reload configuration
        config.reload()
        
        # Get the latest dataset
        active_dataset = config.get_active_dataset()
        
        if active_dataset:
            # Reinitialize data accessor
            _data_accessor = ZarrDataAccessor(active_dataset["path"])
            
            return {
                "status": "success",
                "message": f"Reloaded with dataset: {active_dataset['id']}",
                "dataset": {
                    "id": active_dataset["id"],
                    "modified": active_dataset["modified_iso"],
                    "path": active_dataset["path"]
                }
            }
        else:
            raise HTTPException(status_code=404, detail="No datasets found")
            
    except Exception as e:
        logger.error(f"Error reloading datasets: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload datasets")


@router.post("/admin/switch/{dataset_id}")
async def switch_dataset(dataset_id: str):
    """Switch to a specific dataset."""
    try:
        global _data_accessor
        
        datasets = config.get_available_datasets()
        target_dataset = None
        
        for ds in datasets:
            if ds["id"] == dataset_id:
                target_dataset = ds
                break
        
        if not target_dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
        
        # Set as active and reinitialize
        config.set_active_collection(dataset_id)
        _data_accessor = ZarrDataAccessor(target_dataset["path"])
        
        return {
            "status": "success",
            "message": f"Switched to dataset: {dataset_id}",
            "dataset": {
                "id": target_dataset["id"],
                "modified": target_dataset["modified_iso"],
                "path": target_dataset["path"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching dataset: {e}")
        raise HTTPException(status_code=500, detail="Failed to switch dataset")
