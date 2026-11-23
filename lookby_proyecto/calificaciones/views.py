from django.shortcuts import render
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
