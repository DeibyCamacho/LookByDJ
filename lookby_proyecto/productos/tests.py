from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from inventario.models import InventarioLocal
from locales.models import Local
from usuarios.models import Rol, Usuario

from .forms import ProductoForm
from .models import Producto


class _Base(TestCase):
    def setUp(self):
        self.local = Local.objects.create(
            nombre='LookBy Centro', direccion='Calle 1', ciudad='Medellín'
        )
        self.admin = Usuario.objects.create_user(
            correo='admin@prueba.com', password='clave123', nombre='Admin'
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        self.admin.roles.add(rol)
        # Administrador con propiedad sobre el local: puede gestionar el catálogo.
        self.local.administradores.add(self.admin)
        self.cliente = Usuario.objects.create_user(
            correo='cliente@prueba.com', password='clave123', nombre='Cliente'
        )


class ProductoTemplateTests(_Base):
    def test_lista_publica_muestra_precios_del_inventario_y_no_revienta(self):
        producto = Producto.objects.create(nombre='Champú', categoria='Cuidado')
        InventarioLocal.objects.create(
            local=self.local, producto=producto,
            precio_venta=Decimal('25000.00'), stock_actual=8,
        )

        response = self.client.get('/productos/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '25000,00')
        self.assertContains(response, 'LookBy Centro')
        self.assertContains(response, '?producto=')
        self.assertNotContains(response, '[cite:')

    def test_lista_oculta_productos_desactivados(self):
        Producto.objects.create(nombre='Visible')
        Producto.objects.create(nombre='Oculto', activo=False)
        response = self.client.get(reverse('productos:lista'))
        self.assertContains(response, 'Visible')
        self.assertNotContains(response, 'Oculto')


class ProductoCRUDTests(_Base):
    def test_crear_requiere_admin(self):
        datos = {'nombre': 'Cera', 'descripcion': 'Para barba', 'categoria': 'Barbería'}
        url = reverse('productos:crear')

        self.assertIn('/usuarios/entrar/', self.client.get(url)['Location'])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, datos)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Producto.objects.filter(nombre='Cera').exists())

    def test_editar_y_desactivar_en_lugar_de_borrar(self):
        producto = Producto.objects.create(nombre='Aceite')
        self.client.force_login(self.admin)

        r = self.client.post(
            reverse('productos:editar', args=[producto.pk]),
            {'nombre': 'Aceite capilar', 'descripcion': '', 'categoria': 'Capilar',
             'activo': 'on'},
        )
        self.assertEqual(r.status_code, 302)
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Aceite capilar')

        r = self.client.post(reverse('productos:eliminar', args=[producto.pk]))
        self.assertEqual(r.status_code, 302)
        producto.refresh_from_db()
        self.assertFalse(producto.activo)
        self.assertTrue(Producto.objects.filter(pk=producto.pk).exists())

    def test_form_rechaza_nombre_repetido(self):
        Producto.objects.create(nombre='Champú')
        form = ProductoForm({'nombre': '  champú  ', 'descripcion': '', 'categoria': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_descripcion_no_puede_superar_500_caracteres(self):
        form = ProductoForm({
            'nombre': 'Producto largo', 'descripcion': 'x' * 501, 'categoria': '',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

        producto = Producto.objects.create(nombre='Producto largo', descripcion='x' * 501)
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_admin_de_otro_local_no_puede_editar_producto(self):
        producto = Producto.objects.create(nombre='Solo en Centro')
        InventarioLocal.objects.create(
            local=self.local, producto=producto,
            precio_venta=Decimal('1000'), stock_actual=1,
        )
        otro_local = Local.objects.create(
            nombre='Otro local', direccion='Calle 2', ciudad='Bogotá'
        )
        otro_admin = Usuario.objects.create_user(
            correo='otro-admin@prueba.com', password='clave123', nombre='Otro'
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        otro_admin.roles.add(rol)
        otro_local.administradores.add(otro_admin)
        self.client.force_login(otro_admin)

        url = reverse('productos:editar', args=[producto.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {'nombre': 'Cambiado'}).status_code, 403)
        self.assertEqual(
            self.client.post(reverse('productos:eliminar', args=[producto.pk])).status_code,
            403,
        )
        producto.refresh_from_db()
        self.assertEqual(producto.nombre, 'Solo en Centro')
        self.assertTrue(producto.activo)

    def test_lista_productos_paginada_a_20(self):
        for numero in range(21):
            Producto.objects.create(nombre=f'Producto {numero}')

        primera = self.client.get(reverse('productos:lista'))
        self.assertEqual(len(primera.context['page_obj'].object_list), 20)
        segunda = self.client.get(reverse('productos:lista') + '?page=2')
        self.assertEqual(len(segunda.context['page_obj'].object_list), 1)


class ProductoURLTests(_Base):
    def test_urls_namespaced(self):
        producto = Producto.objects.create(nombre='Producto')
        self.assertEqual(reverse('productos:lista'), '/productos/')
        self.assertEqual(reverse('productos:crear'), '/productos/crear/')
        self.assertEqual(reverse('productos:detalle', args=[producto.pk]),
                         f'/productos/{producto.pk}/')
        self.assertEqual(reverse('productos:editar', args=[producto.pk]),
                         f'/productos/{producto.pk}/editar/')
        self.assertEqual(reverse('productos:eliminar', args=[producto.pk]),
                         f'/productos/{producto.pk}/eliminar/')
