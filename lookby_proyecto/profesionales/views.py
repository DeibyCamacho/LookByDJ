from django.shortcuts import render
from .models import Profesional


def lista_profesionales(request):
    profesionales = Profesional.objects.select_related('usuario').all()
    return render(
        request,
        'profesionales/lista.html',
        {'profesionales': profesionales},
    )
