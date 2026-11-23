from django.shortcuts import render
from .models import Cita


def lista_citas(request):
    citas = Cita.objects.select_related(
        'cliente', 'oferta__servicio', 'oferta__profesional__usuario'
    )
    if request.user.is_authenticated and not request.user.is_superuser:
        citas = citas.filter(cliente=request.user)
    return render(request, 'citas/lista.html', {'citas': citas})
