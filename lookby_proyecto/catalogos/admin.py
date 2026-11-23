from django.contrib import admin
from .models import Catalogo, CatalogoProducto


@admin.register(Catalogo)
class CatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'local')
    list_filter = ('local',)
    search_fields = ('nombre',)


@admin.register(CatalogoProducto)
class CatalogoProductoAdmin(admin.ModelAdmin):
    list_display = ('catalogo', 'producto', 'inventario')
    search_fields = ('catalogo__nombre', 'inventario__producto__nombre')
