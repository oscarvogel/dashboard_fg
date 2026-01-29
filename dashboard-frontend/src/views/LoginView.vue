<!-- LoginView.vue -->
<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'

const dni = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()
const showPassword = ref(false)

const passwordFieldType = computed(() => (showPassword.value ? 'text' : 'password'))

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

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
  <div class="flex justify-center items-center min-h-screen bg-primary-50 font-sans">
    <div class="bg-white p-10 rounded-2xl shadow-lg w-full max-w-md animate-fade-in">
      <div class="text-center mb-8">
        <img src="../assets/logo_fg.png" alt="Forestal Gemini Logo" class="w-[120px] h-auto mb-6 mx-auto" />
        <h1 class="text-3xl font-semibold text-gray-800 mb-2">Bienvenido de Nuevo</h1>
        <p class="text-gray-500 mt-1">Inicia sesión para acceder al dashboard.</p>
      </div>
      <form @submit.prevent="login" class="flex flex-col space-y-5">
        <div class="flex flex-col">
          <label for="dni" class="block mb-2 font-semibold text-sm text-gray-700">DNI o Usuario</label>
          <input id="dni" v-model="dni" type="text" placeholder="Tu número de DNI o Usuario" required
            class="w-full p-3 border border-gray-300 rounded-lg text-base transition-all duration-200 ease-in-out focus:outline-none focus:border-primary-600 focus:ring-3 focus:ring-primary-600 focus:ring-opacity-20" />
        </div>

        <div class="flex flex-col">
          <label for="password" class="block mb-2 font-semibold text-sm text-gray-700">Contraseña</label>
          <div class="relative">
            <input id="password" v-model="password" :type="passwordFieldType" placeholder="••••••••" required
              class="w-full p-3 pr-12 border border-gray-300 rounded-lg text-base transition-all duration-200 ease-in-out focus:outline-none focus:border-primary-600 focus:ring-3 focus:ring-primary-600 focus:ring-opacity-20" />
            <button type="button" @click="togglePasswordVisibility"
              class="absolute inset-y-0 right-0 flex items-center px-4 bg-transparent border-none cursor-pointer text-gray-500 hover:text-gray-800"
              aria-label="Mostrar u ocultar contraseña">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M2.036 12.322a1.012 1.012 0 010-.639l4.443-7.082a1 1 0 011.585-.194l.24.316a1 1 0 001.585.194l4.443 7.082a1.012 1.012 0 010 .639l-4.443 7.082a1 1 0 01-1.585.194l-.24-.316a1 1 0 00-1.585-.194L2.036 12.322z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                stroke="currentColor" class="w-5 h-5">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.774 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.572M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.243 4.243l-4.243-4.243" />
              </svg>
            </button>
          </div>
        </div>

        <p v-if="error" class="text-red-500 text-center">{{ error }}</p>

        <button type="submit" :disabled="loading"
          class="w-full py-3.5 bg-primary-600 text-white border-none rounded-lg text-base font-semibold cursor-pointer transition-colors duration-200 hover:bg-primary-700 disabled:bg-primary-300 disabled:cursor-not-allowed">
          {{ loading ? 'Ingresando...' : 'Ingresar' }}
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fade-in 0.5s ease-out;
}
</style>