from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from calificaciones.models import Calificacion
from citas.models import Cita
from citas.services import crear_cita
from inventario.models import InventarioLocal
from locales.models import Local
from pedidos.models import Pedido
from pedidos.services import crear_pedido
from productos.models import Producto
from profesionales.models import Profesional
from proveedores.models import Proveedor, ProveedorProducto
from servicios.models import OfertaServicio, Servicio
from usuarios.models import Rol, Usuario


# Contraseña SOLO para datos de desarrollo. No usar en producción.
CLAVE_DEMO = 'demo1234'


class Command(BaseCommand):
    help = 'Carga datos de ejemplo para probar LookBy (se puede repetir).'

    def handle(self, *args, **options):
        roles = {}
        for nombre, _ in Rol.NOMBRES:
            roles[nombre], _ = Rol.objects.get_or_create(nombre=nombre)

        admin = self.crear_usuario(
            'admin@lookby.com', 'Admin', roles['ADMINISTRADOR'],
            is_staff=True, is_superuser=True,
        )
        cliente = self.crear_usuario(
            'ana@lookby.com', 'Ana', roles['CLIENTE'],
        )
        pro_usuario = self.crear_usuario(
            'carlos@lookby.com', 'Carlos', roles['PROFESIONAL'],
        )
        profesional, _ = Profesional.objects.get_or_create(
            usuario=pro_usuario,
            defaults={
                'biografia': 'Estilista con 8 años de experiencia.',
                'domicilio': True,
            },
        )

        local, _ = Local.objects.get_or_create(
            nombre='LookBy Centro',
            defaults={
                'descripcion': 'Estudio de belleza y barbería en el centro.',
                'direccion': 'Calle 50 # 43-20',
                'ciudad': 'Medellín',
                'telefono': '3001234567',
                'latitud': Decimal('6.251800'),
                'longitud': Decimal('-75.563600'),
                'usuario': admin,
            },
        )
        local.administradores.add(admin)

        ofertas = []
        datos_servicios = [
            ('Corte de cabello', 'Peluquería', 60, Decimal('50000')),
            ('Coloración', 'Peluquería', 120, Decimal('120000')),
            ('Arreglo de barba', 'Barbería', 30, Decimal('25000')),
        ]
        for nombre, categoria, duracion, precio in datos_servicios:
            servicio, _ = Servicio.objects.get_or_create(
                nombre=nombre,
                defaults={'categoria': categoria, 'descripcion': f'Servicio de {nombre.lower()}.'},
            )
            oferta, _ = OfertaServicio.objects.get_or_create(
                servicio=servicio, profesional=profesional, local=local,
                defaults={'duracion': duracion, 'precio': precio, 'activa': True},
            )
            ofertas.append(oferta)

        productos = []
        for nombre, precio, stock in [
            ('Champú', Decimal('25000'), 20),
            ('Cera para barba', Decimal('18000'), 15),
            ('Aceite capilar', Decimal('32000'), 12),
        ]:
            producto, _ = Producto.objects.get_or_create(
                nombre=nombre, defaults={'categoria': 'Cuidado personal'},
            )
            InventarioLocal.objects.get_or_create(
                local=local, producto=producto,
                defaults={'precio_venta': precio, 'stock_actual': stock},
            )
            productos.append(producto)

        proveedor, _ = Proveedor.objects.get_or_create(
            nombre='Distribuidora Belleza',
            defaults={
                'telefono': '3019998888',
                'correo': 'ventas@distribuidorabelleza.com',
            },
        )
        for producto in productos:
            ProveedorProducto.objects.get_or_create(
                idProveedor=proveedor, producto=producto,
                defaults={'precioMayoreo': Decimal('10000')},
            )

        Calificacion.objects.get_or_create(
            cliente=cliente, local=local,
            defaults={
                'puntuacion': 5,
                'comentario': 'Excelente atención y resultados.',
            },
        )

        if not Cita.objects.exists() and ofertas:
            inicio = (timezone.now() + timedelta(days=2)).replace(
                hour=10, minute=0, second=0, microsecond=0,
            )
            crear_cita(
                cliente, ofertas[0], inicio,
                inicio + timedelta(minutes=ofertas[0].duracion),
            )

        if not Pedido.objects.exists():
            inventario = InventarioLocal.objects.filter(
                local=local, stock_actual__gte=2
            ).first()
            if inventario:
                crear_pedido(
                    cliente, local,
                    direccion_entrega='Calle 50 # 43-20',
                    items=[{'inventario_id': inventario.pk, 'cantidad': 2}],
                )

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados.'))
        self.stdout.write(f'  Admin:        admin@lookby.com / {CLAVE_DEMO}')
        self.stdout.write(f'  Cliente:      ana@lookby.com / {CLAVE_DEMO}')
        self.stdout.write(f'  Profesional:  carlos@lookby.com / {CLAVE_DEMO}')

    def crear_usuario(self, correo, nombre, rol, **extra):
        usuario, _ = Usuario.objects.get_or_create(
            correo=correo,
            defaults={'nombre': nombre, **extra},
        )
        usuario.set_password(CLAVE_DEMO)
        usuario.save()
        usuario.roles.add(rol)
        return usuario
