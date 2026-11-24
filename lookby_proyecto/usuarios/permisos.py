from django.contrib.auth.decorators import user_passes_test


def es_admin(usuario):
    """Administradores por rol o superusuarios del Django admin.

    También es seguro con ``AnonymousUser`` o ``None`` (por ejemplo cuando se
    usa como filtro de plantilla sin usuario en el contexto).
    """
    if usuario is None or not getattr(usuario, 'is_authenticated', False):
        return False
    return bool(
        getattr(usuario, 'is_superuser', False)
        or (
            hasattr(usuario, 'tiene_rol')
            and usuario.tiene_rol('ADMINISTRADOR')
        )
    )


admin_required = user_passes_test(
    es_admin,
    login_url='usuarios:entrar',
)
