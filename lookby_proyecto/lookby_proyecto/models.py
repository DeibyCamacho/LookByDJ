from django.db import models

class Proveedor(models.Model):
    nombre_empresa = models.CharField(max_length=150)
    contacto = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    correo = models.EmailField(unique=True)
    direccion = models.TextField()

    def __str__(self):
        return self.nombre_empresa

class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nombre

class CategoriaInsumo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class ProductoProveedor(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    categoria = models.ForeignKey(CategoriaInsumo, on_delete=models.SET_NULL, null=True)
    nombre_producto = models.CharField(max_length=150)
    presentacion_o_tono = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField()
    precio_mayorista = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre_producto} - {self.presentacion_o_tono}" if self.presentacion_o_tono else self.nombre_producto