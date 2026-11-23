from django import template
from usuarios.permisos import es_admin as usuario_es_admin

register = template.Library()


@register.filter(name='es_admin')
def es_admin_filtro(user):
    """Permite ocultar enlaces administrativos en las plantillas."""
    return usuario_es_admin(user)
