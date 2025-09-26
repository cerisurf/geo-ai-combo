#!/bin/bash

# GeoServer initialization script for EDR Publisher
# This script runs when the GeoServer container starts

echo "Starting GeoServer initialization for EDR Publisher..."

# Wait for GeoServer to be fully started
echo "Waiting for GeoServer to start..."
while ! curl -s -f http://localhost:8080/geoserver/rest/about/version.xml > /dev/null 2>&1; do
    echo "Waiting for GeoServer..."
    sleep 5
done

echo "GeoServer is ready, configuring workspace and data stores..."

# Create workspace if it doesn't exist
curl -u admin:geoserver123 -X POST \
    -H "Content-Type: application/xml" \
    -d '<workspace><name>edr_data</name></workspace>' \
    http://localhost:8080/geoserver/rest/workspaces 2>/dev/null || echo "Workspace may already exist"

# Create shapefile datastore
curl -u admin:geoserver123 -X POST \
    -H "Content-Type: application/xml" \
    -d '<dataStore>
        <name>shapefiles</name>
        <description>European coastline shapefiles</description>
        <enabled>true</enabled>
        <workspace>edr_data</workspace>
        <connectionParameters>
            <entry key="url">file:/opt/geoserver_data/shapefiles</entry>
            <entry key="create spatial index">true</entry>
            <entry key="charset">UTF-8</entry>
            <entry key="memory mapped buffer">true</entry>
            <entry key="enable spatial index">true</entry>
        </connectionParameters>
    </dataStore>' \
    http://localhost:8080/geoserver/rest/workspaces/edr_data/datastores 2>/dev/null || echo "Datastore may already exist"

# Auto-configure feature types for both coastline shapefiles
echo "Auto-configuring coastline layers..."

# Europe coastline (lines)
curl -u admin:geoserver123 -X POST \
    -H "Content-Type: application/xml" \
    -d '<featureType>
        <name>Europe_coastline</name>
        <title>European Coastline</title>
        <abstract>European coastline as line features</abstract>
        <enabled>true</enabled>
        <srs>EPSG:4326</srs>
        <projectionPolicy>REPROJECT_TO_DECLARED</projectionPolicy>
    </featureType>' \
    http://localhost:8080/geoserver/rest/workspaces/edr_data/datastores/shapefiles/featuretypes 2>/dev/null || echo "Europe_coastline layer may already exist"

# Europe coastline polygons
curl -u admin:geoserver123 -X POST \
    -H "Content-Type: application/xml" \
    -d '<featureType>
        <name>Europe_coastline_poly</name>
        <title>European Coastline Polygons</title>
        <abstract>European coastline as polygon features</abstract>
        <enabled>true</enabled>
        <srs>EPSG:4326</srs>
        <projectionPolicy>REPROJECT_TO_DECLARED</projectionPolicy>
    </featureType>' \
    http://localhost:8080/geoserver/rest/workspaces/edr_data/datastores/shapefiles/featuretypes 2>/dev/null || echo "Europe_coastline_poly layer may already exist"

echo "GeoServer configuration completed!"
echo "Available WMS layers:"
echo "  - edr_data:Europe_coastline (line features)"
echo "  - edr_data:Europe_coastline_poly (polygon features)"
echo ""
echo "WMS GetCapabilities URL: http://localhost:8081/geoserver/edr_data/wms?service=WMS&version=1.3.0&request=GetCapabilities"
