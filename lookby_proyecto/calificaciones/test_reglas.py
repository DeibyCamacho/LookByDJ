from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from locales.models import Local
from usuarios.models import Usuario

from .models import Calificacion


class CalificacionTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cliente@correo.com', password='clave123', nombre='Ana',
        )
        self.local = Local.objects.create(
            nombre='LookBy Centro', direccion='Calle 1 # 2-3', ciudad='Medellín',
        )

    def calificacion(self, puntuacion):
        return Calificacion(
            cliente=self.cliente,
            local=self.local,
            puntuacion=puntuacion,
            comentario='Buen servicio',
        )

    def test_rechaza_puntuacion_fuera_de_rango(self):
        for puntuacion in (0, 6):
            with self.subTest(puntuacion=puntuacion):
                with self.assertRaises(ValidationError):
                    self.calificacion(puntuacion).full_clean()

    def test_rechaza_calificacion_sin_local_ni_profesional(self):
        calificacion = Calificacion(
            cliente=self.cliente, puntuacion=5, comentario='Sin objetivo',
        )
        with self.assertRaises(ValidationError):
            calificacion.full_clean()

    def test_evita_calificacion_duplicada_del_mismo_cliente_al_local(self):
        self.calificacion(5).save()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.calificacion(4).save()

    def test_formulario_web_crea_calificacion(self):
        self.client.force_login(self.cliente)
        response = self.client.post('/calificaciones/crear/', {
            'local': self.local.pk,
            'puntuacion': 5,
            'comentario': 'Muy buen servicio',
        })
        self.assertRedirects(response, '/calificaciones/')
        self.assertEqual(Calificacion.objects.count(), 1)

    def test_formulario_rechaza_sin_local_ni_profesional(self):
        self.client.force_login(self.cliente)
        response = self.client.post('/calificaciones/crear/', {
            'puntuacion': 5,
            'comentario': 'Sin objetivo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'solo uno')
