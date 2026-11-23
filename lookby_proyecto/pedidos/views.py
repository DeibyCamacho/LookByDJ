from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from usuarios.permisos import admin_required

from .forms import CrearPedidoForm
from .models import Pedido
from .services import crear_pedido as registrar_pedido


@admin_required
def lista_pedidos(request):
    pedidos = Pedido.objects.select_related('cliente', 'local').all()
    return render(request, 'pedidos/lista_pedidos.html', {'pedidos': pedidos})


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
                return redirect('lista_pedidos')
    else:
        form = CrearPedidoForm()
    return render(request, 'pedidos/crear.html', {'form': form})
