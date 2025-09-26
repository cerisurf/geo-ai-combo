import axios from 'axios'

class EDRService {
  constructor() {
    this.baseURL = '/api'
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }

  /**
   * Get EDR collections
   */
  async getCollections() {
    try {
      const response = await this.client.get('/collections')
      return response.data
    } catch (error) {
      console.error('Failed to fetch collections:', error)
      throw new Error('Failed to fetch collections')
    }
  }

  /**
   * Get specific collection metadata
   */
  async getCollection(collectionId) {
    try {
      const response = await this.client.get(`/collections/${collectionId}`)
      return response.data
    } catch (error) {
      console.error(`Failed to fetch collection ${collectionId}:`, error)
      throw new Error(`Failed to fetch collection ${collectionId}`)
    }
  }

  /**
   * Query position data from EDR API
   * @param {string} collectionId - Collection identifier (e.g., 'wave_data')
   * @param {string} coords - Coordinates in format "lng,lat"
   * @param {Object} options - Additional query options
   */
  async getPositionData(collectionId, coords, options = {}) {
    try {
      const params = new URLSearchParams({
        coords: coords,
        f: 'GeoJSON',
        ...options
      })

      const response = await this.client.get(
        `/collections/${collectionId}/position?${params.toString()}`
      )
      return response.data
    } catch (error) {
      console.error('EDR position query failed:', error)
      if (error.response?.status === 404) {
        throw new Error('No data found at this location')
      } else if (error.response?.status === 400) {
        throw new Error('Invalid coordinates or query parameters')
      }
      throw new Error('Failed to query position data')
    }
  }

  /**
   * Query area data from EDR API
   * @param {string} collectionId - Collection identifier
   * @param {string} coords - Area coordinates (bbox or polygon)
   * @param {Object} options - Additional query options
   */
  async getAreaData(collectionId, coords, options = {}) {
    try {
      const params = new URLSearchParams({
        coords: coords,
        f: 'GeoJSON',
        ...options
      })

      const response = await this.client.get(
        `/collections/${collectionId}/area?${params.toString()}`
      )
      return response.data
    } catch (error) {
      console.error('EDR area query failed:', error)
      throw new Error('Failed to query area data')
    }
  }

  /**
   * Query trajectory data from EDR API
   * @param {string} collectionId - Collection identifier
   * @param {string} coords - Trajectory coordinates
   * @param {Object} options - Additional query options
   */
  async getTrajectoryData(collectionId, coords, options = {}) {
    try {
      const params = new URLSearchParams({
        coords: coords,
        f: 'GeoJSON',
        ...options
      })

      const response = await this.client.get(
        `/collections/${collectionId}/trajectory?${params.toString()}`
      )
      return response.data
    } catch (error) {
      console.error('EDR trajectory query failed:', error)
      throw new Error('Failed to query trajectory data')
    }
  }

  /**
   * Get available instances (time dimension values)
   * @param {string} collectionId - Collection identifier
   */
  async getInstances(collectionId) {
    try {
      const response = await this.client.get(`/collections/${collectionId}/instances`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch instances:', error)
      throw new Error('Failed to fetch time instances')
    }
  }

  /**
   * Format coordinates for EDR API
   * @param {number} lng - Longitude
   * @param {number} lat - Latitude
   * @returns {string} - Formatted coordinates
   */
  formatCoords(lng, lat) {
    return `${lng.toFixed(6)},${lat.toFixed(6)}`
  }

  /**
   * Format bounding box for area queries
   * @param {Object} bounds - Leaflet bounds object
   * @returns {string} - Formatted bbox
   */
  formatBbox(bounds) {
    const sw = bounds.getSouthWest()
    const ne = bounds.getNorthEast()
    return `${sw.lng.toFixed(6)},${sw.lat.toFixed(6)},${ne.lng.toFixed(6)},${ne.lat.toFixed(6)}`
  }
}

export const edrService = new EDRService()
export default edrService
