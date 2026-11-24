from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.permisos import admin_required

from .forms import ProductoForm
from .models import Producto


def lista_productos(request):
    """Catálogo público. El precio no vive aquí: está en InventarioLocal."""
    productos = Producto.objects.filter(activo=True).prefetch_related(
        'inventarios__local'
    )
    return render(request, 'productos/lista_productos.html', {'productos': productos})


def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.prefetch_related('inventarios__local'), pk=pk
    )
    return render(request, 'productos/detalle.html', {'producto': producto})


@login_required
@admin_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('productos:detalle', pk=producto.pk)
    else:
        form = ProductoForm()
    return render(request, 'productos/form.html', {
        'form': form, 'titulo': 'Registrar producto',
    })


@login_required
@admin_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado.')
            return redirect('productos:detalle', pk=producto.pk)
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productos/form.html', {
        'form': form, 'titulo': 'Editar producto', 'producto': producto,
    })


@login_required
@admin_required
def eliminar_producto(request, pk):
    """Baja lógica: se desactiva para no romper inventario ni pedidos."""
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save(update_fields=['activo'])
        messages.success(request, 'Producto desactivado. Se conservó su historial.')
        return redirect('productos:lista')
    return render(request, 'productos/confirmar_eliminar.html', {
        'producto': producto,
    })
