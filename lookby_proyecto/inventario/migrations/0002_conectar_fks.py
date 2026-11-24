import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
        ('locales', '0001_initial'),
        ('inventario', '0001_initial'),
    ]

    operations = [
        # Primero se libera el unique_together que apuntaba a local_id.
        migrations.AlterUniqueTogether(
            name='inventariolocal',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='inventariolocal',
            name='local_id',
        ),
        migrations.AddField(
            model_name='inventariolocal',
            name='local',
            field=models.ForeignKey(
                db_column='idLocal',
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='inventarios',
                to='locales.local',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='inventariolocal',
            name='producto',
            field=models.ForeignKey(
                db_column='idProducto',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='inventarios',
                to='productos.producto',
            ),
        ),
        migrations.AlterField(
            model_name='inventariolocal',
            name='precio_venta',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='precio de venta'),
        ),
        migrations.AlterField(
            model_name='inventariolocal',
            name='stock_actual',
            field=models.PositiveIntegerField(default=0, verbose_name='stock actual'),
        ),
        migrations.AlterUniqueTogether(
            name='inventariolocal',
            unique_together={('local', 'producto')},
        ),
    ]
