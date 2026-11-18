from django.contrib import admin
from .models import Proveedor, Marca, CategoriaInsumo, ProductoProveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'contacto', 'telefono', 'correo')
    search_fields = ('nombre_empresa', 'contacto', 'correo')

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(CategoriaInsumo)
class CategoriaInsumoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(ProductoProveedor)
class ProductoProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre_producto', 'presentacion_o_tono', 'proveedor', 'marca', 'categoria', 'precio_mayorista', 'stock', 'disponible')
    list_filter = ('disponible', 'categoria', 'marca', 'proveedor')
    search_fields = ('nombre_producto', 'presentacion_o_tono')
    list_editable = ('precio_mayorista', 'stock', 'disponible')
