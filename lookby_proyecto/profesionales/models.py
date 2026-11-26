from django.db import models

from usuarios.validators import BIOGRAFIA_MAX, validador_texto_largo


class Profesional(models.Model):
    biografia = models.TextField(
        blank=True,
        validators=[validador_texto_largo(BIOGRAFIA_MAX)],
        help_text=f'Cuéntanos brevemente tu experiencia (máximo {BIOGRAFIA_MAX} caracteres).',
        error_messages={
            'max_length': f'La biografía no puede superar los {BIOGRAFIA_MAX} caracteres.',
        },
    )
    domicilio = models.BooleanField(default=False)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    usuario = models.OneToOneField(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='perfil_profesional'
    )

    def __str__(self):
        return f"Profesional: {self.usuario}"


class Horario(models.Model):
    DIAS_SEMANA = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]

    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    profesional = models.ForeignKey(
        Profesional,
        on_delete=models.CASCADE,
        related_name='horarios'
    )
    local = models.ForeignKey(
        'locales.Local',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='horarios'
    )

    def __str__(self):
        return f"{self.profesional} - {self.get_dia_semana_display()} ({self.hora_inicio} a {self.hora_fin})"