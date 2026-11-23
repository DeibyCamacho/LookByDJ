from django.contrib import admin
from .models import InventarioLocal
# Register your models here.
@admin.register(InventarioLocal)
class InventarioLocalAdmin(admin.ModelAdmin):
    list_display = ('local_id', 'producto', 'precio_venta', 'stock_actual')
    search_fields = ('local_id', 'producto__nombre')
    list_filter = ('local_id',)