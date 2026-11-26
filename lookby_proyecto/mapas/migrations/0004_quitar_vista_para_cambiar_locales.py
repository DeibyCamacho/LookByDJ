"""Quita temporalmente VW_MAPA_LOCALES para poder acortar columnas de Local.

PostgreSQL no permite cambiar el tipo de una columna usada por una vista. La
migración `locales.0005` depende de esta y recrea la vista en `mapas.0005`.
"""

from importlib import import_module

from django.db import migrations


def borrar_vista(apps, schema_editor):
    """Elimina la vista; su definición se restaura justo después."""
    schema_editor.execute('DROP VIEW IF EXISTS vw_mapa_locales;')


def recrear_vista(apps, schema_editor):
    """Reversión: deja la vista como estaba antes del cambio."""
    anterior = import_module('mapas.migrations.0003_vista_mapa_locales')
    anterior.crear_vista(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('mapas', '0003_vista_mapa_locales'),
    ]

    operations = [
        migrations.RunPython(borrar_vista, recrear_vista),
    ]
