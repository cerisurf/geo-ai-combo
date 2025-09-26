# EDR Publisher - Docker Deployment Guide

## 🐳 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for convenience commands)

### 1. Build and Deploy
```bash
# Clone and navigate to project
cd edr-publisher

# Build the image
make build
# OR: docker-compose build

# Convert data and start API
make up
# OR: docker-compose --profile converter run --rm edr-converter && docker-compose up -d edr-api
```

### 2. Test the Deployment
```bash
# Quick health check
curl http://localhost:8080/

# Full API test
make test

# View logs
make logs
```

### 3. Access the API
- **API Endpoint**: http://localhost:8080
- **Interactive Docs**: http://localhost:8080/api
- **ReDoc**: http://localhost:8080/redoc

## 📦 **Architecture Overview**

### Service Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   EDR API       │    │   Redis Cache   │
│   (Production)  │────│   (FastAPI)     │────│   (Optional)    │
│   Port 80/443   │    │   Port 8000     │    │   Port 6379     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Zarr Data     │
                       │   (Persistent)  │
                       └─────────────────┘
```

### Container Profiles
- **Default**: Core EDR API only
- **Cache**: API + Redis caching layer
- **Production**: API + Nginx reverse proxy + Redis
- **Converter**: One-time data conversion service

## 🚀 **Deployment Scenarios**

### Development
```bash
# Quick development setup
make dev-up

# Watch logs in real-time
make logs

# Get shell access
make shell
```

### Production
```bash
# Full production deployment with caching and reverse proxy
make prod-up

# Access via Nginx (port 8090)
curl http://localhost:8090/collections
```

### Data Conversion Only
```bash
# Convert NetCDF to Zarr without starting API
make convert
```

## 🔧 **Configuration**

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `EDR_HOST` | `0.0.0.0` | API bind address |
| `EDR_PORT` | `8000` | API port |
| `EDR_DATA_PATH` | `/app/data` | Zarr data directory |
| `EDR_LOG_LEVEL` | `INFO` | Logging level |
| `EDR_RELOAD` | `false` | Auto-reload on changes |

### Volume Mounts
- **Data Volume**: `./data:/app/data` - Persistent Zarr storage
- **Input Data**: `./sig_wwave_swell-20240623.nc:/app/input/` - Source NetCDF

### Port Mapping
- **API**: `8080:8000` - Direct API access (mapped to avoid conflicts)
- **Nginx**: `8090:80, 8443:443` - Production HTTP/HTTPS (mapped to avoid conflicts)
- **Redis**: `6380:6379` - Cache service (mapped to avoid conflicts)

## 📊 **Monitoring & Health**

### Health Checks
```bash
# Container health status
docker-compose ps

# API health endpoint
curl http://localhost:8080/

# Detailed status
make status
```

### Log Management
```bash
# View all logs
make logs

# Follow specific service
docker-compose logs -f edr-api

# View converter logs
docker-compose logs edr-converter
```

## 🛠️ **Maintenance Commands**

### Makefile Shortcuts
```bash
make help          # Show all available commands
make build          # Build Docker images
make up            # Start services (with data conversion)
make down          # Stop all services
make restart       # Restart services
make clean         # Clean up containers and volumes
make shell         # Access container shell
```

### Manual Docker Commands
```bash
# Build image
docker-compose build edr-api

# Start with specific profile
docker-compose --profile production up -d

# View container status
docker-compose ps

# Scale API instances
docker-compose up -d --scale edr-api=3
```

## 🔐 **Security Considerations**

### Container Security
- ✅ **Non-root user**: App runs as dedicated `edr` user
- ✅ **Read-only mounts**: Source data mounted read-only
- ✅ **Network isolation**: Services in dedicated bridge network
- ✅ **Resource limits**: CPU/memory constraints (configurable)

### Production Hardening
```bash
# Enable security headers and rate limiting
make prod-up

# Use HTTPS in production
# Add SSL certificates to ./docker/ssl/
```

## 🧪 **Testing & Validation**

### Automated Testing
```bash
# Run full test suite
make test

# Test specific endpoints
curl -s http://localhost:8080/collections | jq '.collections[0].id'
curl "http://localhost:8080/collections/wave_data/position?coords=-60.0,45.0"
```

### Performance Testing
```bash
# Load test with Apache Bench
ab -n 1000 -c 10 http://localhost:8080/

# Monitor resource usage
docker stats edr-publisher-api
```

## 🚀 **Scaling & Production**

### Horizontal Scaling
```bash
# Scale API instances
docker-compose up -d --scale edr-api=3

# Load balancing via Nginx
# Configure upstream in nginx.conf
```

### Cloud Deployment
```bash
# Deploy to Docker Swarm
docker stack deploy -c docker-compose.yml edr-stack

# Deploy to Kubernetes
# Convert compose file with Kompose
kompose convert -f docker-compose.yml
```

### Data Management
```bash
# Backup Zarr data
docker run --rm -v edr_data:/data -v $(pwd):/backup alpine tar czf /backup/zarr-backup.tar.gz -C /data .

# Restore Zarr data
docker run --rm -v edr_data:/data -v $(pwd):/backup alpine tar xzf /backup/zarr-backup.tar.gz -C /data
```

## 🎯 **Benefits Achieved**

✅ **Environment Consistency**: Identical runtime across dev/test/prod
✅ **Easy Deployment**: Single command deployment
✅ **Scalability**: Ready for orchestration and load balancing  
✅ **Data Persistence**: Zarr data survives container restarts
✅ **Security**: Non-root execution and network isolation
✅ **Monitoring**: Built-in health checks and logging
✅ **Production Ready**: Nginx proxy, caching, and rate limiting

## 📈 **Next Steps**

1. **CI/CD Integration**: Add GitHub Actions for automated builds
2. **Kubernetes Manifests**: Create K8s deployment files
3. **Monitoring Stack**: Add Prometheus/Grafana
4. **SSL/TLS**: Configure HTTPS with Let's Encrypt
5. **Database**: Add PostgreSQL for metadata storage

