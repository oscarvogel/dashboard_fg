// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import ResumenOperacional from '../views/ResumenOperacional.vue'
import ResumenCombustible from '../views/ResumenCombustible.vue'
import ReporteProduccion from '../views/ReporteProduccion.vue'

const LoginView = () => import('../views/LoginView.vue')
const DashboardView = () => import('../views/DashboardView.vue')

const routes = [
  { path: '/', name: 'login', component: LoginView },
  { 
    path: '/dashboard', 
    name: 'dashboard', 
    component: DashboardView,
    meta: { requiresAuth: true } 
  },
  {
    path: '/resumen-operacional',
    name: 'ResumenOperacional',
    component: ResumenOperacional,
    meta: { requiresAuth: true }
  },
 {
    path: '/resumen-combustible',
    name: 'ResumenCombustible',
    component: ResumenCombustible,
    meta: { requiresAuth: true }
  } ,
 {
    path: '/reporte-produccion',
    name: 'ReporteProduccion',
    component: ReporteProduccion,
    meta: { requiresAuth: true }
  }  
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Guardia de navegación
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/')
  } else if (to.path === '/' && isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router