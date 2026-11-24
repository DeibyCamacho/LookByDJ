import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('locales', '0001_initial'),
        ('inventario', '0002_conectar_fks'),
        ('pedidos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pedido',
            name='cliente_id',
        ),
        migrations.RemoveField(
            model_name='pedido',
            name='local_id',
        ),
        migrations.AddField(
            model_name='pedido',
            name='cliente',
            field=models.ForeignKey(
                db_column='idCliente',
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pedidos',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pedido',
            name='local',
            field=models.ForeignKey(
                db_column='idLocal',
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='pedidos',
                to='locales.local',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pedido',
            name='direccion_entrega',
            field=models.CharField(blank=True, max_length=255, verbose_name='dirección de entrega'),
        ),
        migrations.RemoveField(
            model_name='detallepedido',
            name='producto',
        ),
        migrations.AddField(
            model_name='detallepedido',
            name='inventario',
            field=models.ForeignKey(
                db_column='idInventario',
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='detalles_pedido',
                to='inventario.inventariolocal',
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='detallepedido',
            name='precio_unitario',
            field=models.DecimalField(
                decimal_places=2,
                help_text='Precio fijado en el momento de la compra',
                max_digits=10,
            ),
        ),
    ]
