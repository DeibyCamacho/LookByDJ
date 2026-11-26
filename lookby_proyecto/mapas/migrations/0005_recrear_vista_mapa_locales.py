"""Restaura VW_MAPA_LOCALES después de acortar las columnas de Local."""

from importlib import import_module

from django.db import migrations


def recrear_vista(apps, schema_editor):
    """Usa la misma definición SQL de la migración original 0003."""
    original = import_module('mapas.migrations.0003_vista_mapa_locales')
    original.crear_vista(apps, schema_editor)


def borrar_vista(apps, schema_editor):
    """Quita la vista si se revierte la migración."""
    schema_editor.execute('DROP VIEW IF EXISTS vw_mapa_locales;')


class Migration(migrations.Migration):

    dependencies = [
        ('locales', '0005_alter_local_ciudad_alter_local_descripcion_and_more'),
        ('mapas', '0004_quitar_vista_para_cambiar_locales'),
    ]

    operations = [
        migrations.RunPython(recrear_vista, borrar_vista),
    ]
