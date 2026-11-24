import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calificaciones', '0001_initial'),
        ('locales', '0001_initial'),
        ('profesionales', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='calificacion',
            name='puntuacion',
            field=models.IntegerField(
                help_text='Puntuación de 1 a 5',
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
        migrations.RemoveField(
            model_name='calificacion',
            name='idCliente',
        ),
        migrations.RemoveField(
            model_name='calificacion',
            name='idLocal',
        ),
        migrations.RemoveField(
            model_name='calificacion',
            name='idProfesional',
        ),
        # default de un solo uso: si la tabla está vacía no afecta; si hay
        # filas, se asocia la calificación al usuario 1 y se quita el default.
        migrations.AddField(
            model_name='calificacion',
            name='cliente',
            field=models.ForeignKey(
                db_column='idCliente',
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='calificaciones',
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='calificacion',
            name='local',
            field=models.ForeignKey(
                blank=True,
                db_column='idLocal',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='calificaciones',
                to='locales.local',
            ),
        ),
        migrations.AddField(
            model_name='calificacion',
            name='profesional',
            field=models.ForeignKey(
                blank=True,
                db_column='idProfesional',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='calificaciones',
                to='profesionales.profesional',
            ),
        ),
    ]
