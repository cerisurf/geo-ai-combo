# EDR Publisher

An OGC Environmental Data Retrieval (EDR) API implementation with multi-service architecture including Vue.js frontend, GeoServer WMS, and real-time wave data from NOAA.

## Architecture

```
NOAA NOMADS → Data Pipeline → Zarr Store → EDR API ← Vue.js Frontend
                            ↓
                          NetCDF → GeoServer → WMS Layers
```

## Features

- **Live Wave Data**: Downloads fresh GFS Wave data from NOAA NOMADS
- **Multi-Service Stack**: EDR API, GeoServer WMS, Vue.js frontend
- **Human-Readable Metadata**: Parameter names like "Significant Wave Height"
- **European Focus**: Optimized for European waters coverage
- **OGC Standards**: EDR API and WMS compliance
- **Containerized**: Docker-based deployment with no rebuilds needed

## Quick Start

### 🚀 **Start All Services**
```bash
# Start EDR API, GeoServer, and Frontend
docker-compose --profile geoserver --profile frontend up -d
```

### 📊 **Access Services**
- **Frontend**: http://localhost:3000 (Vue.js + Leaflet map)
- **EDR API**: http://localhost:8080 (Wave data queries)
- **GeoServer**: http://localhost:8081/geoserver (admin/geoserver123)

### 🌊 **Download Fresh Wave Data**
```bash
# Download latest European wave data (runs inside container - no rebuilds!)
docker exec edr-publisher-api bash scripts/update_gfs_wave.sh --region europe --hours 72

# Download global wave data
docker exec edr-publisher-api bash scripts/update_gfs_wave.sh --region global --hours 120

# Restart EDR API to pick up new data
docker restart edr-publisher-api

# Convert to GeoTIFF rasters for GeoServer
docker exec edr-publisher-api python scripts/netcdf_to_rasters.py \
  data/raw/gfswave00_$(date +%Y%m%d).nc \
  --output-dir data/rasters \
  --aggregation daily_avg

# Copy rasters to GeoServer
docker cp data/rasters edr-geoserver:/opt/geoserver_data/
```

### 🗺️ **Publish Wave Rasters in GeoServer**

**GeoTIFF rasters are now automatically created and copied to GeoServer!** 

**Manual Publishing (one-time setup per dataset):**
1. Open http://localhost:8081/geoserver (admin/geoserver123)
2. Go to **Data → Stores → Add new Store**
3. Select **GeoTIFF** from raster data sources
4. Configure for each raster file:
   - **Workspace**: `wave_data`
   - **Data Source Name**: `wave_height_2025_09_25`
   - **URL**: `file:///opt/geoserver_data/rasters/2025-09-25/wave_height_2025-09-25_mean.tif`
5. **Publish Layer** with human-readable title
6. Repeat for other dates and parameters

**Available Raster Parameters:**
- `wave_height_YYYY-MM-DD_mean.tif` - Significant Wave Height
- `wave_direction_YYYY-MM-DD_mean.tif` - Wave Direction  
- `wave_period_YYYY-MM-DD_mean.tif` - Wave Period
- `wind_wave_height_YYYY-MM-DD_mean.tif` - Wind Wave Height
- `wind_wave_direction_YYYY-MM-DD_mean.tif` - Wind Wave Direction
- `wind_wave_period_YYYY-MM-DD_mean.tif` - Wind Wave Period

**Test WMS Layers:**
```bash
# List available layers
curl "http://localhost:8081/geoserver/wave_data/wms?service=WMS&version=1.1.0&request=GetCapabilities" | grep -i "wave_height"

# Get wave height raster
curl "http://localhost:8081/geoserver/wave_data/wms?service=WMS&version=1.1.0&request=GetMap&layers=wave_data:wave_height_2025-09-25_mean&styles=&bbox=0,40,40,70&width=512&height=512&srs=EPSG:4326&format=image/png" -o wave_height.png
```

### 🌐 **Update Frontend for Fresh Data**
```bash
# If frontend isn't showing fresh data, restart it to refresh connections
docker restart edr-frontend

# The frontend will automatically:
# - Connect to fresh EDR data via /api proxy
# - Display human-readable parameter names
# - Show updated time ranges in charts
```

### 🧪 **Test the Complete Pipeline**
```bash
# 1. Test EDR API with fresh European data
curl "http://localhost:8080/collections/wave_data/position?coords=5.0,52.0&f=GeoJSON"

# 2. Check fresh date ranges
curl "http://localhost:8080/collections" | jq '.collections[0].extent.temporal'

# 3. Test WMS layer (after GeoServer config)
curl "http://localhost:8081/geoserver/edr_data/wms?service=WMS&version=1.1.0&request=GetCapabilities"

# 4. Test frontend connectivity
curl "http://localhost:3000" | grep -i "EDR Publisher"
```

### 🔄 **For Regular Updates**
```bash
# Complete refresh workflow:
docker exec edr-publisher-api bash scripts/update_gfs_wave.sh --region europe --hours 72
docker restart edr-publisher-api
docker cp data/raw/gfswave00_$(date +%Y%m%d).nc edr-geoserver:/opt/geoserver/data_dir/
# Then update GeoServer layers via web interface
```

## API Endpoints

- `GET /` - Landing page
- `GET /conformance` - Conformance classes
- `GET /collections` - Available collections
- `GET /collections/{collection_id}` - Collection metadata
- `GET /collections/{collection_id}/position` - Position queries
- `GET /collections/{collection_id}/area` - Area queries

## Project Structure

```
edr-publisher/
├── edr_publisher/          # Main package
│   ├── __init__.py
│   ├── main.py            # FastAPI application
│   ├── models/            # Pydantic models
│   ├── api/               # API route handlers
│   ├── core/              # Core business logic
│   └── data/              # Data access layer
├── scripts/               # Utility scripts
├── tests/                 # Test suite
├── data/                  # Sample data and storage
└── docs/                  # Documentation
```

