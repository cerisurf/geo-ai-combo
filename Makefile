# EDR Publisher - Docker Management
.PHONY: help build up down logs shell test clean convert download-europe download-global reload-data list-datasets

# Default target
help:
	@echo "EDR Publisher Docker Management"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  build       - Build the Docker image"
	@echo "  up          - Start the EDR API service"
	@echo "  down        - Stop all services"
	@echo "  logs        - Show service logs"
	@echo "  shell       - Open shell in running container"
	@echo "  test        - Run API tests"
	@echo "  clean       - Clean up containers and volumes"
	@echo ""
	@echo "Data pipeline:"
	@echo "  download-europe  - Download European wave data"
	@echo "  download-global  - Download global wave data"
	@echo "  reload-data      - Reload latest dataset in API"
	@echo "  list-datasets    - List available datasets"
	@echo ""
	@echo "Production targets:"
	@echo "  prod-up     - Start with production profile (nginx + caching)"
	@echo "  cache-up    - Start with caching enabled"

# Development commands
build:
	docker-compose build edr-api

up:
	@echo "Starting EDR API service..."
	docker-compose up -d edr-api
	@echo "EDR API started. Use 'make status' to check health."

down:
	docker-compose down

logs:
	docker-compose logs -f edr-api

shell:
	docker-compose exec edr-api /bin/bash

# Data management (new pipeline)
convert-data:
	@echo "Use the new data pipeline instead:"
	@echo "  bash scripts/update_gfs_wave.sh --region europe"
	@echo "  or bash scripts/update_gfs_wave.sh --region global"

# Legacy conversion (deprecated)
convert:
	@echo "⚠️  Legacy convert target - use 'make convert-data' for new pipeline"
	@echo "Starting API without conversion (datasets auto-discovered)"

# Testing
test: up
	@echo "Waiting for API to be ready..."
	@sleep 10
	@echo "Running API tests..."
	@curl -f http://localhost:8080/ > /dev/null 2>&1 && echo "✅ API is responding" || echo "❌ API not ready"
	@curl -s http://localhost:8080/collections | jq '.collections[0].id' || echo "❌ Collections endpoint failed"

# Production deployment
prod-up:
	docker-compose --profile production up -d

cache-up:
	docker-compose --profile cache --profile production up -d

geoserver-up:
	docker-compose --profile geoserver up -d

geo-up:
	docker-compose --profile geoserver up -d edr-api geoserver

frontend-up:
	docker-compose --profile frontend up -d

web-up:
	docker-compose --profile frontend --profile geoserver up -d edr-api frontend geoserver

full-up:
	docker-compose --profile cache --profile geoserver --profile frontend --profile production up -d

# Cleanup
clean:
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Development helpers
dev-build:
	docker-compose build --no-cache edr-api

dev-up: dev-build
	docker-compose up edr-api

restart: down up

# Data pipeline targets (containerized)
download-europe:
	@echo "Starting data pipeline container..."
	@docker-compose --profile pipeline up -d data-pipeline
	@echo "Downloading European wave data inside container..."
	@docker-compose exec data-pipeline bash scripts/update_gfs_wave.sh --region europe --hours 72
	@echo "Reloading EDR API..."
	@$(MAKE) reload-data
	@echo "✅ European data pipeline completed!"

download-global:
	@echo "Starting data pipeline container..."
	@docker-compose --profile pipeline up -d data-pipeline
	@echo "Downloading global wave data inside container..."
	@docker-compose exec data-pipeline bash scripts/update_gfs_wave.sh --region global --hours 120
	@echo "Reloading EDR API..."
	@$(MAKE) reload-data
	@echo "✅ Global data pipeline completed!"

reload-data:
	@echo "Reloading latest dataset in EDR API..."
	@curl -X POST http://localhost:8080/admin/reload 2>/dev/null | jq '.' || echo "❌ API not running or reload failed"

reload-geoserver:
	@echo "Reloading GeoServer configuration..."
	@curl -X POST -u admin:geoserver123 "http://localhost:8081/geoserver/rest/reload" || echo "❌ GeoServer not running"

list-datasets:
	@echo "Available datasets:"
	@curl http://localhost:8080/admin/datasets 2>/dev/null | jq '.datasets[] | {id, title, modified}' || echo "❌ API not running"

pipeline-shell:
	@echo "Opening shell in data pipeline container..."
	@docker-compose --profile pipeline up -d data-pipeline
	@docker-compose exec data-pipeline bash

stop-pipeline:
	@echo "Stopping data pipeline container..."
	@docker-compose stop data-pipeline || echo "Pipeline not running"

# Status check
status:
	docker-compose ps
	@echo ""
	@echo "Container health:"
	@docker-compose exec edr-api curl -f http://localhost:8000/ > /dev/null 2>&1 && echo "✅ EDR API: Healthy" || echo "❌ EDR API: Unhealthy"
	@curl -f http://localhost:8081/geoserver/web/ > /dev/null 2>&1 && echo "✅ GeoServer: Healthy" || echo "❌ GeoServer: Not running"
	@echo ""
	@echo "Access URLs:"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - API: http://localhost:8080"
	@echo "  - API Docs: http://localhost:8080/api"
	@echo "  - GeoServer: http://localhost:8081/geoserver (admin/geoserver123)"
	@echo "  - Nginx (production): http://localhost:8090"

