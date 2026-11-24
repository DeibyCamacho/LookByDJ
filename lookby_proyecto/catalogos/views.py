from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.permisos import admin_required

from .forms import CatalogoForm, CatalogoProductoForm
from .models import Catalogo, CatalogoProducto


def lista_catalogos(request):
    catalogos = Catalogo.objects.select_related('local').all()
    return render(request, 'catalogos/lista_catalogos.html', {'catalogos': catalogos})


def detalle_catalogo(request, pk):
    catalogo = get_object_or_404(
        Catalogo.objects.select_related('local'), pk=pk
    )
    items = catalogo.productos.select_related(
        'inventario__producto', 'inventario__local'
    )
    return render(request, 'catalogos/detalle.html', {
        'catalogo': catalogo, 'items': items,
    })


@login_required
@admin_required
def crear_catalogo(request):
    if request.method == 'POST':
        form = CatalogoForm(request.POST)
        if form.is_valid():
            catalogo = form.save()
            messages.success(request, 'Catálogo registrado correctamente.')
            return redirect('catalogos:detalle', pk=catalogo.pk)
    else:
        form = CatalogoForm()
    return render(request, 'catalogos/form.html', {
        'form': form, 'titulo': 'Registrar catálogo',
    })


@login_required
@admin_required
def editar_catalogo(request, pk):
    catalogo = get_object_or_404(Catalogo, pk=pk)
    if request.method == 'POST':
        form = CatalogoForm(request.POST, instance=catalogo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catálogo actualizado.')
            return redirect('catalogos:detalle', pk=catalogo.pk)
    else:
        form = CatalogoForm(instance=catalogo)
    return render(request, 'catalogos/form.html', {
        'form': form, 'titulo': 'Editar catálogo', 'catalogo': catalogo,
    })


@login_required
@admin_required
def eliminar_catalogo(request, pk):
    """Sin campo `activo`: solo se borra si no tiene productos asociados."""
    catalogo = get_object_or_404(Catalogo, pk=pk)
    con_productos = catalogo.productos.exists()
    if request.method == 'POST':
        if con_productos:
            messages.error(
                request,
                'No se puede borrar: este catálogo tiene productos. '
                'Quítalos del catálogo primero.',
            )
            return redirect('catalogos:detalle', pk=catalogo.pk)
        catalogo.delete()
        messages.success(request, 'Catálogo eliminado.')
        return redirect('catalogos:lista')
    return render(request, 'catalogos/confirmar_eliminar.html', {
        'catalogo': catalogo, 'con_productos': con_productos,
    })


@login_required
@admin_required
def agregar_producto(request, pk):
    catalogo = get_object_or_404(Catalogo, pk=pk)
    if request.method == 'POST':
        form = CatalogoProductoForm(request.POST, catalogo=catalogo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado al catálogo.')
            return redirect('catalogos:detalle', pk=catalogo.pk)
    else:
        form = CatalogoProductoForm(catalogo=catalogo)
    return render(request, 'catalogos/producto_form.html', {
        'form': form, 'catalogo': catalogo,
        'titulo': 'Agregar producto al catálogo',
    })


@login_required
@admin_required
def editar_producto(request, pk, item_pk):
    catalogo = get_object_or_404(Catalogo, pk=pk)
    item = get_object_or_404(CatalogoProducto, pk=item_pk, catalogo=catalogo)
    if request.method == 'POST':
        form = CatalogoProductoForm(request.POST, instance=item, catalogo=catalogo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto del catálogo actualizado.')
            return redirect('catalogos:detalle', pk=catalogo.pk)
    else:
        form = CatalogoProductoForm(instance=item, catalogo=catalogo)
    return render(request, 'catalogos/producto_form.html', {
        'form': form, 'catalogo': catalogo, 'item': item,
        'titulo': 'Editar producto del catálogo',
    })


@login_required
@admin_required
def eliminar_producto(request, pk, item_pk):
    catalogo = get_object_or_404(Catalogo, pk=pk)
    item = get_object_or_404(CatalogoProducto, pk=item_pk, catalogo=catalogo)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Producto quitado del catálogo.')
        return redirect('catalogos:detalle', pk=catalogo.pk)
    return render(request, 'catalogos/confirmar_eliminar_producto.html', {
        'catalogo': catalogo, 'item': item,
    })
