from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from locales.models import Local
from usuarios.permisos import admin_required

from .forms import InventarioForm
from .models import InventarioLocal


MENSAJE_LOCAL_AJENO = (
    'No puedes gestionar el inventario de un local que no administras.'
)


def exigir_administrador_local(usuario, local):
    """Solo el dueño/administrador del local (o un superusuario) puede editarlo."""
    if local is None or not local.puede_administrar(usuario):
        raise PermissionDenied(MENSAJE_LOCAL_AJENO)


@admin_required
def lista_inventario(request):
    inventarios = InventarioLocal.objects.select_related(
        'local', 'producto'
    ).order_by('pk')
    pagina = Paginator(inventarios, 20).get_page(request.GET.get('page'))
    return render(request, 'inventario/lista_inventario.html', {
        'inventarios': pagina,
        'page_obj': pagina,
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
        # Comprobamos también el local enviado antes de dar por válido el form.
        local_id = request.POST.get('local')
        if local_id and str(local_id).isdigit():
            local = Local.objects.filter(pk=local_id).first()
            if local is not None:
                exigir_administrador_local(request.user, local)
        form = InventarioForm(request.POST)
        if form.is_valid():
            exigir_administrador_local(request.user, form.cleaned_data['local'])
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
    inventario = get_object_or_404(
        InventarioLocal.objects.select_related('local', 'producto'), pk=pk
    )
    exigir_administrador_local(request.user, inventario.local)
    if request.method == 'POST':
        local_id = request.POST.get('local')
        if local_id and str(local_id).isdigit():
            local = Local.objects.filter(pk=local_id).first()
            if local is not None:
                exigir_administrador_local(request.user, local)
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            exigir_administrador_local(request.user, form.cleaned_data['local'])
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
    inventario = get_object_or_404(
        InventarioLocal.objects.select_related('local', 'producto'), pk=pk
    )
    exigir_administrador_local(request.user, inventario.local)
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
