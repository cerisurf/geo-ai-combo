"""
Pydantic models for OGC EDR API responses.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class LinkRel(str, Enum):
    """Standard link relation types for EDR API."""
    SELF = "self"
    ALTERNATE = "alternate"
    COLLECTION = "collection"
    DESCRIBEDBY = "describedBy"
    DATA = "data"


class Link(BaseModel):
    """OGC API Link object."""
    href: str
    rel: LinkRel
    type: Optional[str] = None
    title: Optional[str] = None
    hreflang: Optional[str] = None


class LandingPage(BaseModel):
    """OGC API Landing Page."""
    title: str
    description: str
    links: List[Link]


class ConformanceClasses(BaseModel):
    """OGC API Conformance response."""
    conformsTo: List[str]


class Extent(BaseModel):
    """Spatial and temporal extent."""
    spatial: Optional[Dict[str, Any]] = None
    temporal: Optional[Dict[str, Any]] = None


class Parameter(BaseModel):
    """Data parameter information."""
    type: str
    description: Optional[str] = None
    unit: Optional[Dict[str, Any]] = None
    observedProperty: Optional[Dict[str, Any]] = None


class Collection(BaseModel):
    """EDR Collection metadata."""
    id: str
    title: str
    description: str
    links: List[Link]
    extent: Extent
    parameter_names: Dict[str, Parameter]
    crs: List[str] = Field(default=["CRS84"])
    output_formats: List[str] = Field(default=["GeoJSON", "CoverageJSON"])
    data_queries: Dict[str, Dict[str, Any]]


class Collections(BaseModel):
    """Collections response."""
    links: List[Link]
    collections: List[Collection]


class QueryType(str, Enum):
    """Supported EDR query types."""
    POSITION = "position"
    AREA = "area"
    CUBE = "cube"
    TRAJECTORY = "trajectory"
    CORRIDOR = "corridor"


class ParameterName(BaseModel):
    """Parameter name for queries."""
    parameter_name: str


class CoverageJSON(BaseModel):
    """CoverageJSON response structure."""
    type: str = "Coverage"
    domain: Dict[str, Any]
    ranges: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature."""
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection."""
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]


# Common query parameters
class CommonQueryParams(BaseModel):
    """Common query parameters for EDR requests."""
    datetime: Optional[str] = None
    parameter_name: Optional[str] = None
    crs: Optional[str] = None
    f: Optional[str] = Field(default="GeoJSON", description="Output format")


class PositionQuery(CommonQueryParams):
    """Position query parameters."""
    coords: str = Field(..., description="POINT(lon lat) or lon,lat")
    z: Optional[str] = None


class AreaQuery(CommonQueryParams):
    """Area query parameters."""
    coords: str = Field(..., description="POLYGON or bbox coordinates")
    z: Optional[str] = None


class CubeQuery(CommonQueryParams):
    """Cube query parameters."""
    bbox: str = Field(..., description="Bounding box: minlon,minlat,maxlon,maxlat")
    z: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    code: str
    description: str
