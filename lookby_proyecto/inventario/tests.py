from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from locales.models import Local
from productos.models import Producto
from usuarios.models import Rol, Usuario

from .forms import InventarioForm
from .models import InventarioLocal


class InventarioTests(TestCase):
    def setUp(self):
        self.local = Local.objects.create(
            nombre='Centro', direccion='Calle 1', ciudad='Medellín'
        )
        self.otro_local = Local.objects.create(
            nombre='Norte', direccion='Calle 2', ciudad='Medellín'
        )
        self.producto = Producto.objects.create(nombre='Champú')
        self.admin = Usuario.objects.create_user(
            correo='admin@prueba.com', password='clave123', nombre='Admin'
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        self.admin.roles.add(rol)
        self.cliente = Usuario.objects.create_user(
            correo='cliente@prueba.com', password='clave123', nombre='Cliente'
        )

    def datos(self, **cambios):
        datos = {
            'local': self.local.pk,
            'producto': self.producto.pk,
            'precio_venta': '25000.00',
            'stock_actual': '5',
        }
        datos.update(cambios)
        return datos

    def test_form_rechaza_duplicado_local_producto(self):
        InventarioLocal.objects.create(
            local=self.local, producto=self.producto,
            precio_venta=Decimal('10000'), stock_actual=1,
        )
        form = InventarioForm(self.datos(precio_venta='20000.00'))
        self.assertFalse(form.is_valid())
        self.assertIn('producto', form.errors)
        self.assertIn('Ya existe un registro', str(form.errors))

    def test_mismo_producto_en_otro_local_si_es_valido(self):
        InventarioLocal.objects.create(
            local=self.local, producto=self.producto,
            precio_venta=Decimal('10000'), stock_actual=1,
        )
        form = InventarioForm(self.datos(local=self.otro_local.pk))
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_rechaza_stock_negativo_y_precio_cero(self):
        form = InventarioForm(self.datos(stock_actual='-1'))
        self.assertFalse(form.is_valid())
        self.assertIn('stock_actual', form.errors)

        form = InventarioForm(self.datos(precio_venta='0'))
        self.assertFalse(form.is_valid())
        self.assertIn('precio_venta', form.errors)

    def test_listado_solo_admin(self):
        self.assertIn('/usuarios/entrar/', self.client.get(reverse('inventario:lista'))['Location'])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('inventario:lista')).status_code, 302)

    def test_crud_con_permisos_de_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('inventario:crear'), self.datos())
        self.assertEqual(r.status_code, 302)
        item = InventarioLocal.objects.get(local=self.local, producto=self.producto)
        self.assertEqual(item.precio_venta, Decimal('25000.00'))

        r = self.client.post(
            reverse('inventario:editar', args=[item.pk]),
            self.datos(precio_venta='30000.00', stock_actual='9'),
        )
        self.assertEqual(r.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.stock_actual, 9)

        r = self.client.post(reverse('inventario:eliminar', args=[item.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(InventarioLocal.objects.filter(pk=item.pk).exists())

    def test_url_eliminar_rechaza_catalogos_asociados(self):
        from catalogos.models import Catalogo, CatalogoProducto

        item = InventarioLocal.objects.create(
            local=self.local, producto=self.producto,
            precio_venta=Decimal('10000'), stock_actual=1,
        )
        catalogo = Catalogo.objects.create(nombre='Cat', local=self.local)
        CatalogoProducto.objects.create(catalogo=catalogo, inventario=item)
        self.client.force_login(self.admin)

        r = self.client.post(reverse('inventario:eliminar', args=[item.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(InventarioLocal.objects.filter(pk=item.pk).exists())
