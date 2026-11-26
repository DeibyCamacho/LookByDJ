"""Vistas de error con el diseño de LookBy (sin trazas ni datos internos)."""

from django.shortcuts import render


def _pagina(request, plantilla, codigo):
    """Renderiza una plantilla de error con el estado HTTP adecuado."""
    return render(request, plantilla, {'codigo': codigo}, status=codigo)


def error_400(request, exception=None):
    """Petición no válida."""
    return _pagina(request, '400.html', 400)


def error_403(request, exception=None):
    """Sin permiso para realizar la acción."""
    return _pagina(request, '403.html', 403)


def error_404(request, exception=None):
    """Página no encontrada."""
    return _pagina(request, '404.html', 404)


def error_413(request, exception=None):
    """La petición envió más información de la permitida."""
    return _pagina(request, '413.html', 413)


def error_500(request):
    """Error interno del servidor."""
    return _pagina(request, '500.html', 500)
