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
        related_name='citas_reservadas'
    )
    oferta = models.ForeignKey(
        'servicios.OfertaServicio',
        on_delete=models.PROTECT,
        related_name='citas'
    )

    def __str__(self):
        return f"Cita #{self.id} - {self.oferta.servicio.nombre} ({self.fecha_inicio})"