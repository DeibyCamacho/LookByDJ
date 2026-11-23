from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from profesionales.models import Profesional
from servicios.models import OfertaServicio, Servicio
from usuarios.models import Usuario

from .models import Cita
from .services import crear_cita


class CrearCitaTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cliente@correo.com', password='clave123', nombre='Ana',
        )
        profesional_usuario = Usuario.objects.create_user(
            correo='pro@correo.com', password='clave123', nombre='Carlos',
        )
        self.profesional = Profesional.objects.create(usuario=profesional_usuario)
        servicio = Servicio.objects.create(
            nombre='Corte de cabello', categoria='Peluquería',
        )
        self.oferta = OfertaServicio.objects.create(
            servicio=servicio, profesional=self.profesional,
            duracion=60, precio=50000,
        )
        self.inicio = timezone.now().replace(microsecond=0) + timedelta(days=1)
        self.fin = self.inicio + timedelta(minutes=60)

    def test_crea_cita_y_toma_precio_de_la_oferta(self):
        cita = crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        self.assertEqual(cita.precio, self.oferta.precio)
        self.assertEqual(cita.estado, 'PENDIENTE')

    def test_rechaza_citas_solapadas_del_mismo_profesional(self):
        crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        solapada_inicio = self.inicio + timedelta(minutes=30)
        with self.assertRaises(ValidationError):
            crear_cita(
                self.cliente, self.oferta, solapada_inicio,
                solapada_inicio + timedelta(minutes=60),
            )

    def test_rechaza_duracion_incorrecta(self):
        with self.assertRaises(ValidationError):
            crear_cita(
                self.cliente, self.oferta, self.inicio,
                self.inicio + timedelta(minutes=30),
            )

    def test_formulario_web_reserva_cita(self):
        self.client.force_login(self.cliente)
        response = self.client.post('/citas/crear/', {
            'oferta': self.oferta.pk,
            'fecha_inicio': '2026-11-26T11:00',
        })
        self.assertRedirects(response, '/citas/')
        self.assertEqual(Cita.objects.count(), 1)
