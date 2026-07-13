from django.urls import path

from .views import (
    CerrarIncidenciaEquipoView, EventoEstadoEquipoCreateView, HorasParadasView,
    IncidenciaEquipoListCreateView, IncidenciaPersonalListCreateView,
    IncidenciasPorPersonaView, ResolverReferenciaView, ResumenMensualView,
)

app_name = "incidencias"
urlpatterns = [
    path("equipos/", IncidenciaEquipoListCreateView.as_view(), name="equipo-list-create"),
    path("equipos/<int:pk>/eventos/", EventoEstadoEquipoCreateView.as_view(), name="evento-create"),
    path("equipos/<int:pk>/cerrar/", CerrarIncidenciaEquipoView.as_view(), name="equipo-close"),
    path("personas/", IncidenciaPersonalListCreateView.as_view(), name="persona-list-create"),
    path("horas-paradas/", HorasParadasView.as_view(), name="horas-paradas"),
    path("por-persona/", IncidenciasPorPersonaView.as_view(), name="por-persona"),
    path("resumen-mensual/", ResumenMensualView.as_view(), name="resumen-mensual"),
    path("resolver/", ResolverReferenciaView.as_view(), name="resolver"),
]
