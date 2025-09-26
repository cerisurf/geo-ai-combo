import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Import Leaflet CSS
import 'leaflet/dist/leaflet.css'

// Import views
import MapView from './views/MapView.vue'
import DataExplorer from './views/DataExplorer.vue'
import About from './views/About.vue'

// Router configuration
const routes = [
  { path: '/', name: 'Map', component: MapView },
  { path: '/data', name: 'Data', component: DataExplorer },
  { path: '/about', name: 'About', component: About }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Create app
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')
