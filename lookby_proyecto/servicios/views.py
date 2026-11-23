from django.shortcuts import render
from .models import Servicio, OfertaServicio


def lista_servicios(request):
    servicios = Servicio.objects.all()
    ofertas = OfertaServicio.objects.select_related(
        'servicio', 'profesional__usuario', 'local'
    ).filter(activa=True)
    return render(
        request,
        'servicios/lista.html',
        {'servicios': servicios, 'ofertas': ofertas},
    )
