from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import LocalForm
from .models import Local


def _local_administrable(request, pk):
    """Devuelve el local solo si el usuario lo administra; si no, 403."""
    local = get_object_or_404(Local, pk=pk)
    if not local.puede_administrar(request.user):
        raise PermissionDenied
    return local


def lista_locales(request):
    locales = Local.objects.filter(activo=True)
    ciudad = request.GET.get('ciudad', '').strip()
    nombre = (request.GET.get('nombre') or request.GET.get('q') or '').strip()
    if ciudad:
        locales = locales.filter(ciudad__icontains=ciudad)
    if nombre:
        locales = locales.filter(nombre__icontains=nombre)
    return render(request, 'locales/lista.html', {
        'locales': locales,
        'ciudad': ciudad,
        'nombre': nombre,
    })


def detalle_local(request, pk):
    local = get_object_or_404(Local, pk=pk)
    puede_admin = local.puede_administrar(request.user)
    if not local.activo and not puede_admin:
        # Un local desactivado no se muestra al público
        return render(request, 'locales/no_disponible.html', status=404)
    return render(request, 'locales/detalle.html', {'local': local, 'puede_admin': puede_admin})


@login_required
def crear_local(request):
    if request.method == 'POST':
        form = LocalForm(request.POST)
        if form.is_valid():
            local = form.save(commit=False)
            local.usuario = request.user  # FK idUsuario del MER
            local.save()
            form.save_m2m()
            # Administrador de ESTE local, nunca administrador global.
            local.administradores.add(request.user)
            messages.success(request, 'Local registrado.')
            return redirect('locales:detalle', pk=local.pk)
    else:
        form = LocalForm()
    return render(request, 'locales/form.html', {'form': form, 'titulo': 'Registrar local'})


@login_required
def editar_local(request, pk):
    local = _local_administrable(request, pk)
    if request.method == 'POST':
        form = LocalForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            messages.success(request, 'Local actualizado.')
            return redirect('locales:detalle', pk=local.pk)
    else:
        form = LocalForm(instance=local)
    return render(request, 'locales/form.html', {'form': form, 'titulo': 'Editar local', 'local': local})


@login_required
def desactivar_local(request, pk):
    local = _local_administrable(request, pk)
    if request.method == 'POST':
        local.activo = False  # se desactiva, no se borra: conserva el historial
        local.save(update_fields=['activo'])
        messages.success(request, 'Local desactivado.')
        return redirect('locales:lista')
    return render(request, 'locales/confirmar_desactivar.html', {'local': local})
