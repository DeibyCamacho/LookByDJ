from django.db import models


# Nota: Proveedor y ProveedorProducto viven en la app `proveedores` (decisión
# del equipo). Aquí solo queda el catálogo base de productos del MER.


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
