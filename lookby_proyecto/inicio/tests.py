from django.test import TestCase
from django.urls import reverse


class InicioTests(TestCase):
    def test_home_carga(self):
        response = self.client.get(reverse('inicio:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CONECTA CON')
        self.assertContains(response, 'LOOKBY EXPERIENCE')
