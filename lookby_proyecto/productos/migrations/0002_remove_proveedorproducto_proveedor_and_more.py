from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
    ]

    operations = [
        # Se eliminan los modelos duplicados: la app oficial es `proveedores`.
        # No hacen falta RemoveField individuales; borrar el modelo basta y
        # evita problemas al reconstruir tablas en SQLite.
        migrations.DeleteModel(
            name='ProveedorProducto',
        ),
        migrations.DeleteModel(
            name='Proveedor',
        ),
        migrations.AlterField(
            model_name='producto',
            name='categoria',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='producto',
            name='nombre',
            field=models.CharField(max_length=150),
        ),
    ]
