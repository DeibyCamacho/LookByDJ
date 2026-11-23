from django.test import TestCase

from .models import Rol, Usuario


class PermisosTests(TestCase):
    def setUp(self):
        self.admin_rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        self.cliente = Usuario.objects.create_user(
            correo='ana@correo.com', password='clave123', nombre='Ana',
        )

    def test_listados_admin_redirigen_a_quien_no_es_admin(self):
        for url in ('/inventario/', '/pedidos/', '/proveedores/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/usuarios/entrar/', response['Location'])

    def test_cliente_con_rol_admin_puede_ver_inventario(self):
        self.cliente.roles.add(self.admin_rol)
        self.client.force_login(self.cliente)
        response = self.client.get('/inventario/')
        self.assertEqual(response.status_code, 200)
