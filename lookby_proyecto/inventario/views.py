from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.permisos import admin_required

from .forms import InventarioForm
from .models import InventarioLocal


@admin_required
def lista_inventario(request):
    inventarios = InventarioLocal.objects.select_related('local', 'producto').all()
    return render(request, 'inventario/lista_inventario.html', {
        'inventarios': inventarios,
    })


@admin_required
def detalle_inventario(request, pk):
    inventario = get_object_or_404(
        InventarioLocal.objects.select_related('local', 'producto'), pk=pk
    )
    return render(request, 'inventario/detalle.html', {'inventario': inventario})


@login_required
@admin_required
def crear_inventario(request):
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            inventario = form.save()
            messages.success(request, 'Inventario registrado correctamente.')
            return redirect('inventario:detalle', pk=inventario.pk)
    else:
        form = InventarioForm()
    return render(request, 'inventario/form.html', {
        'form': form, 'titulo': 'Registrar inventario',
    })


@login_required
@admin_required
def editar_inventario(request, pk):
    inventario = get_object_or_404(InventarioLocal, pk=pk)
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventario actualizado.')
            return redirect('inventario:detalle', pk=inventario.pk)
    else:
        form = InventarioForm(instance=inventario)
    return render(request, 'inventario/form.html', {
        'form': form, 'titulo': 'Editar inventario', 'inventario': inventario,
    })


@login_required
@admin_required
def eliminar_inventario(request, pk):
    inventario = get_object_or_404(InventarioLocal, pk=pk)
    usado_en_catalogos = inventario.catalogos.exists()
    if request.method == 'POST':
        if usado_en_catalogos:
            messages.error(
                request,
                'No se puede borrar: este inventario aparece en catálogos. '
                'Quítalo de los catálogos primero.',
            )
            return redirect('inventario:detalle', pk=inventario.pk)
        inventario.delete()
        messages.success(request, 'Registro de inventario eliminado.')
        return redirect('inventario:lista')
    return render(request, 'inventario/confirmar_eliminar.html', {
        'inventario': inventario,
        'usado_en_catalogos': usado_en_catalogos,
    })
