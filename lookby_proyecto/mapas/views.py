from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render
from .models import VwMapaLocales


CAMPOS = ['id_local', 'nombre', 'direccion', 'latitud', 'longitud', 'calificacion']


def obtener_locales():
    """Lee la vista SQL VW_MAPA_LOCALES; si aún no existe, devuelve una lista vacía."""
    try:
        return list(VwMapaLocales.objects.values(*CAMPOS))
    except DatabaseError:
        return []


def lista_mapa(request):
    return render(request, 'mapas/lista.html', {'locales': obtener_locales()})


def api_mapa_locales(request):
    """Endpoint JSON usado por el proveedor de mapas."""
    return JsonResponse({'locales': obtener_locales()})
