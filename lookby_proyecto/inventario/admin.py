from django.contrib import admin

from .forms import InventarioForm
from .models import InventarioLocal


@admin.register(InventarioLocal)
class InventarioLocalAdmin(admin.ModelAdmin):
    # Reutiliza el ModelForm de la app: precio (>= 0, 2 decimales, tope) y
    # stock (0 a 100000) usan los mismos validadores compartidos.
    form = InventarioForm
    list_display = ('local', 'producto', 'precio_venta', 'stock_actual')
    search_fields = ('local__nombre', 'producto__nombre')
    list_filter = ('local',)
    list_select_related = ('local', 'producto')
