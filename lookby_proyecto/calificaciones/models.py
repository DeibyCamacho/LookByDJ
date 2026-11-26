from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from usuarios.validators import COMENTARIO_MAX, validador_texto_largo


class Calificacion(models.Model):
    idCalificacion = models.AutoField(primary_key=True)
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Puntuación de 1 a 5',
    )
    comentario = models.TextField(
        validators=[validador_texto_largo(COMENTARIO_MAX)],
        help_text=f'Máximo {COMENTARIO_MAX} caracteres.',
    )

    # MER: CALIFICACION.idCliente / idLocal / idProfesional como llaves foráneas.
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='calificaciones',
        db_column='idCliente',
    )
    local = models.ForeignKey(
        'locales.Local',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calificaciones',
        db_column='idLocal',
    )
    profesional = models.ForeignKey(
        'profesionales.Profesional',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calificaciones',
        db_column='idProfesional',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(puntuacion__gte=1, puntuacion__lte=5),
                name='check_puntuacion_1_5',
            ),
            models.CheckConstraint(
                condition=Q(local__isnull=False) | Q(profesional__isnull=False),
                name='check_calificacion_con_objetivo',
            ),
            models.UniqueConstraint(
                fields=['cliente', 'local'],
                condition=Q(local__isnull=False),
                name='uniq_calificacion_cliente_local',
            ),
            models.UniqueConstraint(
                fields=['cliente', 'profesional'],
                condition=Q(profesional__isnull=False),
                name='uniq_calificacion_cliente_profesional',
            ),
        ]

    def __str__(self):
        return f'Calificación {self.puntuacion} - {self.cliente}'
