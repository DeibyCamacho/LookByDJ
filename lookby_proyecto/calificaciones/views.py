from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from usuarios.permisos import es_admin

from .forms import CalificacionForm
from .models import Calificacion


def _puede_editar(request, calificacion):
    return calificacion.cliente_id == request.user.pk or es_admin(request.user)


def lista_calificaciones(request):
    calificaciones = Calificacion.objects.select_related(
        'cliente', 'local', 'profesional'
    ).all()
    return render(
        request,
        'calificaciones/lista.html',
        {'calificaciones': calificaciones},
    )


@login_required
def crear_calificacion(request):
    if request.method == 'POST':
        form = CalificacionForm(request.POST, cliente=request.user)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.cliente = request.user
            try:
                calificacion.full_clean()
                calificacion.save()
            except ValidationError as exc:
                form.add_error(None, exc)
            except IntegrityError:
                form.add_error(None, 'Ya calificaste este local o profesional.')
            else:
                messages.success(request, '¡Gracias por tu calificación!')
                # Destino conservado para las pruebas existentes.
                return redirect('calificaciones:lista')
    else:
        form = CalificacionForm(cliente=request.user)
    return render(request, 'calificaciones/crear.html', {'form': form})


def detalle_calificacion(request, pk):
    calificacion = get_object_or_404(
        Calificacion.objects.select_related('cliente', 'local', 'profesional'),
        pk=pk,
    )
    return render(
        request,
        'calificaciones/detalle.html',
        {'calificacion': calificacion},
    )


@login_required
def editar_calificacion(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if not _puede_editar(request, calificacion):
        raise Http404('No puedes editar esta calificación.')

    if request.method == 'POST':
        form = CalificacionForm(
            request.POST, instance=calificacion, cliente=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Calificación actualizada.')
            return redirect('calificaciones:detalle', pk=calificacion.pk)
    else:
        form = CalificacionForm(instance=calificacion, cliente=request.user)
    return render(request, 'calificaciones/editar.html', {
        'form': form,
        'calificacion': calificacion,
    })


@login_required
def eliminar_calificacion(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk)
    if not _puede_editar(request, calificacion):
        raise Http404('No puedes eliminar esta calificación.')

    if request.method == 'POST':
        calificacion.delete()
        messages.success(request, 'Calificación eliminada.')
        return redirect('calificaciones:lista')
    return render(request, 'calificaciones/eliminar.html', {
        'calificacion': calificacion,
    })
