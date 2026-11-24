from django.contrib import admin
from .models import VwMapaLocales


@admin.register(VwMapaLocales)
class VwMapaLocalesAdmin(admin.ModelAdmin):
    """Solo lectura: VW_MAPA_LOCALES es una vista SQL, no una tabla editable."""

    list_display = ('id_local', 'nombre', 'direccion', 'calificacion')
    search_fields = ('nombre', 'direccion')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
