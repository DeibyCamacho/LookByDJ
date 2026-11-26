from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from usuarios.permisos import es_admin

from profesionales.models import Profesional

from .forms import CrearCitaForm, ReprogramarCitaForm
from .models import Cita
from .services import cancelar_cita as cancelar_cita_servicio
from .services import crear_cita as reservar_cita
from .services import reprogramar_cita


def _cita_del_cliente(request, pk):
    """Ver es para todos los roles; modificar solo para quien reservó."""
    return get_object_or_404(Cita, pk=pk, cliente=request.user)


def citas_visibles(usuario):
    """Cada rol ve únicamente las citas que le corresponden."""
    citas = Cita.objects.select_related(
        'cliente', 'oferta__servicio', 'oferta__profesional__usuario',
        'oferta__local',
    )
    if es_admin(usuario):
        return citas
    filtro = Q(cliente=usuario)
    if Profesional.objects.filter(usuario=usuario).exists():
        filtro |= Q(oferta__profesional__usuario=usuario)
    return citas.filter(filtro).distinct()


@login_required
def lista_citas(request):
    return render(request, 'citas/lista.html', {'citas': citas_visibles(request.user)})


@login_required
def crear_cita(request):
    """Reserva una cita; las reglas de negocio viven en services.py."""
    if request.method == 'POST':
        form = CrearCitaForm(request.POST)
        if form.is_valid():
            oferta = form.cleaned_data['oferta']
            inicio = form.cleaned_data['fecha_inicio']
            fin = inicio + timedelta(minutes=oferta.duracion)
            try:
                reservar_cita(request.user, oferta, inicio, fin)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, '¡Cita reservada correctamente!')
                return redirect('citas:lista')
    else:
        form = CrearCitaForm()
    return render(request, 'citas/crear.html', {'form': form})


@login_required
def detalle_cita(request, pk):
    cita = get_object_or_404(citas_visibles(request.user), pk=pk)
    return render(
        request,
        'citas/detalle.html',
        {
            'cita': cita,
            'puede_cambiar': (
                cita.cliente_id == request.user.pk
                and cita.estado in ('PENDIENTE', 'CONFIRMADA')
            ),
        },
    )


@login_required
def editar_cita(request, pk):
    """Reprograma una cita pendiente o confirmada usando services.py."""
    cita = _cita_del_cliente(request, pk)
    if cita.estado not in ('PENDIENTE', 'CONFIRMADA'):
        messages.error(request, 'Esa cita no se puede reprogramar.')
        return redirect('citas:detalle', pk=pk)

    if request.method == 'POST':
        form = ReprogramarCitaForm(request.POST)
        if form.is_valid():
            oferta = form.cleaned_data['oferta']
            inicio = form.cleaned_data['fecha_inicio']
            try:
                reprogramar_cita(cita, oferta=oferta, fecha_inicio=inicio)
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                messages.success(request, 'Cita reprogramada correctamente.')
                return redirect('citas:detalle', pk=pk)
    else:
        form = ReprogramarCitaForm(initial={
            'oferta': cita.oferta_id,
            'fecha_inicio': cita.fecha_inicio,
        })
    return render(request, 'citas/editar.html', {'form': form, 'cita': cita})


@login_required
@require_POST
def cancelar_cita(request, pk):
    """Cancela conservando la cita en el historial (no se borra)."""
    cita = _cita_del_cliente(request, pk)
    try:
        cancelar_cita_servicio(cita)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect('citas:detalle', pk=pk)
    messages.success(request, 'La cita fue cancelada.')
    return redirect('citas:lista')
