from django.contrib import admin

from produccion.models import Empleado

# Register your models here.
@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'dni', 'user')
    search_fields = ('nombre', 'dni')
    list_filter = ('user',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')
    