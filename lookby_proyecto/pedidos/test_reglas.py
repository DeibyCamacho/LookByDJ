from decimal import Decimal

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from inventario.models import InventarioLocal
from locales.models import Local
from productos.models import Producto
from usuarios.models import Usuario

from .admin import DetallePedidoInline, PedidoAdmin
from .forms import CrearPedidoForm
from .models import Pedido
from .services import cancelar_pedido, crear_pedido


class CrearPedidoTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cliente@correo.com', password='clave123', nombre='Ana',
        )
        self.local = Local.objects.create(
            nombre='LookBy Centro', direccion='Calle 1 # 2-3', ciudad='Medellín',
        )
        producto = Producto.objects.create(nombre='Champú')
        self.inventario = InventarioLocal.objects.create(
            local=self.local,
            producto=producto,
            precio_venta=Decimal('25.50'),
            stock_actual=10,
        )

    def test_calcula_total_y_descuenta_stock(self):
        pedido = crear_pedido(
            self.cliente,
            self.local,
            direccion_entrega='Calle 5 # 6-7',
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 3}],
        )
        self.assertEqual(pedido.total, Decimal('76.50'))
        self.assertEqual(pedido.estado, 'CONFIRMADO')
        self.assertEqual(pedido.detalles.count(), 1)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 7)

    def test_rechaza_pedido_sin_stock_suficiente(self):
        with self.assertRaises(ValidationError):
            crear_pedido(
                self.cliente,
                self.local,
                items=[{'inventario_id': self.inventario.pk, 'cantidad': 99}],
            )
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 10)

    def test_rechaza_pedido_vacio(self):
        with self.assertRaises(ValidationError):
            crear_pedido(self.cliente, self.local, items=[])

    def test_formulario_web_crea_pedido(self):
        self.client.force_login(self.cliente)
        response = self.client.post('/pedidos/crear/', {
            'local': self.local.pk,
            'inventario': self.inventario.pk,
            'cantidad': 2,
            'direccion_entrega': 'Calle 5 # 6-7',
        })
        self.assertRedirects(response, '/pedidos/', fetch_redirect_response=False)
        self.assertEqual(Pedido.objects.count(), 1)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 8)

    def _inventario_de_otro_local(self):
        otro_local = Local.objects.create(
            nombre='LookBy Norte', direccion='Calle 9 # 1-2', ciudad='Medellín',
        )
        producto = Producto.objects.create(nombre='Acondicionador')
        return InventarioLocal.objects.create(
            local=otro_local,
            producto=producto,
            precio_venta=Decimal('30.00'),
            stock_actual=5,
        )

    def test_form_rechaza_inventario_de_otro_local(self):
        otro_inventario = self._inventario_de_otro_local()
        form = CrearPedidoForm({
            'local': self.local.pk,
            'inventario': otro_inventario.pk,
            'cantidad': 1,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('inventario', form.errors)
        self.assertIn('otro local', str(form.errors['inventario']))

    def test_post_con_inventario_de_otro_local_no_da_500(self):
        otro_inventario = self._inventario_de_otro_local()
        self.client.force_login(self.cliente)
        response = self.client.post('/pedidos/crear/', {
            'local': self.local.pk,
            'inventario': otro_inventario.pk,
            'cantidad': 1,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'otro local')
        self.assertEqual(Pedido.objects.count(), 0)

    def test_cliente_ve_solo_sus_pedidos_y_admin_ve_todos(self):
        otro_cliente = Usuario.objects.create_user(
            correo='otro@correo.com', password='clave123', nombre='Luis',
        )
        admin_user = Usuario.objects.create_superuser(
            correo='admin@correo.com', password='clave123', nombre='Admin',
        )
        mio = crear_pedido(
            self.cliente, self.local,
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 1}],
        )
        ajeno = crear_pedido(
            otro_cliente, self.local,
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 1}],
        )

        self.client.force_login(self.cliente)
        respuesta = self.client.get('/pedidos/')
        ids = [pedido.pk for pedido in respuesta.context['pedidos']]
        self.assertEqual(ids, [mio.pk])
        self.assertNotIn(ajeno.pk, ids)

        self.client.force_login(admin_user)
        respuesta = self.client.get('/pedidos/')
        ids = [pedido.pk for pedido in respuesta.context['pedidos']]
        self.assertCountEqual(ids, [mio.pk, ajeno.pk])

    def test_anonimo_es_enviado_al_login(self):
        response = self.client.get('/pedidos/')
        self.assertRedirects(
            response, f"{reverse('usuarios:entrar')}?next=/pedidos/",
            fetch_redirect_response=False,
        )

    def test_admin_no_puede_borrar_pedido_confirmado(self):
        pedido = crear_pedido(
            self.cliente, self.local,
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 2}],
        )
        admin_user = Usuario.objects.create_superuser(
            correo='admin@correo.com', password='clave123', nombre='Admin',
        )
        request = RequestFactory().get('/admin/')
        request.user = admin_user
        self.assertFalse(
            PedidoAdmin(Pedido, admin.site).has_delete_permission(request, pedido)
        )
        self.assertFalse(
            DetallePedidoInline(Pedido, admin.site).has_delete_permission(request, pedido)
        )

        self.client.force_login(admin_user)
        url = reverse('admin:pedidos_pedido_delete', args=[pedido.pk])
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Pedido.objects.filter(pk=pedido.pk).exists())

    def test_admin_puede_cancelar_en_lugar_de_borrar(self):
        pedido = crear_pedido(
            self.cliente, self.local,
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 2}],
        )
        admin_user = Usuario.objects.create_superuser(
            correo='admin@correo.com', password='clave123', nombre='Admin',
        )
        self.client.force_login(admin_user)
        respuesta = self.client.post(
            reverse('admin:pedidos_pedido_changelist'),
            {
                'action': 'cancelar_seleccionados',
                '_selected_action': [str(pedido.pk)],
            },
            follow=True,
        )
        self.assertEqual(respuesta.status_code, 200)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'CANCELADO')
        self.assertTrue(Pedido.objects.filter(pk=pedido.pk).exists())

    def test_detalle_y_cancelacion_web(self):
        pedido = crear_pedido(
            self.cliente, self.local, direccion_entrega='Calle 5 # 6-7',
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 3}],
        )
        otro_cliente = Usuario.objects.create_user(
            correo='otro@correo.com', password='clave123', nombre='Luis',
        )

        self.client.force_login(self.cliente)
        self.assertEqual(
            self.client.get(reverse('pedidos:detalle', args=[pedido.pk])).status_code,
            200,
        )
        self.client.force_login(otro_cliente)
        self.assertEqual(
            self.client.get(reverse('pedidos:detalle', args=[pedido.pk])).status_code,
            404,
        )

        self.client.force_login(self.cliente)
        response = self.client.post(reverse('pedidos:eliminar', args=[pedido.pk]))
        self.assertRedirects(response, '/pedidos/', fetch_redirect_response=False)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, 'CANCELADO')
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 10)

    def test_cancelar_pedido_ya_cancelado_falla(self):
        pedido = crear_pedido(
            self.cliente, self.local,
            items=[{'inventario_id': self.inventario.pk, 'cantidad': 1}],
        )
        cancelar_pedido(pedido)
        with self.assertRaises(ValidationError):
            cancelar_pedido(pedido)
