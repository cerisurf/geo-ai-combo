<template>
  <div class="about">
    <div class="about-container">
      <div class="hero-section">
        <h1>🌊 EDR Publisher</h1>
        <p class="hero-subtitle">Marine Data Explorer & Visualization Platform</p>
      </div>

      <div class="content-section">
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">🗺️</div>
            <h3>Interactive Mapping</h3>
            <p>Visualize marine data layers with Leaflet-powered interactive maps. Browse European coastlines and overlay geospatial data.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>EDR API Integration</h3>
            <p>Query Environmental Data Retrieval (EDR) APIs for position-based, area-based, and trajectory-based data requests.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">🌊</div>
            <h3>Wave Data Analysis</h3>
            <p>Access and analyze significant wave height data with time series visualization and statistical analysis tools.</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">🛰️</div>
            <h3>OGC Services</h3>
            <p>Built-in support for OGC Web Map Service (WMS) and Web Feature Service (WFS) standards via GeoServer.</p>
          </div>
        </div>
      </div>

      <div class="info-section">
        <h2>🏗️ Architecture</h2>
        <div class="architecture-diagram">
          <div class="arch-component">
            <h4>Frontend (Vue.js)</h4>
            <ul>
              <li>Interactive Leaflet maps</li>
              <li>Real-time data visualization</li>
              <li>Responsive user interface</li>
            </ul>
          </div>
          <div class="arch-arrow">→</div>
          <div class="arch-component">
            <h4>EDR API (FastAPI)</h4>
            <ul>
              <li>OGC EDR standard compliance</li>
              <li>Zarr data format support</li>
              <li>High-performance queries</li>
            </ul>
          </div>
          <div class="arch-arrow">→</div>
          <div class="arch-component">
            <h4>GeoServer</h4>
            <ul>
              <li>WMS/WFS services</li>
              <li>Vector data publishing</li>
              <li>Spatial data styling</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="tech-section">
        <h2>🛠️ Technology Stack</h2>
        <div class="tech-categories">
          <div class="tech-category">
            <h4>Frontend</h4>
            <div class="tech-tags">
              <span class="tech-tag">Vue.js 3</span>
              <span class="tech-tag">Leaflet</span>
              <span class="tech-tag">Chart.js</span>
              <span class="tech-tag">Vite</span>
              <span class="tech-tag">Axios</span>
            </div>
          </div>
          
          <div class="tech-category">
            <h4>Backend</h4>
            <div class="tech-tags">
              <span class="tech-tag">FastAPI</span>
              <span class="tech-tag">Python</span>
              <span class="tech-tag">Zarr</span>
              <span class="tech-tag">Xarray</span>
              <span class="tech-tag">NumPy</span>
            </div>
          </div>
          
          <div class="tech-category">
            <h4>Geospatial</h4>
            <div class="tech-tags">
              <span class="tech-tag">GeoServer</span>
              <span class="tech-tag">PostGIS</span>
              <span class="tech-tag">GDAL</span>
              <span class="tech-tag">NetCDF</span>
              <span class="tech-tag">OGC Standards</span>
            </div>
          </div>
          
          <div class="tech-category">
            <h4>Infrastructure</h4>
            <div class="tech-tags">
              <span class="tech-tag">Docker</span>
              <span class="tech-tag">Docker Compose</span>
              <span class="tech-tag">Nginx</span>
              <span class="tech-tag">Redis</span>
            </div>
          </div>
        </div>
      </div>

      <div class="data-section">
        <h2>📚 Data Sources</h2>
        <div class="data-info">
          <div class="data-item">
            <h4>🌊 Wave Data</h4>
            <p>Significant wave height measurements from oceanographic models, stored in optimized Zarr format for fast time-series access.</p>
          </div>
          
          <div class="data-item">
            <h4>🏝️ Coastline Data</h4>
            <p>High-resolution European coastline vectors including both line and polygon representations for detailed geographic context.</p>
          </div>
          
          <div class="data-item">
            <h4>📊 Time Series</h4>
            <p>Multi-dimensional oceanographic data with temporal, spatial, and parametric dimensions for comprehensive analysis.</p>
          </div>
        </div>
      </div>

      <div class="api-section">
        <h2>🔗 API Endpoints</h2>
        <div class="endpoint-list">
          <div class="endpoint-item">
            <span class="method get">GET</span>
            <code>/collections</code>
            <span class="description">List all available data collections</span>
          </div>
          
          <div class="endpoint-item">
            <span class="method get">GET</span>
            <code>/collections/{id}/position</code>
            <span class="description">Query data at specific coordinates</span>
          </div>
          
          <div class="endpoint-item">
            <span class="method get">GET</span>
            <code>/collections/{id}/area</code>
            <span class="description">Query data within geographic area</span>
          </div>
          
          <div class="endpoint-item">
            <span class="method get">GET</span>
            <code>/geoserver/wms</code>
            <span class="description">Web Map Service for vector layers</span>
          </div>
        </div>
      </div>

      <div class="footer-section">
        <p>Built with ❤️ for marine data exploration and oceanographic research.</p>
        <div class="links">
          <a href="https://github.com/opengeospatial/ogcapi-environmental-data-retrieval" target="_blank">
            OGC EDR Specification
          </a>
          <a href="https://leafletjs.com/" target="_blank">
            Leaflet Documentation
          </a>
          <a href="https://vuejs.org/" target="_blank">
            Vue.js Guide
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'About'
}
</script>

<style scoped>
.about {
  min-height: calc(100vh - 140px);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem 0;
}

.about-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.hero-section {
  text-align: center;
  color: white;
  margin-bottom: 3rem;
}

.hero-section h1 {
  font-size: 3rem;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.hero-subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  margin: 0;
}

.content-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.feature-card {
  text-align: center;
  padding: 1.5rem;
  border-radius: 8px;
  background: #f8f9fa;
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.feature-card p {
  color: #666;
  line-height: 1.5;
  font-size: 0.9rem;
}

.info-section, .tech-section, .data-section, .api-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.info-section h2, .tech-section h2, .data-section h2, .api-section h2 {
  color: #2c3e50;
  margin-bottom: 1.5rem;
  text-align: center;
}

.architecture-diagram {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.arch-component {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border: 2px solid #e9ecef;
  min-width: 200px;
  text-align: center;
}

.arch-component h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.arch-component ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.arch-component li {
  color: #666;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.arch-arrow {
  font-size: 1.5rem;
  color: #007bff;
  font-weight: bold;
}

.tech-categories {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.tech-category h4 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tech-tag {
  background: #007bff;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.data-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.data-item {
  padding: 1rem;
  border-left: 4px solid #007bff;
  background: #f8f9fa;
  border-radius: 4px;
}

.data-item h4 {
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.data-item p {
  color: #666;
  line-height: 1.5;
  margin: 0;
  font-size: 0.9rem;
}

.endpoint-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.endpoint-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.method {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  min-width: 50px;
  text-align: center;
}

.method.get {
  background: #28a745;
  color: white;
}

.endpoint-item code {
  background: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 0.85rem;
  min-width: 250px;
}

.description {
  color: #666;
  font-size: 0.9rem;
}

.footer-section {
  background: rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  color: white;
}

.footer-section p {
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.links {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.links a:hover {
  background: rgba(255,255,255,0.1);
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .hero-section h1 {
    font-size: 2rem;
  }
  
  .architecture-diagram {
    flex-direction: column;
  }
  
  .arch-arrow {
    transform: rotate(90deg);
  }
  
  .endpoint-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .endpoint-item code {
    min-width: auto;
  }
}
</style>
