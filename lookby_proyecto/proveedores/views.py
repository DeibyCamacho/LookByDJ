from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.permisos import admin_required

from .forms import ProveedorForm, ProveedorProductoForm
from .models import Proveedor, ProveedorProducto


@admin_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.order_by('pk')
    pagina = Paginator(proveedores, 20).get_page(request.GET.get('page'))
    return render(request, 'proveedores/lista.html', {
        'proveedores': pagina, 'page_obj': pagina,
    })


@admin_required
def detalle_proveedor(request, pk):
    proveedor = get_object_or_404(
        Proveedor.objects.prefetch_related('productos_suministrados__producto'), pk=pk
    )
    return render(request, 'proveedores/detalle.html', {'proveedor': proveedor})


@login_required
@admin_required
def crear_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, 'Proveedor registrado correctamente.')
            return redirect('proveedores:detalle', pk=proveedor.pk)
    else:
        form = ProveedorForm()
    return render(request, 'proveedores/form.html', {
        'form': form, 'titulo': 'Registrar proveedor',
    })


@login_required
@admin_required
def editar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado.')
            return redirect('proveedores:detalle', pk=proveedor.pk)
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'proveedores/form.html', {
        'form': form, 'titulo': 'Editar proveedor', 'proveedor': proveedor,
    })


@login_required
@admin_required
def eliminar_proveedor(request, pk):
    """Sin campo `activo`: solo se borra si no tiene productos asociados."""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    con_vinculos = proveedor.productos_suministrados.exists()
    if request.method == 'POST':
        if con_vinculos:
            messages.error(
                request,
                'No se puede borrar: este proveedor tiene productos asociados. '
                'Elimina primero esas relaciones.',
            )
            return redirect('proveedores:detalle', pk=proveedor.pk)
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado.')
        return redirect('proveedores:lista')
    return render(request, 'proveedores/confirmar_eliminar.html', {
        'proveedor': proveedor, 'con_vinculos': con_vinculos,
    })


@login_required
@admin_required
def crear_suministro(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado al proveedor.')
            return redirect('proveedores:detalle', pk=proveedor.pk)
    else:
        form = ProveedorProductoForm(initial={'idProveedor': proveedor.pk})
    return render(request, 'proveedores/suministro_form.html', {
        'form': form, 'proveedor': proveedor, 'titulo': 'Agregar producto al proveedor',
    })


@login_required
@admin_required
def editar_suministro(request, pk, suministro_pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    suministro = get_object_or_404(
        ProveedorProducto, pk=suministro_pk, idProveedor=proveedor
    )
    if request.method == 'POST':
        form = ProveedorProductoForm(request.POST, instance=suministro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Precio de mayoreo actualizado.')
            return redirect('proveedores:detalle', pk=proveedor.pk)
    else:
        form = ProveedorProductoForm(instance=suministro)
    return render(request, 'proveedores/suministro_form.html', {
        'form': form, 'proveedor': proveedor,
        'titulo': 'Editar producto del proveedor', 'suministro': suministro,
    })


@login_required
@admin_required
def eliminar_suministro(request, pk, suministro_pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    suministro = get_object_or_404(
        ProveedorProducto, pk=suministro_pk, idProveedor=proveedor
    )
    if request.method == 'POST':
        suministro.delete()
        messages.success(request, 'Producto quitado del proveedor.')
        return redirect('proveedores:detalle', pk=proveedor.pk)
    return render(request, 'proveedores/confirmar_eliminar_suministro.html', {
        'proveedor': proveedor, 'suministro': suministro,
    })
