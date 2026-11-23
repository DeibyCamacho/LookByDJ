from django.contrib import admin
from .models import InventarioLocal


@admin.register(InventarioLocal)
class InventarioLocalAdmin(admin.ModelAdmin):
    list_display = ('local', 'producto', 'precio_venta', 'stock_actual')
    search_fields = ('local__nombre', 'producto__nombre')
    list_filter = ('local',)
