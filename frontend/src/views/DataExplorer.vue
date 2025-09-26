<template>
  <div class="data-explorer">
    <div class="explorer-header">
      <h2>📊 Data Explorer</h2>
      <p>Explore EDR collections and visualize time series data</p>
    </div>

    <div class="explorer-content">
      <!-- Collections List -->
      <div class="section">
        <h3>📚 Available Collections</h3>
        <div v-if="loading.collections" class="loading">Loading collections...</div>
        <div v-else-if="collections.length" class="collections-grid">
          <div 
            v-for="collection in collections" 
            :key="collection.id"
            class="collection-card"
            :class="{ active: selectedCollection?.id === collection.id }"
            @click="selectCollection(collection)"
          >
            <h4>{{ collection.id }}</h4>
            <p>{{ collection.title || 'No title available' }}</p>
            <div class="collection-meta">
              <span class="meta-item">
                📅 {{ formatDateRange(collection.extent?.temporal) }}
              </span>
              <span class="meta-item">
                🌍 {{ formatSpatialExtent(collection.extent?.spatial) }}
              </span>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          No collections found. Make sure the EDR API is running.
        </div>
      </div>

      <!-- Selected Collection Details -->
      <div v-if="selectedCollection" class="section">
        <h3>🔍 Collection Details: {{ selectedCollection.id }}</h3>
        <div class="collection-details">
          <div class="detail-group">
            <strong>Title:</strong> {{ selectedCollection.title || 'N/A' }}
          </div>
          <div class="detail-group">
            <strong>Description:</strong> {{ selectedCollection.description || 'N/A' }}
          </div>
          <div class="detail-group">
            <strong>Data Queries:</strong>
            <div class="query-types">
              <span v-for="query in selectedCollection.data_queries" :key="query" class="query-tag">
                {{ query }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Query Section -->
      <div v-if="selectedCollection" class="section">
        <h3>⚡ Quick Data Query</h3>
        <div class="quick-query">
          <div class="query-form">
            <div class="form-group">
              <label>Coordinates (lng, lat):</label>
              <input 
                v-model="queryCoords" 
                type="text" 
                placeholder="-60.0, 45.0"
                class="form-input"
              />
            </div>
            <button 
              @click="performQuickQuery" 
              :disabled="!queryCoords || loading.query"
              class="query-button"
            >
              {{ loading.query ? 'Querying...' : 'Query Data' }}
            </button>
          </div>
          
          <div v-if="queryResult" class="query-results">
            <h4>📈 Query Results</h4>
            <div class="result-summary">
              <span class="result-stat">
                Features: {{ queryResult.features?.length || 0 }}
              </span>
              <span class="result-stat">
                Type: {{ queryResult.type }}
              </span>
            </div>
            
            <!-- Time Series Chart -->
            <div v-if="chartData" class="chart-container">
              <canvas ref="chartCanvas"></canvas>
            </div>
            
            <!-- Raw Data Preview -->
            <details class="raw-data">
              <summary>View Raw Data</summary>
              <pre>{{ JSON.stringify(queryResult, null, 2) }}</pre>
            </details>
          </div>
        </div>
      </div>

      <!-- API Information -->
      <div class="section">
        <h3>🔗 API Information</h3>
        <div class="api-info">
          <div class="api-links">
            <a href="/api/collections" target="_blank" class="api-link">
              📋 Collections Endpoint
            </a>
            <a href="/api/api" target="_blank" class="api-link">
              📖 API Documentation
            </a>
            <a href="/geoserver/edr_data/wms?service=WMS&request=GetCapabilities" target="_blank" class="api-link">
              🗺️ WMS Capabilities
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { edrService } from '@/services/edrService'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'DataExplorer',
  data() {
    return {
      collections: [],
      selectedCollection: null,
      queryCoords: '-60.0,45.0',
      queryResult: null,
      chartData: null,
      chart: null,
      loading: {
        collections: true,
        query: false
      }
    }
  },
  async mounted() {
    await this.loadCollections()
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy()
    }
  },
  methods: {
    async loadCollections() {
      try {
        this.loading.collections = true
        const data = await edrService.getCollections()
        this.collections = data.collections || []
        
        // Auto-select first collection if available
        if (this.collections.length > 0) {
          this.selectCollection(this.collections[0])
        }
      } catch (error) {
        console.error('Failed to load collections:', error)
        this.collections = []
      } finally {
        this.loading.collections = false
      }
    },

    selectCollection(collection) {
      this.selectedCollection = collection
      this.queryResult = null
      this.chartData = null
      if (this.chart) {
        this.chart.destroy()
        this.chart = null
      }
    },

    async performQuickQuery() {
      if (!this.selectedCollection || !this.queryCoords) return

      try {
        this.loading.query = true
        const coords = this.queryCoords.trim()
        
        this.queryResult = await edrService.getPositionData(
          this.selectedCollection.id, 
          coords
        )
        
        this.prepareChartData()
      } catch (error) {
        console.error('Query failed:', error)
        alert(`Query failed: ${error.message}`)
        this.queryResult = null
        this.chartData = null
      } finally {
        this.loading.query = false
      }
    },

    prepareChartData() {
      if (!this.queryResult?.features?.length) return

        // Extract time series data from features
        const features = this.queryResult.features
        const timeValues = []
        const dataValues = []

        features.forEach(feature => {
          if (feature.properties?.datetime && feature.properties?.htsgwsfc !== undefined) {
            timeValues.push(new Date(feature.properties.datetime))
            dataValues.push(feature.properties.htsgwsfc)
          }
        })

        if (timeValues.length > 0) {
          // Format time labels for display
          const timeLabels = timeValues.map(date => date.toLocaleDateString() + ' ' + date.toLocaleTimeString())
          
          this.chartData = {
            labels: timeLabels,
            datasets: [{
              label: 'Wave Height (m)',
              data: dataValues,
              borderColor: 'rgb(75, 192, 192)',
              backgroundColor: 'rgba(75, 192, 192, 0.2)',
              tension: 0.1
            }]
          }

        this.$nextTick(() => {
          this.createChart()
        })
      }
    },

    createChart() {
      if (!this.chartData || !this.$refs.chartCanvas) return

      const ctx = this.$refs.chartCanvas.getContext('2d')
      
      if (this.chart) {
        this.chart.destroy()
      }

      this.chart = new Chart(ctx, {
        type: 'line',
        data: this.chartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Time'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Wave Height (m)'
              }
            }
          },
          plugins: {
            title: {
              display: true,
              text: 'Time Series Data'
            },
            legend: {
              display: true
            }
          }
        }
      })
    },

    formatDateRange(temporal) {
      if (!temporal?.interval?.length) return 'Unknown'
      const interval = temporal.interval[0]
      const start = new Date(interval[0]).toLocaleDateString()
      const end = new Date(interval[1]).toLocaleDateString()
      return `${start} - ${end}`
    },

    formatSpatialExtent(spatial) {
      if (!spatial?.bbox?.length) return 'Unknown'
      const bbox = spatial.bbox[0]
      return `${bbox[0].toFixed(1)}, ${bbox[1].toFixed(1)} to ${bbox[2].toFixed(1)}, ${bbox[3].toFixed(1)}`
    }
  }
}
</script>

