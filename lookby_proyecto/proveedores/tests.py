from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from productos.models import Producto
from usuarios.models import Rol, Usuario

from .forms import ProveedorForm, ProveedorProductoForm
from .models import Proveedor, ProveedorProducto


class ProveedorTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            correo='admin@prueba.com', password='clave123', nombre='Admin'
        )
        rol, _ = Rol.objects.get_or_create(nombre=Rol.ADMINISTRADOR)
        self.admin.roles.add(rol)
        self.cliente = Usuario.objects.create_user(
            correo='cliente@prueba.com', password='clave123', nombre='Cliente'
        )
        self.producto = Producto.objects.create(nombre='Champú')

    def datos(self, **cambios):
        datos = {
            'nombre': 'Distribuidora',
            'telefono': '3019998888',
            'correo': 'ventas@ejemplo.com',
        }
        datos.update(cambios)
        return datos

    def test_form_valida_correo_y_telefono(self):
        self.assertFalse(ProveedorForm(self.datos(correo='no-es-correo')).is_valid())
        self.assertFalse(ProveedorForm(self.datos(telefono='abc')).is_valid())
        self.assertFalse(ProveedorForm(self.datos(telefono='123')).is_valid())
        self.assertTrue(ProveedorForm(self.datos()).is_valid())

    def test_crear_editar_y_eliminar_requiere_admin(self):
        url = reverse('proveedores:crear')
        self.assertIn('/usuarios/entrar/', self.client.get(url)['Location'])
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.post(url, self.datos()).status_code, 302)

        self.client.force_login(self.admin)
        r = self.client.post(url, self.datos())
        self.assertEqual(r.status_code, 302)
        proveedor = Proveedor.objects.get(nombre='Distribuidora')

        r = self.client.post(
            reverse('proveedores:editar', args=[proveedor.pk]),
            self.datos(nombre='Distribuidora 2'),
        )
        self.assertEqual(r.status_code, 302)
        proveedor.refresh_from_db()
        self.assertEqual(proveedor.nombre, 'Distribuidora 2')

    def test_no_borra_proveedor_con_productos_asociados(self):
        proveedor = Proveedor.objects.create(nombre='Proveedor', telefono='3001234567',
                                             correo='a@b.com')
        ProveedorProducto.objects.create(
            idProveedor=proveedor, producto=self.producto,
            precioMayoreo=Decimal('10000'),
        )
        self.client.force_login(self.admin)

        r = self.client.post(reverse('proveedores:eliminar', args=[proveedor.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Proveedor.objects.filter(pk=proveedor.pk).exists())

        suministro = proveedor.productos_suministrados.first()
        r = self.client.post(reverse(
            'proveedores:suministro_eliminar', args=[proveedor.pk, suministro.pk]
        ))
        self.assertEqual(r.status_code, 302)
        r = self.client.post(reverse('proveedores:eliminar', args=[proveedor.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Proveedor.objects.filter(pk=proveedor.pk).exists())

    def test_detalle_muestra_productos(self):
        proveedor = Proveedor.objects.create(nombre='Proveedor', telefono='3001234567',
                                             correo='a@b.com')
        ProveedorProducto.objects.create(
            idProveedor=proveedor, producto=self.producto,
            precioMayoreo=Decimal('10000'),
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse('proveedores:detalle', args=[proveedor.pk]))
        self.assertContains(response, 'Champú')
        self.assertContains(response, '10000,00')

    def test_correo_invalido_en_formulario_y_modelo(self):
        self.assertFalse(ProveedorForm(self.datos(correo='no-es-correo')).is_valid())
        self.assertFalse(ProveedorForm(self.datos(correo='x' * 140 + '@ejemplo.com')).is_valid())

        proveedor = Proveedor(
            nombre='Proveedor', telefono='3001234567', correo='correo-raro'
        )
        with self.assertRaises(ValidationError):
            proveedor.full_clean()

        proveedor.correo = 'ventas@ejemplo.com'
        proveedor.full_clean()

    def test_precio_mayoreo_cero_valido_y_negativo_rechazado(self):
        datos = {
            'idProveedor': Proveedor.objects.create(
                nombre='Proveedor', telefono='3001234567', correo='a@b.com'
            ).pk,
            'producto': self.producto.pk,
        }
        form = ProveedorProductoForm({**datos, 'precioMayoreo': '0'})
        self.assertTrue(form.is_valid(), form.errors)

        form = ProveedorProductoForm({**datos, 'precioMayoreo': '-1'})
        self.assertFalse(form.is_valid())
        self.assertIn('precioMayoreo', form.errors)

        vinculo = ProveedorProducto(
            idProveedor_id=datos['idProveedor'], producto=self.producto,
            precioMayoreo=Decimal('-1'),
        )
        with self.assertRaises(ValidationError):
            vinculo.full_clean()

    def test_lista_proveedores_paginada_a_20(self):
        self.client.force_login(self.admin)
        for numero in range(21):
            Proveedor.objects.create(
                nombre=f'Proveedor {numero}', telefono='3001234567',
                correo=f'proveedor{numero}@ejemplo.com',
            )
        primera = self.client.get(reverse('proveedores:lista'))
        self.assertEqual(len(primera.context['page_obj'].object_list), 20)
        segunda = self.client.get(reverse('proveedores:lista') + '?page=2')
        self.assertEqual(len(segunda.context['page_obj'].object_list), 1)
