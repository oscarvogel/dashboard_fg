from django.urls import path, include
from .views import CargasCombustibleView, EmpleadoViewSet, EquiposPorUNView, FiltrosCombustibleView, FiltrosDinamicosView, LoginEmpleadoView, ProduccionDashboardView, ProduccionOperadorView, RegistrosEmpleadoViewSet, ResumenOperacionalView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'empleado', EmpleadoViewSet)
router.register(r'registros-empleado', RegistrosEmpleadoViewSet, basename='registros-empleado')

urlpatterns = [
    path('', include(router.urls)),
    path('login-empleado/', LoginEmpleadoView.as_view(), name='login_empleado'),
    path('produccion/', ProduccionOperadorView.as_view(), name='produccion_operador'),
    # path('produccion-dashboard/', ProduccionListView.as_view(), name='produccion-list'),
    path('produccion-dashboard/', ProduccionDashboardView.as_view(), name='produccion-list'),
    path('filtros/', FiltrosDinamicosView.as_view(), name='filtros-dinamicos'),
    path('resumen-operacional/', ResumenOperacionalView.as_view(), name='resumen-operacional'),
    path('filtros-combustible/', FiltrosCombustibleView.as_view(), name='filtros-combustible'),
    path('equipos-por-un/', EquiposPorUNView.as_view(), name='equipos-por-un'),
    path('cargas-combustible/', CargasCombustibleView.as_view(), name='cargas-combustible'),    
]