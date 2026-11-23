from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Calificacion(models.Model):
    idCalificacion = models.AutoField(primary_key=True)
    puntuacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Puntuación de 1 a 5',
    )
    comentario = models.TextField()

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

    def __str__(self):
        return f'Calificación {self.puntuacion} - {self.cliente}'
