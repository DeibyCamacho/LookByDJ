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
        try:
            cantidad = int(item['cantidad'])
        except (KeyError, TypeError, ValueError):
            raise ValidationError('La cantidad debe ser un número entero.')
        if cantidad <= 0:
            raise ValidationError('La cantidad debe ser mayor que cero.')

        # Guarda defensiva: un inventario de otro local antes terminaba en un
        # 500 (InventarioLocal.DoesNotExist) si el formulario era manipulado.
        try:
            inventario = InventarioLocal.objects.select_for_update().get(
                pk=item['inventario_id'],
                local=local,
            )
        except (InventarioLocal.DoesNotExist, ValueError, TypeError):
            raise ValidationError(
                'El producto seleccionado no pertenece al local indicado.'
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


@transaction.atomic
def cancelar_pedido(pedido):
    """
    Baja lógica: usa el estado CANCELADO ya existente en el modelo (no hace
    falta migración) y devuelve al inventario el stock reservado.
    """
    if pedido.estado not in ('PENDIENTE', 'CONFIRMADO'):
        raise ValidationError('Este pedido ya no se puede cancelar.')

    cantidades = {}
    for detalle in pedido.detalles.all():
        cantidades[detalle.inventario_id] = (
            cantidades.get(detalle.inventario_id, 0) + detalle.cantidad
        )
    for inventario_id, cantidad in cantidades.items():
        inventario = InventarioLocal.objects.select_for_update().get(pk=inventario_id)
        inventario.stock_actual += cantidad
        inventario.save(update_fields=['stock_actual'])

    pedido.estado = 'CANCELADO'
    pedido.save(update_fields=['estado'])
    return pedido
