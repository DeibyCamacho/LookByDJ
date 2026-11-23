from django.db import models


class Producto(models.Model):
    nombre = models.CharField(max_length=20)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=20, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class Proveedor(models.Model):
    nombre = models.CharField(max_length=20)
    telefono = models.CharField(max_length=30, blank=True)
    correo = models.EmailField(blank=True)

    def __str__(self):
        return self.nombre

class ProveedorProducto(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos_suministrados')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='proveedores')
    precio_suministro = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('proveedor', 'producto')

    def __str__(self):
        return f"{self.proveedor.nombre} - {self.producto.nombre}"