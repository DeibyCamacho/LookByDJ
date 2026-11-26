from django.db import models

from usuarios.validators import (
    DESCRIPCION_MAX,
    validador_texto_largo,
    validadores_precio,
)


class Servicio(models.Model):
    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=100)
    descripcion = models.TextField(
        blank=True,
        validators=[validador_texto_largo(DESCRIPCION_MAX)],
        help_text=f'Describe el servicio en {DESCRIPCION_MAX} caracteres como máximo.',
        error_messages={
            'max_length': f'La descripción no puede superar los {DESCRIPCION_MAX} caracteres.',
        },
    )

    def __str__(self):
        return self.nombre


class OfertaServicio(models.Model):
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=validadores_precio(),
        help_text='Precio en pesos colombianos. Puede ser 0 (servicio gratuito); máximo 2 decimales.',
        error_messages={
            'min_value': 'El precio no puede ser negativo. Usa 0 si el servicio es gratuito.',
            'max_value': 'El precio supera el máximo permitido.',
            'max_digits': 'El precio tiene demasiados dígitos.',
            'decimal_places': 'El precio admite máximo 2 decimales.',
        },
    )
    duracion = models.IntegerField(help_text="Duración en minutos")
    activa = models.BooleanField(default=True)
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='ofertas'
    )
    profesional = models.ForeignKey(
        'profesionales.Profesional',
        on_delete=models.CASCADE,
        related_name='ofertas'
    )
    local = models.ForeignKey(
        'locales.Local',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ofertas'
    )

    def __str__(self):
        return f"{self.servicio.nombre} por {self.profesional} (${self.precio})"