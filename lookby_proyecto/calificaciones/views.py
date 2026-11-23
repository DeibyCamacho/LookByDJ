from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import redirect, render

from .forms import CalificacionForm
from .models import Calificacion


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
        form = CalificacionForm(request.POST)
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
                return redirect('calificaciones:lista')
    else:
        form = CalificacionForm()
    return render(request, 'calificaciones/crear.html', {'form': form})
