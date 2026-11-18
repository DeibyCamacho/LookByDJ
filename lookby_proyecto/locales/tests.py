from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario

from .models import Local

CLAVE = 'Clave-Segura-2026'


def datos_local(**extra):
    datos = {
        'nombre': 'Salón Luna', 'descripcion': 'Belleza', 'direccion': 'Calle 1 # 2-3',
        'ciudad': 'Bogotá', 'telefono': '', 'latitud': '4.711000', 'longitud': '-74.072100',
    }
    datos.update(extra)
    return datos


class LocalesBase(TestCase):
    def setUp(self):
        self.dueno = Usuario.objects.create_user('dueno@example.com', CLAVE, nombre='Dueño')
        self.otro = Usuario.objects.create_user('otro@example.com', CLAVE, nombre='Otro')
        self.local = Local.objects.create(nombre='Salón Luna', direccion='Calle 1', ciudad='Bogotá')
        self.local.administradores.add(self.dueno)


class CrearLocalTests(LocalesBase):
    def test_crear_requiere_login(self):
        r = self.client.get(reverse('locales:crear'))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('usuarios:entrar'), r.url)

    def test_crear_asigna_administrador_y_rol(self):
        self.client.force_login(self.otro)
        r = self.client.post(reverse('locales:crear'), datos_local(nombre='Nuevo'))
        local = Local.objects.get(nombre='Nuevo')
        self.assertRedirects(r, reverse('locales:detalle', args=[local.pk]))
        self.assertTrue(local.puede_administrar(self.otro))
        self.assertTrue(self.otro.tiene_rol('ADMINISTRADOR'))

    def test_coordenadas_incompletas_rechazadas(self):
        self.client.force_login(self.otro)
        r = self.client.post(reverse('locales:crear'), datos_local(nombre='X', longitud=''))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Local.objects.filter(nombre='X').exists())

    def test_coordenadas_fuera_de_rango_rechazadas(self):
        self.client.force_login(self.otro)
        r = self.client.post(reverse('locales:crear'), datos_local(nombre='X', latitud='95'))
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Local.objects.filter(nombre='X').exists())


class PermisosLocalTests(LocalesBase):
    def test_admin_del_local_puede_editar(self):
        self.client.force_login(self.dueno)
        r = self.client.post(reverse('locales:editar', args=[self.local.pk]), datos_local(nombre='Renombrado'))
        self.assertRedirects(r, reverse('locales:detalle', args=[self.local.pk]))
        self.local.refresh_from_db()
        self.assertEqual(self.local.nombre, 'Renombrado')

    def test_otro_usuario_no_puede_editar_ni_desactivar(self):
        self.client.force_login(self.otro)
        self.assertEqual(self.client.get(reverse('locales:editar', args=[self.local.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('locales:editar', args=[self.local.pk]), datos_local(nombre='Hack')).status_code, 403)
        self.assertEqual(self.client.post(reverse('locales:desactivar', args=[self.local.pk])).status_code, 403)
        self.local.refresh_from_db()
        self.assertEqual(self.local.nombre, 'Salón Luna')
        self.assertTrue(self.local.activo)

    def test_anonimo_redirigido_al_login(self):
        r = self.client.post(reverse('locales:desactivar', args=[self.local.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('usuarios:entrar'), r.url)

    def test_superusuario_puede_administrar(self):
        root = Usuario.objects.create_superuser('root@example.com', CLAVE, nombre='Root')
        self.client.force_login(root)
        self.assertEqual(self.client.get(reverse('locales:editar', args=[self.local.pk])).status_code, 200)


class ListadoYDesactivarTests(LocalesBase):
    def test_lista_publica(self):
        r = self.client.get(reverse('locales:lista'))
        self.assertContains(r, 'Salón Luna')

    def test_filtro_por_ciudad(self):
        Local.objects.create(nombre='Otro', direccion='x', ciudad='Cali')
        r = self.client.get(reverse('locales:lista'), {'ciudad': 'cali'})
        self.assertContains(r, 'Otro')
        self.assertNotContains(r, 'Salón Luna')

    def test_desactivar_oculta_pero_no_borra(self):
        self.client.force_login(self.dueno)
        self.client.post(reverse('locales:desactivar', args=[self.local.pk]))
        self.local.refresh_from_db()
        self.assertFalse(self.local.activo)
        self.client.logout()
        self.assertNotContains(self.client.get(reverse('locales:lista')), 'Salón Luna')
        self.assertEqual(self.client.get(reverse('locales:detalle', args=[self.local.pk])).status_code, 404)

    def test_desactivar_por_get_no_cambia_nada(self):
        self.client.force_login(self.dueno)
        self.client.get(reverse('locales:desactivar', args=[self.local.pk]))
        self.local.refresh_from_db()
        self.assertTrue(self.local.activo)

    def test_admin_ve_local_desactivado(self):
        self.local.activo = False
        self.local.save()
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(reverse('locales:detalle', args=[self.local.pk])).status_code, 200)
