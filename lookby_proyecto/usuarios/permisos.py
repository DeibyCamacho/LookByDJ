from django.contrib.auth.decorators import user_passes_test


def es_admin(usuario):
    """Administradores por rol o superusuarios del Django admin."""
    return usuario.is_authenticated and (
        usuario.is_superuser or usuario.tiene_rol('ADMINISTRADOR')
    )


admin_required = user_passes_test(
    es_admin,
    login_url='usuarios:entrar',
)
