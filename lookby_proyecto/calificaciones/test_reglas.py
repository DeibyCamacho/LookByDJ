from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from locales.models import Local
from pedidos.models import Pedido
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

    def test_calificacion_duplicada_rechazada_desde_la_web(self):
        self.client.force_login(self.cliente)
        datos = {
            'local': self.local.pk,
            'puntuacion': 5,
            'comentario': 'Muy buen servicio',
        }
        primera = self.client.post('/calificaciones/crear/', datos)
        self.assertRedirects(primera, '/calificaciones/', fetch_redirect_response=False)
        segunda = self.client.post('/calificaciones/crear/', datos)
        self.assertEqual(segunda.status_code, 200)
        self.assertContains(segunda, 'Ya calificaste')
        self.assertEqual(Calificacion.objects.count(), 1)

    def test_elegibilidad_cuando_hay_citas_o_pedidos_registrados(self):
        Pedido.objects.create(cliente=self.cliente, local=self.local, total=0)
        otro_local = Local.objects.create(
            nombre='LookBy Norte', direccion='Calle 9 # 1-2', ciudad='Medellín',
        )
        self.client.force_login(self.cliente)

        permitida = self.client.post('/calificaciones/crear/', {
            'local': self.local.pk,
            'puntuacion': 4,
            'comentario': 'Compré aquí',
        })
        self.assertRedirects(permitida, '/calificaciones/', fetch_redirect_response=False)

        rechazada = self.client.post('/calificaciones/crear/', {
            'local': otro_local.pk,
            'puntuacion': 4,
            'comentario': 'No he ido',
        })
        self.assertEqual(rechazada.status_code, 200)
        self.assertContains(rechazada, 'cita o un pedido')
        self.assertEqual(Calificacion.objects.count(), 1)

    def test_detalle_edicion_y_eliminacion(self):
        calificacion = self.calificacion(3)
        calificacion.save()
        self.client.force_login(self.cliente)

        detalle = self.client.get(
            reverse('calificaciones:detalle', args=[calificacion.pk])
        )
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, 'Buen servicio')

        edicion = self.client.post(
            reverse('calificaciones:editar', args=[calificacion.pk]),
            {
                'local': self.local.pk,
                'puntuacion': 4,
                'comentario': 'Mejoró el servicio',
            },
        )
        self.assertRedirects(
            edicion,
            reverse('calificaciones:detalle', args=[calificacion.pk]),
            fetch_redirect_response=False,
        )
        calificacion.refresh_from_db()
        self.assertEqual(calificacion.puntuacion, 4)
        self.assertEqual(calificacion.comentario, 'Mejoró el servicio')

        borrado = self.client.post(
            reverse('calificaciones:eliminar', args=[calificacion.pk])
        )
        self.assertRedirects(borrado, '/calificaciones/', fetch_redirect_response=False)
        self.assertFalse(Calificacion.objects.filter(pk=calificacion.pk).exists())

    def test_no_se_puede_editar_calificacion_ajena(self):
        calificacion = self.calificacion(5)
        calificacion.save()
        otro = Usuario.objects.create_user(
            correo='otro@correo.com', password='clave123', nombre='Luis',
        )
        self.client.force_login(otro)
        respuesta = self.client.get(
            reverse('calificaciones:editar', args=[calificacion.pk])
        )
        self.assertEqual(respuesta.status_code, 404)
