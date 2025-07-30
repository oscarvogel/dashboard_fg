// src/services/api.js
import axios from 'axios'

// Determina la URL base de la API según el entorno
const API_BASE_URL = import.meta.env.PROD
  ? 'http://66.97.47.156:8088/' // URL de producción
  : 'http://localhost:8000/'; // URL de desarrollo

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor: agrega el token en cada petición
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Manejo de token expirado (opcional)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Aquí podrías renovar el token con el refresh
      // Por ahora, redirigimos al login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('empleado')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default api