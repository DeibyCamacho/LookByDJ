from django.db import models
from productos.models import Producto


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
    precio_venta = models.DecimalField('precio de venta', max_digits=10, decimal_places=2)
    stock_actual = models.PositiveIntegerField('stock actual', default=0)

    class Meta:
        unique_together = ('local', 'producto')

    def __str__(self):
        return f'{self.local.nombre} - {self.producto.nombre} (Stock: {self.stock_actual})'