<style scoped>
.data-explorer {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.explorer-header {
  text-align: center;
  margin-bottom: 2rem;
}

.explorer-header h2 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.explorer-header p {
  color: #666;
  font-size: 1.1rem;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.section h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.2rem;
}

.collections-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.collection-card {
  border: 2px solid #e9ecef;
  border-radius: 6px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.collection-card:hover {
  border-color: #007bff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,123,255,0.15);
}

.collection-card.active {
  border-color: #007bff;
  background-color: #f8f9fa;
}

.collection-card h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.collection-card p {
  margin: 0 0 1rem 0;
  color: #666;
  font-size: 0.9rem;
}

.collection-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-item {
  font-size: 0.8rem;
  color: #666;
}

.collection-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.query-types {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.query-tag {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #495057;
}

.quick-query {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.query-form {
  display: flex;
  gap: 1rem;
  align-items: end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.form-input {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
}

.query-button {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  white-space: nowrap;
}

.query-button:hover:not(:disabled) {
  background: #0056b3;
}

.query-button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.query-results {
  border-top: 1px solid #e9ecef;
  padding-top: 1.5rem;
}

.result-summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.result-stat {
  background: #e9ecef;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.chart-container {
  height: 300px;
  margin: 1.5rem 0;
  position: relative;
}

.raw-data {
  margin-top: 1rem;
}

.raw-data summary {
  cursor: pointer;
  color: #007bff;
  font-weight: 500;
}

.raw-data pre {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.8rem;
  max-height: 300px;
  margin-top: 0.5rem;
}

.api-links {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.api-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  color: #495057;
  text-decoration: none;
  border-radius: 6px;
  border: 1px solid #dee2e6;
  transition: all 0.3s ease;
}

.api-link:hover {
  background: #e9ecef;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
  background: #f8f9fa;
  border-radius: 6px;
}
</style>
