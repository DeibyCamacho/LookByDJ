from django.contrib import admin
from .models import Proveedor, ProveedorProducto


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('idProveedor', 'nombre', 'telefono', 'correo')
    search_fields = ('nombre', 'correo')


@admin.register(ProveedorProducto)
class ProveedorProductoAdmin(admin.ModelAdmin):
    list_display = ('idProveedor', 'producto', 'precioMayoreo')
    list_filter = ('idProveedor',)
    search_fields = ('producto__nombre',)
