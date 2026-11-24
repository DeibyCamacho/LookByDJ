import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
        ('proveedores', '0001_initial'),
    ]

    operations = [
        # Primero se libera el unique_together que apuntaba a nombreProducto.
        migrations.AlterUniqueTogether(
            name='proveedorproducto',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='proveedorproducto',
            name='idProveedor',
            field=models.ForeignKey(
                db_column='idProveedor',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='productos_suministrados',
                to='proveedores.proveedor',
            ),
        ),
        migrations.RemoveField(
            model_name='proveedorproducto',
            name='nombreProducto',
        ),
        migrations.AddField(
            model_name='proveedorproducto',
            name='producto',
            field=models.ForeignKey(
                db_column='idProducto',
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='proveedores',
                to='productos.producto',
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='proveedorproducto',
            unique_together={('idProveedor', 'producto')},
        ),
    ]
