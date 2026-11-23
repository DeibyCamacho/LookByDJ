from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Cita


@transaction.atomic
def crear_cita(cliente, oferta, fecha_inicio, fecha_fin):
    """Crea una reserva validando reglas de horario y duración."""
    if not oferta.activa:
        raise ValidationError('La oferta de servicio no está activa.')

    # Bloquea las citas del profesional mientras se valida el solapamiento.
    list(
        Cita.objects.select_for_update().filter(
            oferta__profesional=oferta.profesional,
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio,
        )
    )

    cita = Cita(
        cliente=cliente,
        oferta=oferta,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        precio=oferta.precio,
    )
    cita.full_clean()
    cita.save()
    return cita
