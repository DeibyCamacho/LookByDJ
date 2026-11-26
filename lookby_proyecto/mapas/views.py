"""Vistas del mapa público de locales.

Un fallo de la vista SQL se registra en el log de la aplicación, pero nunca se
muestra al visitante: la plantilla distingue entre "sin datos" y "fallo al
cargar" mediante un estado, y el JSON público conserva su forma original.
"""

import logging
from math import isfinite

from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.shortcuts import render

from .models import VwMapaLocales

logger = logging.getLogger('lookby')

CAMPOS = ['id_local', 'nombre', 'direccion', 'latitud', 'longitud', 'calificacion']

ESTADO_OK = 'ok'
ESTADO_SIN_DATOS = 'sin_datos'
ESTADO_FALLO = 'fallo'


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


def leer_locales():
    """Devuelve ``(locales, estado)`` sin filtrar errores en silencio.

    El estado es ``ok``, ``sin_datos`` o ``fallo``. El detalle del error solo
    va al log del servidor; la respuesta no incluye trazas ni mensajes de BD.
    """
    try:
        filas = list(VwMapaLocales.objects.values(*CAMPOS))
    except DatabaseError as exc:
        logger.error('No se pudo consultar VW_MAPA_LOCALES: %s', exc)
        return [], ESTADO_FALLO

    normalizados = (_normalizar(fila) for fila in filas)
    locales = [fila for fila in normalizados if fila is not None]
    estado = ESTADO_SIN_DATOS if not locales else ESTADO_OK
    return locales, estado


def obtener_locales():
    """Devuelve solo la lista de locales (API compatible con código existente)."""
    return leer_locales()[0]


def lista_mapa(request):
    locales, estado = leer_locales()
    return render(request, 'mapas/lista.html', {
        'locales': locales,
        'estado_mapa': estado,
        'sin_datos_mapa': estado == ESTADO_SIN_DATOS,
        'fallo_mapa': estado == ESTADO_FALLO,
    })


def api_mapa_locales(request):
    """Endpoint JSON usado por el proveedor de mapas (acceso público)."""
    return JsonResponse({'locales': obtener_locales()})
