<template>
  <div class="map-view">
    <!-- Control Panel -->
    <div class="control-panel">
      <div class="panel-section">
        <h3>🗺️ Map Layers</h3>
        <div class="layer-controls">
          <label class="layer-control">
            <input 
              type="checkbox" 
              v-model="layers.coastline.visible"
              @change="toggleLayer('coastline')"
            />
            <span>European Coastline</span>
          </label>
          <label class="layer-control">
            <input 
              type="checkbox" 
              v-model="layers.coastlinePoly.visible"
              @change="toggleLayer('coastlinePoly')"
            />
            <span>Coastline Polygons</span>
          </label>
          <label class="layer-control">
            <input 
              type="checkbox" 
              v-model="layers.waveHeight.visible"
              @change="toggleLayer('waveHeight')"
            />
            <span>Wave Height (Sep 25)</span>
          </label>
        </div>
      </div>

      <div class="panel-section">
        <h3>📍 EDR Query</h3>
        <div class="query-controls">
          <p class="instruction">Click on the map to query wave data at that location</p>
          <div v-if="selectedPoint" class="selected-point">
            <strong>Selected Point:</strong><br>
            Lat: {{ selectedPoint.lat.toFixed(4) }}<br>
            Lng: {{ selectedPoint.lng.toFixed(4) }}
            <button @click="queryEDR" class="query-btn" :disabled="isQuerying">
              {{ isQuerying ? 'Querying...' : 'Get Wave Data' }}
            </button>
          </div>
        </div>
      </div>

      <div class="panel-section" v-if="edrData">
        <h3>📊 Wave Data</h3>
        <div class="data-display">
          <p><strong>Features found:</strong> {{ edrData.features?.length || 0 }}</p>
          <div v-if="edrData.features?.length" class="feature-preview">
            <p><strong>Sample Data Point:</strong></p>
            <pre>{{ JSON.stringify(edrData.features[0].properties, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Map Container -->
    <div class="map-container">
      <div id="map" ref="mapContainer"></div>
    </div>
  </div>
</template>

<script>
import L from 'leaflet'
import { edrService } from '@/services/edrService'

export default {
  name: 'MapView',
  data() {
    return {
      map: null,
      wmsLayers: {},
      selectedPoint: null,
      selectedMarker: null,
      edrData: null,
      isQuerying: false,
      layers: {
        coastline: {
          visible: true,
          layer: null,
          url: '/geoserver/edr_data/wms',
          options: {
            layers: 'edr_data:Europe_coastline',
            format: 'image/png',
            transparent: true,
            styles: '',
            version: '1.3.0'
          }
        },
        coastlinePoly: {
          visible: false,
          layer: null,
          url: '/geoserver/edr_data/wms',
          options: {
            layers: 'edr_data:Europe_coastline_poly',
            format: 'image/png',
            transparent: true,
            styles: '',
            version: '1.3.0'
          }
        },
        waveHeight: {
          visible: true,
          layer: null,
          url: '/geoserver/wave_data/wms',
          options: {
            layers: 'wave_data:wave_height_2025_09_25',
            format: 'image/png',
            transparent: true,
            styles: '',
            version: '1.3.0',
            opacity: 0.7
          }
        }
      }
    }
  },
  mounted() {
    this.initMap()
    this.setupMapLayers()
    this.addLayerControl()
  },
  methods: {
    initMap() {
      // Initialize map centered on Europe
      this.map = L.map(this.$refs.mapContainer, {
        center: [55.0, 10.0],
        zoom: 4,
        zoomControl: true
      })

      // Add base tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
      }).addTo(this.map)

      // Add click event for EDR queries
      this.map.on('click', this.onMapClick)
    },

    setupMapLayers() {
      // Initialize WMS layers
      Object.keys(this.layers).forEach(layerKey => {
        const layerConfig = this.layers[layerKey]
        layerConfig.layer = L.tileLayer.wms(layerConfig.url, layerConfig.options)
        
        if (layerConfig.visible) {
          layerConfig.layer.addTo(this.map)
        }
      })
    },

    toggleLayer(layerKey) {
      const layerConfig = this.layers[layerKey]
      
      if (layerConfig.visible) {
        layerConfig.layer.addTo(this.map)
      } else {
        this.map.removeLayer(layerConfig.layer)
      }
    },

    onMapClick(e) {
      this.selectedPoint = {
        lat: e.latlng.lat,
        lng: e.latlng.lng
      }

      // Remove previous marker
      if (this.selectedMarker) {
        this.map.removeLayer(this.selectedMarker)
      }

      // Add new marker
      this.selectedMarker = L.marker([e.latlng.lat, e.latlng.lng], {
        icon: L.divIcon({
          className: 'selected-point-marker',
          html: '<div style="background: #e74c3c; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>',
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        })
      }).addTo(this.map)

      // Clear previous data
      this.edrData = null
    },
    
    addLayerControl() {
      // Create layer control for toggling layers
      const baseLayers = {}
      const overlayLayers = {
        'Europe Coastline': this.layers.coastline.layer,
        'Europe Coastline (Filled)': this.layers.coastlinePoly.layer,
        'Wave Height (Sep 25)': this.layers.waveHeight.layer
      }
      
      // Add layer control to map
      L.control.layers(baseLayers, overlayLayers, {
        position: 'topright',
        collapsed: false
      }).addTo(this.map)
    },

    async queryEDR() {
      if (!this.selectedPoint) return

      this.isQuerying = true
      try {
        const coords = `${this.selectedPoint.lng},${this.selectedPoint.lat}`
        this.edrData = await edrService.getPositionData('wave_data', coords)
        
        // Add popup to marker with data summary
        if (this.selectedMarker && this.edrData.features?.length) {
          this.selectedMarker.bindPopup(`
            <div>
              <strong>Wave Data Point</strong><br>
              Features: ${this.edrData.features.length}<br>
              <small>Click "Get Wave Data" in panel for details</small>
            </div>
          `).openPopup()
        }
      } catch (error) {
        console.error('EDR query failed:', error)
        alert('Failed to query wave data. Please try again.')
      } finally {
        this.isQuerying = false
      }
    }
  }
}
</script>

<style scoped>
.map-view {
  display: flex;
  height: calc(100vh - 140px);
  background: #f8f9fa;
}

.control-panel {
  width: 320px;
  background: white;
  border-right: 1px solid #e9ecef;
  overflow-y: auto;
  box-shadow: 2px 0 10px rgba(0,0,0,0.1);
}

.panel-section {
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.panel-section h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.layer-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.layer-control {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.layer-control input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.query-controls .instruction {
  color: #666;
  font-size: 0.875rem;
  margin-bottom: 1rem;
  line-height: 1.4;
}

.selected-point {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  font-size: 0.875rem;
}

.query-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.75rem;
  font-size: 0.875rem;
  transition: background-color 0.3s ease;
}

.query-btn:hover:not(:disabled) {
  background: #0056b3;
}

.query-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.data-display {
  font-size: 0.875rem;
}

.feature-preview {
  margin-top: 1rem;
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #dee2e6;
}

.feature-preview pre {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #495057;
  overflow-x: auto;
  max-height: 150px;
}

.map-container {
  flex: 1;
  position: relative;
}

#map {
  width: 100%;
  height: 100%;
}

/* Custom marker styles */
:deep(.selected-point-marker) {
  background: transparent !important;
  border: none !important;
}
</style>
