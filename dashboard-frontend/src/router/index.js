import { createRouter, createWebHistory } from 'vue-router'

// Vistas existentes
import ResumenOperacional from '../views/ResumenOperacional.vue'
import ResumenCombustible from '../views/ResumenCombustible.vue'
import ReporteProduccion from '../views/ReporteProduccion.vue'
import HorasNoOperativas from '../views/HorasNoOperativas.vue'
import MaquinasPorFrente from '../views/MaquinasPorFrente.vue'
import EfectividadServicios from '../views/EfectividadServicios.vue'
import ResumenMaquinasComponentes from '../views/ResumenMaquinasComponentes.vue'
import KPIsChoferes from '../views/KPIsChoferes.vue'

// Carga diferida para vistas principales
const LoginView = () => import('../views/LoginView.vue')
const DashboardView = () => import('../views/DashboardView.vue')
const ProduccionEjecutivaView = () => import('../views/ProduccionEjecutivaView.vue')
const MantenimientoKPIs = () => import('../views/MantenimientoKPIs.vue')

const routes = [
  { path: '/', name: 'login', component: LoginView },
  {
    path: '/dashboard',
    name: 'produccion-ejecutiva',
    component: ProduccionEjecutivaView,
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard-detallado',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/mantenimiento-kpis',
    name: 'MantenimientoKPIs',
    component: MantenimientoKPIs,
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
  },
  {
    path: '/reporte-produccion',
    name: 'ReporteProduccion',
    component: ReporteProduccion,
    meta: { requiresAuth: true }
  },
  {
    path: '/horas-no-operativas',
    name: 'HorasNoOperativas',
    component: HorasNoOperativas,
    meta: { requiresAuth: true }
  },
  {
    path: '/maquinas-frente-operador',
    name: 'MaquinasPorFrente',
    component: MaquinasPorFrente,
    meta: { requiresAuth: true }
  },
  {
    path: '/efectividad-servicios',
    name: 'EfectividadServicios',
    component: EfectividadServicios,
    meta: { requiresAuth: true }
  },
  {
    path: '/resumen-maquinas-componentes',
    name: 'ResumenMaquinasComponentes',
    component: ResumenMaquinasComponentes,
    meta: { requiresAuth: true }
  }
  ,
  {
    path: '/kpis-choferes',
    name: 'KPIsChoferes',
    component: KPIsChoferes,
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