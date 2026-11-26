from django.core.validators import MaxValueValidator
from django.db import models

from productos.models import Producto
from usuarios.validators import validadores_precio


class InventarioLocal(models.Model):
    """Stock y precio de venta de un producto dentro de un local (MER: INVENTARIO)."""

    local = models.ForeignKey(
        'locales.Local',
        on_delete=models.CASCADE,
        related_name='inventarios',
        db_column='idLocal',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='inventarios',
        db_column='idProducto',
    )
    precio_venta = models.DecimalField(
        'precio de venta',
        max_digits=10,
        decimal_places=2,
        validators=validadores_precio(),
        help_text='Precio en pesos colombianos. Puede ser 0; máximo 2 decimales.',
        error_messages={
            'min_value': 'El precio de venta no puede ser negativo. Usa 0 si es gratuito.',
            'max_value': 'El precio de venta supera el máximo permitido.',
            'max_digits': 'El precio de venta tiene demasiados dígitos.',
            'decimal_places': 'El precio de venta admite máximo 2 decimales.',
        },
    )
    stock_actual = models.PositiveIntegerField(
        'stock actual',
        default=0,
        validators=[MaxValueValidator(100000)],
        help_text='Unidades disponibles (de 0 a 100000).',
        error_messages={
            'min_value': 'El stock no puede ser negativo. Usa 0 si no hay existencias.',
            'max_value': 'El stock no puede superar las 100000 unidades.',
        },
    )

    class Meta:
        # Se conserva `unique_together` (legacy): convertirlo en UniqueConstraint
        # nominal exigiría una migración adicional y no cambia la regla de negocio.
        unique_together = ('local', 'producto')

    def __str__(self):
        return f'{self.local.nombre} - {self.producto.nombre} (Stock: {self.stock_actual})'
