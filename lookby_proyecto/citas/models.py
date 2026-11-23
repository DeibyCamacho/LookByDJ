from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models


class Cita(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    cliente = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='citas_reservadas',
    )
    oferta = models.ForeignKey(
        'servicios.OfertaServicio',
        on_delete=models.PROTECT,
        related_name='citas',
    )

    def clean(self):
        """Valida duración y evita que un profesional tenga citas solapadas."""
        errores = {}
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                errores['fecha_fin'] = 'La hora final debe ser posterior a la inicial.'
            elif self.oferta_id:
                duracion = timedelta(minutes=self.oferta.duracion)
                if self.fecha_fin - self.fecha_inicio != duracion:
                    errores['fecha_fin'] = (
                        f'La duración debe ser exactamente {self.oferta.duracion} minutos.'
                    )
                if self.estado != 'CANCELADA':
                    solapadas = Cita.objects.filter(
                        oferta__profesional=self.oferta.profesional,
                        fecha_inicio__lt=self.fecha_fin,
                        fecha_fin__gt=self.fecha_inicio,
                    ).exclude(estado='CANCELADA')
                    if self.pk:
                        solapadas = solapadas.exclude(pk=self.pk)
                    if solapadas.exists():
                        errores['fecha_inicio'] = (
                            'El profesional ya tiene una cita en ese periodo de tiempo.'
                        )
        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"Cita #{self.id} - {self.oferta.servicio.nombre} ({self.fecha_inicio})"
