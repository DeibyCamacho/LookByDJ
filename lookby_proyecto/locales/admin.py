from django.contrib import admin

from .models import Local


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'ciudad', 'direccion', 'activo')
    list_filter = ('activo', 'ciudad')
    search_fields = ('nombre', 'ciudad', 'direccion')
    filter_horizontal = ('administradores',)
