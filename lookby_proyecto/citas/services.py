from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from profesionales.models import Horario, Profesional

from .models import Cita


def _con_zona_horaria(fecha):
    """Los formularios entregan fechas conscientes; se normalizan las demás."""
    if fecha is not None and timezone.is_naive(fecha):
        return timezone.make_aware(fecha, timezone.get_current_timezone())
    return fecha


def _validar_no_pasada(inicio):
    if inicio is not None and inicio < timezone.now():
        raise ValidationError('No se pueden reservar citas en el pasado.')


def _validar_horario(oferta, inicio, fin):
    """La cita debe caer dentro de un horario publicado por el profesional."""
    horarios = Horario.objects.filter(profesional=oferta.profesional)
    if not horarios.exists():
        raise ValidationError(
            'El profesional todavía no tiene horarios publicados. '
            'No se puede reservar hasta que publique su horario de atención.'
        )

    if inicio.date() != fin.date():
        raise ValidationError('La cita debe completarse dentro de un mismo día.')

    candidatos = horarios.filter(dia_semana=inicio.isoweekday())
    if oferta.local_id:
        candidatos = candidatos.filter(
            Q(local__isnull=True) | Q(local_id=oferta.local_id)
        )
    else:
        candidatos = candidatos.filter(local__isnull=True)

    hora_inicio = inicio.time().replace(microsecond=0)
    hora_fin = fin.time().replace(microsecond=0)
    if not candidatos.filter(
        hora_inicio__lte=hora_inicio,
        hora_fin__gte=hora_fin,
    ).exists():
        raise ValidationError(
            'La cita debe estar dentro del horario atendido por el profesional '
            'para ese día y local.'
        )


@transaction.atomic
def crear_cita(cliente, oferta, fecha_inicio, fecha_fin):
    """Crea una reserva validando reglas de negocio y bloqueando al profesional."""
    if not oferta.activa:
        raise ValidationError('La oferta de servicio no está activa.')

    inicio = _con_zona_horaria(fecha_inicio)
    fin = _con_zona_horaria(fecha_fin)
    _validar_no_pasada(inicio)
    if fin is not None and fin <= inicio:
        raise ValidationError('La hora final debe ser posterior a la inicial.')

    # Bloquear al profesional evita dos reservas concurrentes en el mismo hueco.
    Profesional.objects.select_for_update().get(pk=oferta.profesional_id)
    list(
        Cita.objects.select_for_update().filter(
            oferta__profesional_id=oferta.profesional_id,
            fecha_inicio__lt=fin,
            fecha_fin__gt=inicio,
        )
    )

    _validar_horario(oferta, inicio, fin)

    cita = Cita(
        cliente=cliente,
        oferta=oferta,
        fecha_inicio=inicio,
        fecha_fin=fin,
        precio=oferta.precio,
    )
    cita.full_clean()
    cita.save()
    return cita


@transaction.atomic
def reprogramar_cita(cita, oferta=None, fecha_inicio=None):
    """Reprograma una cita existente reutilizando todas las reglas de reserva."""
    if cita.estado in ('CANCELADA', 'COMPLETADA'):
        raise ValidationError('Esa cita ya no se puede reprogramar.')

    oferta = oferta or cita.oferta
    if not oferta.activa:
        raise ValidationError('La oferta de servicio no está activa.')

    inicio = _con_zona_horaria(fecha_inicio or cita.fecha_inicio)
    fin = inicio + timedelta(minutes=oferta.duracion)
    _validar_no_pasada(inicio)

    Profesional.objects.select_for_update().get(pk=oferta.profesional_id)
    Cita.objects.select_for_update().filter(pk=cita.pk).first()
    list(
        Cita.objects.select_for_update()
        .filter(
            oferta__profesional_id=oferta.profesional_id,
            fecha_inicio__lt=fin,
            fecha_fin__gt=inicio,
        )
        .exclude(pk=cita.pk)
    )

    _validar_horario(oferta, inicio, fin)

    cita.oferta = oferta
    cita.fecha_inicio = inicio
    cita.fecha_fin = fin
    cita.precio = oferta.precio
    cita.full_clean()
    cita.save()
    return cita


@transaction.atomic
def cancelar_cita(cita):
    """Cancela conservando el historial, con la fila bloqueada como al reprogramar."""
    cita_bloqueada = Cita.objects.select_for_update().get(pk=cita.pk)
    if cita_bloqueada.estado in ('COMPLETADA', 'CANCELADA'):
        raise ValidationError('Solo se pueden cancelar citas pendientes o confirmadas.')
    cita_bloqueada.estado = 'CANCELADA'
    cita_bloqueada.save(update_fields=['estado'])
    return cita_bloqueada
