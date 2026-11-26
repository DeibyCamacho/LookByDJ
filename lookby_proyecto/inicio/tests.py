from django.core.exceptions import RequestDataTooBig
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lookby_proyecto.middleware import ManejoPeticionesGrandesMiddleware


class InicioTests(TestCase):
    def test_home_carga(self):
        response = self.client.get(reverse('inicio:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CONECTA CON')
        self.assertContains(response, 'LOOKBY EXPERIENCE')

    def test_pagina_404_es_amigable_y_no_muestra_trazas(self):
        respuesta = self.client.get('/esta-pagina-no-existe/')
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, 'Esta página no existe', status_code=404)
        self.assertNotContains(respuesta, 'Traceback', status_code=404)

    def test_contador_de_caracteres_esta_en_la_base(self):
        respuesta = self.client.get(reverse('inicio:home'))
        self.assertContains(respuesta, 'contador-caracteres')
        self.assertContains(respuesta, 'strict-origin-when-cross-origin')

    def test_login_ofrece_recuperacion_de_clave(self):
        respuesta = self.client.get(reverse('usuarios:entrar'))
        self.assertContains(respuesta, reverse('usuarios:recuperar'))
        self.assertContains(respuesta, '¿Olvidaste tu contraseña?')


class ManejoPeticionesGrandesTests(TestCase):
    """El exceso de tamaño debe dar 413 con diseño propio, sin traceback."""

    def test_request_data_too_big_devuelve_413(self):
        def vista_explosiva(request):
            raise RequestDataTooBig('POST demasiado grande')

        middleware = ManejoPeticionesGrandesMiddleware(vista_explosiva)
        respuesta = middleware(RequestFactory().post('/locales/', {}))
        self.assertEqual(respuesta.status_code, 413)
        self.assertContains(
            respuesta, 'Enviaste más información de la permitida', status_code=413
        )

    def test_peticion_normal_pasa_sin_cambios(self):
        middleware = ManejoPeticionesGrandesMiddleware(
            lambda request: 'respuesta normal'
        )
        self.assertEqual(
            middleware(RequestFactory().get('/')), 'respuesta normal'
        )
