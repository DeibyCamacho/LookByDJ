from decimal import Decimal

from django.core.exceptions import ValidationError
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
        # Las escrituras exigen administrar el local; este admin sí lo administra.
        self.local.usuario = self.admin
        self.local.save(update_fields=['usuario'])
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

    def test_form_rechaza_stock_negativo_y_precio_negativo(self):
        form = InventarioForm(self.datos(stock_actual='-1'))
        self.assertFalse(form.is_valid())
        self.assertIn('stock_actual', form.errors)

        form = InventarioForm(self.datos(precio_venta='-1'))
        self.assertFalse(form.is_valid())
        self.assertIn('precio_venta', form.errors)

        # La regla es >= 0: el precio cero es válido (producto gratuito).
        form = InventarioForm(self.datos(precio_venta='0'))
        self.assertTrue(form.is_valid(), form.errors)

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

    def test_modelo_valida_precio_y_tope_de_stock(self):
        item = InventarioLocal(
            local=self.local, producto=self.producto,
            precio_venta=Decimal('0'), stock_actual=100000,
        )
        item.full_clean()  # 0 y 100000 son válidos.

        item.precio_venta = Decimal('-1')
        with self.assertRaises(ValidationError):
            item.full_clean()

        item.precio_venta = Decimal('0')
        item.stock_actual = 100001
        with self.assertRaises(ValidationError):
            item.full_clean()

        form = InventarioForm(self.datos(stock_actual='100001'))
        self.assertFalse(form.is_valid())
        self.assertIn('stock_actual', form.errors)

    def test_admin_de_otro_local_no_puede_gestionar_inventario(self):
        item = InventarioLocal.objects.create(
            local=self.local, producto=self.producto,
            precio_venta=Decimal('10000'), stock_actual=1,
        )
        otro_admin = Usuario.objects.create_user(
            correo='otro-admin@prueba.com', password='clave123', nombre='Otro',
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        otro_admin.roles.add(rol)
        self.otro_local.usuario = otro_admin
        self.otro_local.save(update_fields=['usuario'])
        self.client.force_login(otro_admin)

        self.assertEqual(
            self.client.post(reverse('inventario:crear'), self.datos()).status_code, 403
        )
        self.assertEqual(
            self.client.get(reverse('inventario:editar', args=[item.pk])).status_code, 403
        )
        self.assertEqual(
            self.client.post(reverse('inventario:eliminar', args=[item.pk])).status_code, 403
        )
        self.assertTrue(InventarioLocal.objects.filter(pk=item.pk).exists())

        # El superusuario sí puede gestionar inventario ajeno.
        superusuario = Usuario.objects.create_superuser(
            correo='root@prueba.com', password='clave123', nombre='Root',
        )
        self.client.force_login(superusuario)
        self.assertEqual(
            self.client.get(reverse('inventario:editar', args=[item.pk])).status_code, 200
        )

    def test_lista_inventario_paginada_a_20(self):
        self.client.force_login(self.admin)
        for numero in range(21):
            producto = Producto.objects.create(nombre=f'Extra {numero}')
            InventarioLocal.objects.create(
                local=self.local, producto=producto,
                precio_venta=Decimal('1000'), stock_actual=1,
            )
        primera = self.client.get(reverse('inventario:lista'))
        self.assertEqual(len(primera.context['page_obj'].object_list), 20)
        self.assertTrue(primera.context['page_obj'].has_next())
        segunda = self.client.get(reverse('inventario:lista') + '?page=2')
        self.assertEqual(len(segunda.context['page_obj'].object_list), 1)
