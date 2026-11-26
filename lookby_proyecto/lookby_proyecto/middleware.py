"""Middleware de manejo amable de peticiones demasiado grandes.

Django lanza ``RequestDataTooBig``/``TooManyFieldsSent`` cuando el cuerpo de un
POST supera ``DATA_UPLOAD_MAX_MEMORY_SIZE`` o ``DATA_UPLOAD_MAX_NUMBER_FIELDS``.
Sin este middleware se muestra la página técnica amarilla; con él el usuario ve
la plantilla ``413.html`` con el diseño de LookBy y un botón para volver.
"""

from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent
from django.shortcuts import render


class ManejoPeticionesGrandesMiddleware:
    """Convierte los errores 413 de Django en una respuesta de aplicación."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Deja pasar la petición y captura solo los excesos de tamaño."""
        try:
            return self.get_response(request)
        except (RequestDataTooBig, TooManyFieldsSent):
            return render(request, '413.html', status=413)
