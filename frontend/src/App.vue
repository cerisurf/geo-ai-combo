<template>
  <div id="app">
    <!-- Navigation Header -->
    <nav class="navbar">
      <div class="nav-container">
        <div class="nav-brand">
          <h1>🌊 EDR Publisher</h1>
          <span class="nav-subtitle">Marine Data Explorer</span>
        </div>
        
        <div class="nav-links">
          <router-link to="/" class="nav-link" :class="{ active: $route.name === 'Map' }">
            🗺️ Map View
          </router-link>
          <router-link to="/data" class="nav-link" :class="{ active: $route.name === 'Data' }">
            📊 Data Explorer
          </router-link>
          <router-link to="/about" class="nav-link" :class="{ active: $route.name === 'About' }">
            ℹ️ About
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <p>&copy; 2024 EDR Publisher. Built with Vue.js, Leaflet, and GeoServer.</p>
        <div class="footer-links">
          <a href="http://localhost:8080/api" target="_blank">EDR API Docs</a>
          <a href="http://localhost:8081/geoserver" target="_blank">GeoServer Admin</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style scoped>
.navbar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1rem 0;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.nav-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
  margin-left: 0.5rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.nav-link:hover {
  background-color: rgba(255,255,255,0.1);
  transform: translateY(-1px);
}

.nav-link.active {
  background-color: rgba(255,255,255,0.2);
  font-weight: 600;
}

.main-content {
  min-height: calc(100vh - 140px);
  padding: 0;
}

.footer {
  background: #2c3e50;
  color: white;
  padding: 1rem 0;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.footer-links {
  display: flex;
  gap: 1rem;
}

.footer-links a {
  color: #ecf0f1;
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: #3498db;
}

@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    gap: 1rem;
  }
  
  .nav-links {
    justify-content: center;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>
