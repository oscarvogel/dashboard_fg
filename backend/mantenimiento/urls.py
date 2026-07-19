from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('ordenes/estado/', views.buscar_estado_orden, name='buscar-estado-orden'),
    path('ordenes/<str:referencia>/', views.consultar_orden, name='consultar-orden'),
    path('efectividad-sector/', views.efectividad_sector, name='efectividad-sector'),
    path('efectividad-empleado/', views.efectividad_empleado, name='efectividad-empleado'),
    path('empleados-con-movimiento/', views.empleados_con_movimiento, name='empleados-con-movimiento'),
    path('detalles-sector/', views.detalles_sector, name='detalles-sector'),
    path('tareas-empleado/', views.tareas_empleado, name='tareas-empleado'),
    path('resumen-por-equipo/', views.resumen_por_equipo, name='resumen-por-equipo'),
    path('equipos-con-ordenes/', views.equipos_con_ordenes, name='equipos-con-ordenes'),
    path('tipos-tareas-con-movimiento/', views.tipos_tareas_con_movimiento, name='tipos-tareas-con-movimiento'),
    path('ordenes-por-equipo/', views.ordenes_por_equipo, name='ordenes-por-equipo'),
    path('kpis-mantenimiento/', views.kpis_mantenimiento, name='kpis-mantenimiento'),
]
