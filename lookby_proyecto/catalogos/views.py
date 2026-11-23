from django.shortcuts import render
from .models import Catalogo


def lista_catalogos(request):
    catalogos = Catalogo.objects.select_related('local').all()
    return render(request, 'catalogos/lista_catalogos.html', {'catalogos': catalogos})
