from django.db import models

class Ubicacion(models.Model):
    idUbicacion = models.AutoField(primary_key=True)
    nombreLugar = models.CharField(max_length=150)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.nombreLugar} - {self.direccion}"