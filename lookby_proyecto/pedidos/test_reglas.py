from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventario.models import InventarioLocal
from locales.models import Local
from productos.models import Producto
from usuarios.models import Usuario

from .models import Pedido
from .services import crear_pedido


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
