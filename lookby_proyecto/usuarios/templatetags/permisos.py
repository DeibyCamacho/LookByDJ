from django import template
from usuarios.permisos import es_admin as usuario_es_admin

register = template.Library()


@register.filter(name='es_admin')
def es_admin_filtro(user):
    """Permite ocultar enlaces administrativos en las plantillas.

    Con un visitante anónimo (o sin usuario en el contexto) devuelve False
    en lugar de lanzar AttributeError.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    return bool(usuario_es_admin(user))
