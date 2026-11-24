from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .views import obtener_locales


FILAS = [
    {
        'id_local': 1, 'nombre': 'LookBy Centro', 'direccion': 'Calle 1 # 2-3',
        'latitud': Decimal('6.251800'), 'longitud': Decimal('-75.563600'),
        'calificacion': Decimal('4.50'),
    },
    {
        'id_local': 2, 'nombre': 'Sin coordenadas', 'direccion': 'Calle 2',
        'latitud': None, 'longitud': None, 'calificacion': None,
    },
    {
        'id_local': 3, 'nombre': 'Origen', 'direccion': 'Calle 3',
        'latitud': 0, 'longitud': 0, 'calificacion': Decimal('3.00'),
    },
    {
        'id_local': 4, 'nombre': 'Sin nota', 'direccion': 'Calle 4',
        'latitud': Decimal('6.240000'), 'longitud': Decimal('-75.560000'),
        'calificacion': None,
    },
]


class MapaTests(TestCase):
    def test_obtener_locales_omite_coordenadas_nulas_y_origen(self):
        with patch('mapas.views.VwMapaLocales.objects.values', return_value=FILAS):
            locales = obtener_locales()
        self.assertEqual([local['id_local'] for local in locales], [1, 4])
        self.assertIsNone(locales[1]['calificacion'])
        self.assertTrue(locales[1]['sin_calificar'])

    def test_api_devuelve_json_valido_y_omite_coordenadas_nulas(self):
        with patch('mapas.views.VwMapaLocales.objects.values', return_value=FILAS):
            response = self.client.get(reverse('mapas:api_locales'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        datos = response.json()
        self.assertEqual(set(datos), {'locales'})
        self.assertEqual([local['id_local'] for local in datos['locales']], [1, 4])
        for local in datos['locales']:
            self.assertIsInstance(local['latitud'], float)
            self.assertIsInstance(local['longitud'], float)
            self.assertNotEqual((local['latitud'], local['longitud']), (0, 0))
        self.assertIsNone(datos['locales'][1]['calificacion'])

    def test_api_devuelve_lista_vacia_si_la_vista_no_existe(self):
        from django.db.utils import DatabaseError

        with patch(
            'mapas.views.VwMapaLocales.objects.values',
            side_effect=DatabaseError('vw_mapa_locales no existe'),
        ):
            response = self.client.get(reverse('mapas:api_locales'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'locales': []})

    def test_lista_muestra_sin_calificar_cuando_no_hay_nota(self):
        with patch('mapas.views.VwMapaLocales.objects.values', return_value=FILAS):
            response = self.client.get(reverse('mapas:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sin calificar')
        self.assertContains(response, 'LookBy Centro')
