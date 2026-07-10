from django.contrib import admin

from produccion.models import Empleado, Equipo

# Register your models here.
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni', 'user')
    search_fields = ('nombre', 'dni')
    list_filter = ('user',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    """feature/equipo-aliases (2026-07-08) — Admin para Equipo con aliases editables."""
    list_display = ('patente', 'detalle', 'codigo_fg', 'modelo_normalizado', 'baja')
    search_fields = ('patente', 'detalle', 'codigo_fg', 'modelo_normalizado')
    list_filter = ('baja', 'tipo_movil', 'unidad_negocio')
    list_editable = ('codigo_fg', 'modelo_normalizado', 'baja')
    