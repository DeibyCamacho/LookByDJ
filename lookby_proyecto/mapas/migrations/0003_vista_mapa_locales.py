from django.db import migrations


SQL_POSTGRES = """
CREATE OR REPLACE VIEW vw_mapa_locales AS
SELECT
    l.id AS "idLocal",
    l.nombre,
    l.direccion,
    l.latitud,
    l.longitud,
    ROUND(AVG(c.puntuacion), 2) AS calificacion
FROM locales_local l
LEFT JOIN calificaciones_calificacion c ON c."idLocal" = l.id
WHERE l."activo" = TRUE AND l."latitud" IS NOT NULL AND l."longitud" IS NOT NULL
GROUP BY l.id, l.nombre, l.direccion, l.latitud, l.longitud;
"""

SQL_SQLITE = (
"DROP VIEW IF EXISTS vw_mapa_locales;",
"""
CREATE VIEW vw_mapa_locales AS
SELECT
    l.id AS "idLocal",
    l.nombre,
    l.direccion,
    l.latitud,
    l.longitud,
    ROUND(AVG(c.puntuacion), 2) AS calificacion
FROM locales_local l
LEFT JOIN calificaciones_calificacion c ON c."idLocal" = l.id
WHERE l."activo" = 1 AND l."latitud" IS NOT NULL AND l."longitud" IS NOT NULL
GROUP BY l.id, l.nombre, l.direccion, l.latitud, l.longitud;
""",
)

DROP_SQL = "DROP VIEW IF EXISTS vw_mapa_locales;"


def crear_vista(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        sentencias = (SQL_POSTGRES,)
    else:
        # SQLite no admite varias sentencias en una sola execute().
        sentencias = SQL_SQLITE
    for sentencia in sentencias:
        schema_editor.execute(sentencia)


def borrar_vista(apps, schema_editor):
    schema_editor.execute(DROP_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('locales', '0003_local_usuario'),
        ('calificaciones', '0003_calificacion_check_puntuacion_1_5_and_more'),
        ('mapas', '0002_vwmapalocales_delete_ubicacion'),
    ]

    operations = [
        migrations.RunPython(crear_vista, borrar_vista),
    ]
