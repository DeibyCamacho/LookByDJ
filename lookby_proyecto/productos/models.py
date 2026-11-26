from django.db import models

from usuarios.validators import DESCRIPCION_MAX, validador_texto_largo


# Nota: Proveedor y ProveedorProducto viven en la app `proveedores` (decisión
# del equipo). Aquí solo queda el catálogo base de productos del MER.


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(
        blank=True,
        validators=[validador_texto_largo(DESCRIPCION_MAX)],
        help_text=f'Describe el producto en {DESCRIPCION_MAX} caracteres como máximo.',
        error_messages={
            'max_length': f'La descripción no puede superar los {DESCRIPCION_MAX} caracteres.',
        },
    )
    categoria = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
