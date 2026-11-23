from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from inventario.models import InventarioLocal
from .models import DetallePedido, Pedido


@transaction.atomic
def crear_pedido(cliente, local, direccion_entrega='', items=None):
    """
    Confirma un pedido: valida stock del local, descuenta existencias y
    calcula el total en el servidor (nunca se confía en el total del navegador).

    `items` es una lista de dicts: {'inventario_id': int, 'cantidad': int}.
    """
    items = items or []
    if not items:
        raise ValidationError('El pedido debe tener al menos un producto.')

    pedido = Pedido.objects.create(
        cliente=cliente,
        local=local,
        direccion_entrega=direccion_entrega,
        estado='PENDIENTE',
    )

    total = Decimal('0.00')
    for item in items:
        cantidad = int(item['cantidad'])
        if cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor que cero.')

        inventario = InventarioLocal.objects.select_for_update().get(
            pk=item['inventario_id'],
            local=local,
        )
        if inventario.stock_actual < cantidad:
            raise ValidationError(
                f'Stock insuficiente para {inventario.producto.nombre}.'
            )

        precio = inventario.precio_venta
        DetallePedido.objects.create(
            pedido=pedido,
            inventario=inventario,
            cantidad=cantidad,
            precio_unitario=precio,
        )
        inventario.stock_actual -= cantidad
        inventario.save(update_fields=['stock_actual'])
        total += precio * cantidad

    pedido.total = total
    pedido.estado = 'CONFIRMADO'
    pedido.save(update_fields=['total', 'estado'])
    return pedido
