from django.conf import settings
from django.db import models

from usuarios.validators import (
    DIRECCION_MAX,
    validadores_cantidad,
    validadores_direccion,
)


class Pedido(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]

    # MER: PEDIDO.idCliente FK y PEDIDO.idLocal FK (antes eran IDs temporales).
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='pedidos',
        db_column='idCliente',
    )
    local = models.ForeignKey(
        'locales.Local',
        on_delete=models.PROTECT,
        related_name='pedidos',
        db_column='idLocal',
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    direccion_entrega = models.CharField(
        'dirección de entrega',
        max_length=DIRECCION_MAX,
        validators=validadores_direccion(),
        help_text=(
            'Obligatoria. Entre 10 y 150 caracteres, con letras y al menos un '
            'número. Ejemplo: Calle 50 # 43-20, Medellín.'
        ),
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f'Pedido #{self.id} - Cliente {self.cliente} [{self.estado}]'


class DetallePedido(models.Model):
    # MER: DETALLE_PEDIDO apunta a INVENTARIO (precio y stock son por local).
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='detalles',
    )
    inventario = models.ForeignKey(
        'inventario.InventarioLocal',
        on_delete=models.PROTECT,
        related_name='detalles_pedido',
        db_column='idInventario',
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=validadores_cantidad(),
        help_text='Entre 1 y 1000 unidades por producto.',
    )
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Precio fijado en el momento de la compra',
    )

    @property
    def producto(self):
        """Atajo para las plantillas que esperaban detalle.producto."""
        return self.inventario.producto

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f'{self.cantidad}x {self.producto.nombre} (Pedido #{self.pedido.id})'
