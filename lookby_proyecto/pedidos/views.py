from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.permisos import es_admin

from .forms import CrearPedidoForm, PedidoEditarForm
from .models import DetallePedido, Pedido
from .services import cancelar_pedido as cancelar
from .services import crear_pedido as registrar_pedido


def _pedidos_visibles(request):
    """Cliente ve solo los suyos; administrador ve todos."""
    pedidos = Pedido.objects.select_related('cliente', 'local').prefetch_related(
        Prefetch(
            'detalles',
            queryset=DetallePedido.objects.select_related('inventario__producto'),
        )
    )
    if not es_admin(request.user):
        pedidos = pedidos.filter(cliente=request.user)
    return pedidos


@login_required
def lista_pedidos(request):
    return render(request, 'pedidos/lista_pedidos.html', {
        'pedidos': _pedidos_visibles(request),
        'es_admin': es_admin(request.user),
    })


@login_required
def crear_pedido(request):
    """Registra un pedido validando stock y calculando el total en el servidor."""
    if request.method == 'POST':
        form = CrearPedidoForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                registrar_pedido(
                    cliente=request.user,
                    local=datos['local'],
                    direccion_entrega=datos['direccion_entrega'],
                    items=[{
                        'inventario_id': datos['inventario'].pk,
                        'cantidad': datos['cantidad'],
                    }],
                )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, '¡Pedido confirmado!')
                # Destino conservado para las pruebas existentes.
                return redirect('pedidos:lista')
    else:
        form = CrearPedidoForm()
    return render(request, 'pedidos/crear.html', {'form': form})


@login_required
def detalle_pedido(request, pk):
    pedido = get_object_or_404(_pedidos_visibles(request), pk=pk)
    return render(request, 'pedidos/detalle.html', {
        'pedido': pedido,
        'es_admin': es_admin(request.user),
    })


@login_required
def editar_pedido(request, pk):
    pedido = get_object_or_404(_pedidos_visibles(request), pk=pk)
    if pedido.estado in ('CANCELADO', 'ENTREGADO'):
        messages.error(request, 'Este pedido ya no se puede editar.')
        return redirect('pedidos:detalle', pk=pedido.pk)

    if request.method == 'POST':
        form = PedidoEditarForm(request.POST, instance=pedido)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dirección del pedido actualizada.')
            return redirect('pedidos:detalle', pk=pedido.pk)
    else:
        form = PedidoEditarForm(instance=pedido)
    return render(request, 'pedidos/editar.html', {'form': form, 'pedido': pedido})


@login_required
def eliminar_pedido(request, pk):
    """Baja lógica (cancelación), nunca borrado físico de un pedido confirmado."""
    pedido = get_object_or_404(_pedidos_visibles(request), pk=pk)
    if request.method == 'POST':
        try:
            cancelar(pedido)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        else:
            messages.success(request, 'Pedido cancelado.')
        return redirect('pedidos:lista')
    return render(request, 'pedidos/cancelar.html', {'pedido': pedido})
