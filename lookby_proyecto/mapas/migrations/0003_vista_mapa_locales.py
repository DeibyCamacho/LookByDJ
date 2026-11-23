from django.db import migrations


SQL_POSTGRES = """
CREATE OR REPLACE VIEW vw_mapa_locales AS
SELECT
    l.id AS "idLocal",
    l.nombre,
    l.direccion,
    l.latitud,
    l.longitud,
    COALESCE(ROUND(AVG(c.puntuacion), 2), 0) AS calificacion
FROM locales_local l
LEFT JOIN calificaciones_calificacion c ON c."idLocal" = l.id
GROUP BY l.id, l.nombre, l.direccion, l.latitud, l.longitud;
"""

SQL_SQLITE = """
CREATE VIEW IF NOT EXISTS vw_mapa_locales AS
SELECT
    l.id AS "idLocal",
    l.nombre,
    l.direccion,
    l.latitud,
    l.longitud,
    COALESCE(ROUND(AVG(c.puntuacion), 2), 0) AS calificacion
FROM locales_local l
LEFT JOIN calificaciones_calificacion c ON c."idLocal" = l.id
GROUP BY l.id, l.nombre, l.direccion, l.latitud, l.longitud;
"""

DROP_SQL = "DROP VIEW IF EXISTS vw_mapa_locales;"


def crear_vista(apps, schema_editor):
    sql = SQL_POSTGRES if schema_editor.connection.vendor == 'postgresql' else SQL_SQLITE
    schema_editor.execute(sql)


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
