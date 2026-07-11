from django.contrib import admin

from produccion.models import Empleado, Equipo, EquipoAlias

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


@admin.register(EquipoAlias)
class EquipoAliasAdmin(admin.ModelAdmin):
    list_display = (
        "alias_display",
        "equipo",
        "activo",
        "origen",
        "confirmado_por",
        "confirmado_at",
    )
    list_filter = ("activo", "origen")
    search_fields = (
        "alias_display",
        "alias_normalizado",
        "equipo__patente",
        "equipo__detalle",
    )
    readonly_fields = (
        "alias_normalizado",
        "alias_activo_key",
        "confirmado_por",
        "confirmado_at",
        "created_at",
        "updated_at",
    )
    list_select_related = ("equipo", "confirmado_por")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
