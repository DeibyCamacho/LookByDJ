from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from inventario.models import InventarioLocal
from locales.models import Local
from productos.models import Producto
from usuarios.models import Rol, Usuario

from .forms import CatalogoForm, CatalogoProductoForm
from .models import Catalogo, CatalogoProducto


class CatalogoTests(TestCase):
    def test_lista_catalogos_vacia(self):
        response = self.client.get('/catalogos/')
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(Catalogo.objects.all(), [])


class CatalogoCRUDTests(TestCase):
    def setUp(self):
        self.local = Local.objects.create(
            nombre='Centro', direccion='Calle 1', ciudad='Medellín'
        )
        self.otro_local = Local.objects.create(
            nombre='Norte', direccion='Calle 2', ciudad='Bogotá'
        )
        self.admin = Usuario.objects.create_user(
            correo='admin@prueba.com', password='clave123', nombre='Admin'
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        self.admin.roles.add(rol)
        # Dueño del local: las vistas ahora exigen propiedad para escribir.
        self.local.usuario = self.admin
        self.local.save(update_fields=['usuario'])
        self.cliente = Usuario.objects.create_user(
            correo='cliente@prueba.com', password='clave123', nombre='Cliente'
        )
        self.catalogo = Catalogo.objects.create(nombre='Catálogo Centro', local=self.local)

        p1 = Producto.objects.create(nombre='Producto del centro')
        p2 = Producto.objects.create(nombre='Producto del norte')
        self.inv_local = InventarioLocal.objects.create(
            local=self.local, producto=p1,
            precio_venta=Decimal('25000.00'), stock_actual=7,
        )
        self.inv_otro = InventarioLocal.objects.create(
            local=self.otro_local, producto=p2,
            precio_venta=Decimal('99000.00'), stock_actual=3,
        )

    def test_form_solo_ofrece_inventario_del_mismo_local(self):
        form = CatalogoProductoForm(catalogo=self.catalogo)
        self.assertEqual(list(form.fields['inventario'].queryset), [self.inv_local])

        valido = CatalogoProductoForm(
            {'catalogo': self.catalogo.pk, 'inventario': self.inv_local.pk},
            catalogo=self.catalogo,
        )
        self.assertTrue(valido.is_valid(), valido.errors)

        # Sin el filtro del __init__ se ejercita la validación cruzada de clean().
        invalido = CatalogoProductoForm({
            'catalogo': self.catalogo.pk, 'inventario': self.inv_otro.pk,
        })
        self.assertFalse(invalido.is_valid())
        self.assertIn('inventario', invalido.errors)
        self.assertIn('otro local', str(invalido.errors))

    def test_vista_rechaza_inventario_de_otro_local(self):
        self.client.force_login(self.admin)
        url = reverse('catalogos:producto_crear', args=[self.catalogo.pk])

        r = self.client.post(url, {
            'catalogo': self.catalogo.pk, 'inventario': self.inv_otro.pk,
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(CatalogoProducto.objects.exists())

        r = self.client.post(url, {
            'catalogo': self.catalogo.pk, 'inventario': self.inv_local.pk,
        })
        self.assertEqual(r.status_code, 302)
        self.assertEqual(CatalogoProducto.objects.count(), 1)

    def test_detalle_muestra_nombre_stock_y_precio(self):
        CatalogoProducto.objects.create(
            catalogo=self.catalogo, inventario=self.inv_local
        )
        response = self.client.get(
            reverse('catalogos:detalle', args=[self.catalogo.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Producto del centro')
        self.assertContains(response, '25000,00')
        self.assertContains(response, '7')

    def test_crear_editar_y_borrar_catalogo_con_permisos(self):
        url = reverse('catalogos:crear')
        self.assertIn('/usuarios/entrar/', self.client.get(url)['Location'])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.admin)
        r = self.client.post(url, {
            'nombre': 'Nuevo catálogo', 'descripcion': '', 'local': self.local.pk,
        })
        self.assertEqual(r.status_code, 302)
        catalogo = Catalogo.objects.get(nombre='Nuevo catálogo')

        r = self.client.post(
            reverse('catalogos:editar', args=[catalogo.pk]),
            {'nombre': 'Renombrado', 'descripcion': '', 'local': self.local.pk},
        )
        self.assertEqual(r.status_code, 302)
        catalogo.refresh_from_db()
        self.assertEqual(catalogo.nombre, 'Renombrado')

        r = self.client.post(reverse('catalogos:eliminar', args=[catalogo.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Catalogo.objects.filter(pk=catalogo.pk).exists())

    def test_no_borra_catalogo_con_productos(self):
        CatalogoProducto.objects.create(
            catalogo=self.catalogo, inventario=self.inv_local
        )
        self.client.force_login(self.admin)
        r = self.client.post(
            reverse('catalogos:eliminar', args=[self.catalogo.pk])
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Catalogo.objects.filter(pk=self.catalogo.pk).exists())

    def test_descripcion_no_puede_superar_500_caracteres(self):
        form = CatalogoForm({
            'nombre': 'Catálogo extenso', 'descripcion': 'x' * 501,
            'local': self.local.pk,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('descripcion', form.errors)

        self.catalogo.descripcion = 'x' * 501
        with self.assertRaises(ValidationError):
            self.catalogo.full_clean()

    def test_admin_de_otro_local_no_puede_gestionar_catalogo(self):
        otro_admin = Usuario.objects.create_user(
            correo='otro-admin@prueba.com', password='clave123', nombre='Otro',
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        otro_admin.roles.add(rol)
        self.otro_local.usuario = otro_admin
        self.otro_local.save(update_fields=['usuario'])
        self.client.force_login(otro_admin)

        self.assertEqual(
            self.client.post(reverse('catalogos:crear'), {
                'nombre': 'Ajeno', 'descripcion': '', 'local': self.local.pk,
            }).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(reverse('catalogos:editar', args=[self.catalogo.pk])).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse('catalogos:eliminar', args=[self.catalogo.pk])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse('catalogos:producto_crear', args=[self.catalogo.pk])
            ).status_code,
            403,
        )
        self.assertTrue(Catalogo.objects.filter(pk=self.catalogo.pk).exists())

    def test_lista_catalogos_paginada_y_sin_n_plus_one(self):
        for numero in range(21):
            Catalogo.objects.create(
                nombre=f'Catálogo {numero}', local=self.local,
                descripcion='Catálogo de prueba',
            )
        with CaptureQueriesContext(connection) as consultas:
            primera = self.client.get(reverse('catalogos:lista'))
        self.assertEqual(len(primera.context['page_obj'].object_list), 20)
        # Un COUNT por fila daría al menos 20 consultas extra.
        self.assertLess(len(consultas), 15)
        self.assertContains(primera, 'Página 1 de 2')

        segunda = self.client.get(reverse('catalogos:lista') + '?page=2')
        self.assertEqual(len(segunda.context['page_obj'].object_list), 2)
        self.assertEqual(primera.context['catalogos'][0].num_productos, 0)
