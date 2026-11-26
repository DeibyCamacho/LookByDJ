from django.contrib import admin

from .forms import ProveedorForm, ProveedorProductoForm
from .models import Proveedor, ProveedorProducto


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    # Mismo correo validado que en el sitio público (EmailField de 150 caracteres).
    form = ProveedorForm
    list_display = ('idProveedor', 'nombre', 'telefono', 'correo')
    search_fields = ('nombre', 'correo')


@admin.register(ProveedorProducto)
class ProveedorProductoAdmin(admin.ModelAdmin):
    # validadores_precio se aplica también en el admin al reutilizar el form.
    form = ProveedorProductoForm
    list_display = ('idProveedor', 'producto', 'precioMayoreo')
    list_filter = ('idProveedor',)
    search_fields = ('producto__nombre',)
    list_select_related = ('idProveedor', 'producto')
