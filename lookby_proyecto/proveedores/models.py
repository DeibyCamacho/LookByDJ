from django.db import models

class Proveedor(models.Model):
    idProveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=50)
    correo = models.CharField(max_length=150)

    def __str__(self):
        return self.nombre

class ProveedorProducto(models.Model):
    idProveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, db_column='idProveedor')
    # Ajuste temporal: reemplazamos la llave foránea por texto mientras se crea la app de productos
    nombreProducto = models.CharField(max_length=150, default="Producto genérico")
    precioMayoreo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('idProveedor', 'nombreProducto')

    def __str__(self):
        return f"{self.idProveedor.nombre} - {self.nombreProducto}"