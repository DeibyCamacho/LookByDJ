from django.test import TestCase
from .models import Catalogo


class CatalogoTests(TestCase):
    def test_lista_catalogos_vacia(self):
        response = self.client.get('/catalogos/')
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(Catalogo.objects.all(), [])
