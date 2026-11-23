from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.permisos import es_admin

from .forms import CrearCitaForm
from .models import Cita
from .services import crear_cita as reservar_cita


def lista_citas(request):
    citas = Cita.objects.select_related(
        'cliente', 'oferta__servicio', 'oferta__profesional__usuario'
    )
    if request.user.is_authenticated and not request.user.is_superuser:
        citas = citas.filter(cliente=request.user)
    return render(request, 'citas/lista.html', {'citas': citas})


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
@require_POST
def cancelar_cita(request, pk):
    """Cancela conservando la cita en el historial (no se borra)."""
    cita = get_object_or_404(Cita, pk=pk)
    if cita.cliente_id != request.user.pk and not es_admin(request.user):
        messages.error(request, 'No puedes cancelar la cita de otra persona.')
        return redirect('citas:lista')
    cita.estado = 'CANCELADA'
    cita.save(update_fields=['estado'])
    messages.success(request, 'La cita fue cancelada.')
    return redirect('citas:lista')
