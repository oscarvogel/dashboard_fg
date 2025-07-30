// src/composables/useAuth.js
import api from '../services/api'

const login = async (dni, password) => {
  try {
    const response = await api.post('/api/login-empleado/', { dni, password })
    const { access, refresh, operador } = response.data

    // Guardar en localStorage
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('empleado', JSON.stringify(operador))

    // Configurar axios para futuras llamadas
    api.defaults.headers.common['Authorization'] = `Bearer ${access}`

    return { success: true, user: operador }
  } catch (error) {
    return { success: false, error: 'Credenciales inválidas' }
  }
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('empleado')
  delete api.defaults.headers.common['Authorization']
}

const isAuthenticated = () => {
  return !!localStorage.getItem('access_token')
}

export { login, logout, isAuthenticated }