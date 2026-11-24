from math import isfinite

from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render

from .models import VwMapaLocales


CAMPOS = ['id_local', 'nombre', 'direccion', 'latitud', 'longitud', 'calificacion']


def _coordenada(valor, limite):
    """Convierte a float o devuelve None si la coordenada no es usable."""
    if valor is None or valor == '':
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not isfinite(numero) or not -limite <= numero <= limite:
        return None
    return numero


def _normalizar(fila):
    """Descarta filas sin coordenadas (evita marcadores en [0, 0])."""
    latitud = _coordenada(fila.get('latitud'), 90)
    longitud = _coordenada(fila.get('longitud'), 180)
    if latitud is None or longitud is None or (latitud == 0 and longitud == 0):
        return None

    calificacion = fila.get('calificacion')
    if calificacion in (None, ''):
        calificacion = None
    else:
        try:
            calificacion = round(float(calificacion), 2)
        except (TypeError, ValueError):
            calificacion = None

    return {
        'id_local': fila.get('id_local'),
        'nombre': fila.get('nombre') or '',
        'direccion': fila.get('direccion') or '',
        'latitud': latitud,
        'longitud': longitud,
        'calificacion': calificacion,
        'sin_calificar': calificacion is None,
    }


def obtener_locales():
    """Lee la vista SQL VW_MAPA_LOCALES; si aún no existe, devuelve una lista vacía."""
    try:
        filas = list(VwMapaLocales.objects.values(*CAMPOS))
    except DatabaseError:
        return []
    normalizados = (_normalizar(fila) for fila in filas)
    return [fila for fila in normalizados if fila is not None]


def lista_mapa(request):
    return render(request, 'mapas/lista.html', {'locales': obtener_locales()})


def api_mapa_locales(request):
    """Endpoint JSON usado por el proveedor de mapas."""
    return JsonResponse({'locales': obtener_locales()})
