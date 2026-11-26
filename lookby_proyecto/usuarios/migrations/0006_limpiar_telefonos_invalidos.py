"""Complemento de la 0005 para bases donde ya se había aplicado el saneamiento.

La primera versión de la 0005 quitaba letras pero conservaba números cortos
como ``123456``. Este paso los deja vacíos (el campo es opcional) para que no
aparezcan teléfonos inválidos en los listados.
"""

import re

from django.db import migrations

_TELEFONO = re.compile(r'^\+?[0-9]+(?: [0-9]+)*$')


def limpiar_telefonos(apps, schema_editor):
    """Vacia los teléfonos que no cumplen la regla de 7 a 15 dígitos."""
    Usuario = apps.get_model('usuarios', 'Usuario')
    cambios = 0
    for usuario in Usuario.objects.exclude(telefono='').iterator():
        valor = re.sub(r'\s+', ' ', (usuario.telefono or '')).strip()
        digitos = valor.lstrip('+').replace(' ', '')
        valido = (
            bool(valor)
            and bool(_TELEFONO.match(valor))
            and 7 <= len(digitos) <= 15
            and not (len(digitos) == 10 and not digitos.startswith('3'))
        )
        if not valido:
            usuario.telefono = ''
            usuario.save(update_fields=['telefono'])
            cambios += 1


def no_op(apps, schema_editor):
    """No hay forma de recuperar el número original borrado."""


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0005_alter_usuario_apellido_alter_usuario_nombre_and_more'),
    ]

    operations = [
        migrations.RunPython(limpiar_telefonos, no_op),
    ]
