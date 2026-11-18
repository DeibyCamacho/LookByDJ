from django.test import TestCase
from django.urls import reverse

from .models import Usuario

CLAVE = 'Clave-Segura-2026'


def datos_registro(**extra):
    datos = {
        'nombre': 'Ana', 'apellido': 'Pérez', 'correo': 'ana@example.com',
        'telefono': '3001234567', 'password1': CLAVE, 'password2': CLAVE,
    }
    datos.update(extra)
    return datos


class RegistroTests(TestCase):
    def test_registro_crea_usuario_cliente_y_abre_sesion(self):
        r = self.client.post(reverse('usuarios:registro'), datos_registro())
        self.assertRedirects(r, reverse('usuarios:perfil'))
        u = Usuario.objects.get(correo='ana@example.com')
        self.assertTrue(u.tiene_rol('CLIENTE'))
        self.assertNotEqual(u.password, CLAVE)  # guardada como hash
        self.assertTrue(u.check_password(CLAVE))
        self.assertIn('_auth_user_id', self.client.session)

    def test_correo_duplicado_sin_importar_mayusculas(self):
        Usuario.objects.create_user('ana@example.com', CLAVE, nombre='Ana')
        r = self.client.post(reverse('usuarios:registro'), datos_registro(correo='ANA@Example.com'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_campos_obligatorios(self):
        r = self.client.post(reverse('usuarios:registro'), {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_contrasenas_distintas(self):
        r = self.client.post(reverse('usuarios:registro'), datos_registro(password2='otra'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_contrasena_debil_rechazada(self):
        r = self.client.post(reverse('usuarios:registro'), datos_registro(password1='12345678', password2='12345678'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)


class SesionTests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user('ana@example.com', CLAVE, nombre='Ana')

    def test_login_correcto(self):
        r = self.client.post(reverse('usuarios:entrar'), {'username': 'ana@example.com', 'password': CLAVE})
        self.assertRedirects(r, reverse('usuarios:perfil'))

    def test_login_incorrecto(self):
        r = self.client.post(reverse('usuarios:entrar'), {'username': 'ana@example.com', 'password': 'mal'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_post_cierra_sesion(self):
        self.client.force_login(self.u)
        self.client.post(reverse('usuarios:salir'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_get_no_permitido(self):
        self.client.force_login(self.u)
        self.assertEqual(self.client.get(reverse('usuarios:salir')).status_code, 405)

    def test_perfil_requiere_login(self):
        r = self.client.get(reverse('usuarios:perfil'))
        self.assertRedirects(r, f"{reverse('usuarios:entrar')}?next={reverse('usuarios:perfil')}")

    def test_perfil_actualiza_datos_pero_no_correo(self):
        self.client.force_login(self.u)
        self.client.post(reverse('usuarios:perfil'), {
            'nombre': 'Ana María', 'apellido': 'Gómez', 'telefono': '300',
            'correo': 'otro@example.com',
        })
        self.u.refresh_from_db()
        self.assertEqual(self.u.nombre, 'Ana María')
        self.assertEqual(self.u.correo, 'ana@example.com')

    def test_un_usuario_puede_tener_varios_roles(self):
        self.u.agregar_rol('CLIENTE')
        self.u.agregar_rol('PROFESIONAL')
        self.assertEqual(self.u.roles.count(), 2)
