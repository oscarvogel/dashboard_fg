<!-- LoginView.vue -->
<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const dni = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()

const login = async () => {
  // Limpiar error anterior
  error.value = ''
  loading.value = true

  try {
    const response = await api.post('/api/login-empleado/', {
      dni: dni.value,
      password: password.value
    })

    // Si llega aquí, login exitoso
    const { access, refresh, operador } = response.data

    // Guardar en localStorage
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    localStorage.setItem('empleado', JSON.stringify(operador))

    // Redirigir al dashboard
    router.push('/dashboard')

  } catch (err) {
    // ✅ Manejo de errores
    if (err.response) {
      // El servidor respondió con error (401, etc.)
      if (err.response.data?.error) {
        error.value = err.response.data.error
      } else {
        error.value = 'Credenciales inválidas'
      }
    } else {
      // Error de red o sin conexión
      error.value = 'Error de conexión con el servidor'
    }
    // ✅ No redirigir: se queda en el login
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <form @submit.prevent="login" class="login-form">
      <h2>Inicio de Sesión</h2>

      <div class="form-group">
        <label>DNI</label>
        <input v-model="dni" type="text" placeholder="12345678" required />
      </div>

      <div class="form-group">
        <label>Contraseña</label>
        <input v-model="password" type="password" placeholder="Contraseña" required />
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? 'Ingresando...' : 'Ingresar' }}
      </button>

      <!-- ✅ Mensaje de error visible -->
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.login-form {
  background: white;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 350px;
  text-align: center;
}

.form-group {
  text-align: left;
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #555;
}

.form-group input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

button:hover {
  background-color: #0c7cd5;
}

button:disabled {
  background-color: #90d0ff;
  cursor: not-allowed;
}

.error {
  color: #f5222d;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}
</style>