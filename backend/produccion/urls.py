from django.urls import path, include
from .views import (
    CargasCombustibleView, CombustibleEquipoLHView, CombustibleEquipoVsHistoricoView,
    CombustibleSinProduccionView, EmpleadoViewSet, EquipoAliasesPatchView, EquiposListSearchView, EquiposPorUNView,
    FacturacionMovilView, FiltrosCombustibleView, FiltrosDinamicosView, HorasNoOperativasDashboardView, LoginEmpleadoView,
    MovilOperativoView, MovilesRankingView, ProduccionDashboardView, ProduccionEjecutivaView, ProduccionOperadorView, RegistrosEmpleadoViewSet,
    ResumenOperacionalView, UnidadesNegocioActivasView, maquinas_por_frente_operador, resumen_maquinas_componentes,
)
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
    path('produccion-ejecutiva/', ProduccionEjecutivaView.as_view(), name='produccion-ejecutiva'),
    path('produccion-ejecutiva-filtros/', UnidadesNegocioActivasView.as_view(), name='produccion-ejecutiva-filtros'),
    path('filtros/', FiltrosDinamicosView.as_view(), name='filtros-dinamicos'),
    path('resumen-operacional/', ResumenOperacionalView.as_view(), name='resumen-operacional'),
    path('filtros-combustible/', FiltrosCombustibleView.as_view(), name='filtros-combustible'),
    path('equipos-por-un/', EquiposPorUNView.as_view(), name='equipos-por-un'),
    path('cargas-combustible/', CargasCombustibleView.as_view(), name='cargas-combustible'),
    path('combustible-equipo-lh/', CombustibleEquipoLHView.as_view(), name='combustible-equipo-lh'),
    path('combustible-equipo-vs-historico/', CombustibleEquipoVsHistoricoView.as_view(), name='combustible-equipo-vs-historico'),
    path('combustible-sin-produccion/', CombustibleSinProduccionView.as_view(), name='combustible-sin-produccion'),
    path('indicadores/facturacion-movil/', FacturacionMovilView.as_view(), name='facturacion-movil'),
    path('indicadores/movil-operativo/', MovilOperativoView.as_view(), name='movil-operativo'),
    path('indicadores/moviles-ranking/', MovilesRankingView.as_view(), name='moviles-ranking'),
    path('horas-no-operativas/', HorasNoOperativasDashboardView.as_view(), name='horas-no-operativas'),
    path('maquinas-frente-operador/', maquinas_por_frente_operador, name='maquinas_frente_operador'),
    path('resumen-maquinas-componentes/', resumen_maquinas_componentes, name='resumen_maquinas_componentes'),
    # === feature/equipo-aliases (2026-07-08) ===================================
    path('equipos/', EquiposListSearchView.as_view(), name='equipos-search'),
    path('equipos/<str:patente>/aliases/', EquipoAliasesPatchView.as_view(), name='equipos-aliases-patch'),
]
