from django.db import models

from usuarios.validators import (
    validadores_correo,
    validadores_precio,
    validadores_telefono,
)


class Proveedor(models.Model):
    idProveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(
        'teléfono',
        max_length=50,
        validators=validadores_telefono(),
        help_text='Entre 7 y 15 dígitos. Puedes empezar con + y separar con espacios.',
    )
    correo = models.EmailField(
        'correo electrónico',
        max_length=150,
        validators=validadores_correo(),
        help_text='Correo válido, con arroba y dominio (máximo 150 caracteres).',
        error_messages={'invalid': 'Escribe un correo electrónico válido.'},
    )

    def __str__(self):
        return self.nombre


class ProveedorProducto(models.Model):
    idProveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        db_column='idProveedor',
        related_name='productos_suministrados',
    )
    # MER: PROVEEDOR_PRODUCTO.idProducto FK (antes era texto temporal).
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE,
        db_column='idProducto',
        related_name='proveedores',
    )
    precioMayoreo = models.DecimalField(
        'precio de mayoreo',
        max_digits=10,
        decimal_places=2,
        validators=validadores_precio(),
        help_text='Precio de mayoreo en pesos. Puede ser 0; máximo 2 decimales.',
        error_messages={
            'min_value': 'El precio de mayoreo no puede ser negativo. Usa 0 si es gratuito.',
            'max_value': 'El precio de mayoreo supera el máximo permitido.',
            'max_digits': 'El precio de mayoreo tiene demasiados dígitos.',
            'decimal_places': 'El precio de mayoreo admite máximo 2 decimales.',
        },
    )

    class Meta:
        # Se conserva `unique_together` (legacy): convertirlo en UniqueConstraint
        # nominal exigiría una migración adicional y no cambia la regla de negocio.
        unique_together = ('idProveedor', 'producto')

    def __str__(self):
        return f'{self.idProveedor.nombre} - {self.producto.nombre}'
