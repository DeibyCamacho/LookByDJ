from datetime import time, timedelta
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
from profesionales.models import Horario, Profesional
from proveedores.models import Proveedor, ProveedorProducto
from servicios.models import OfertaServicio, Servicio
from usuarios.models import Rol, Usuario


# Contraseña SOLO para datos de desarrollo. No usar en producción.
CLAVE_DEMO = 'demo1234'


class Command(BaseCommand):
    help = 'Carga datos de ejemplo para probar LookBy (se puede repetir).'

    def handle(self, *args, **options):
        self.cuentas_nuevas = 0
        roles = {}
        for nombre, _ in Rol.NOMBRES:
            roles[nombre], _ = Rol.objects.get_or_create(nombre=nombre)

        admin = self.crear_usuario(
            'admin@lookby.com', 'Admin', roles['ADMINISTRADOR'],
            telefono='3001112233', is_staff=True, is_superuser=True,
        )
        cliente = self.crear_usuario(
            'ana@lookby.com', 'Ana', roles['CLIENTE'],
            telefono='3004445566',
        )
        pro_usuario = self.crear_usuario(
            'carlos@lookby.com', 'Carlos', roles['PROFESIONAL'],
            telefono='3007778899',
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

        # El profesional demo necesita horario: crear_cita rechaza reservas
        # fuera de jornada (y antes no había ningún Horario cargado).
        for dia in range(1, 8):
            Horario.objects.get_or_create(
                profesional=profesional,
                local=local,
                dia_semana=dia,
                defaults={'hora_inicio': time(8, 0), 'hora_fin': time(20, 0)},
            )

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

        self.stdout.write(self.style.SUCCESS('Datos de ejemplo cargados (comando idempotente).'))
        if self.cuentas_nuevas:
            self.stdout.write(
                'Credenciales iniciales (SOLO desarrollo; cambia la contraseña '
                f'antes de usar la app en producción): {CLAVE_DEMO}'
            )
        else:
            self.stdout.write(
                'Las cuentas demo ya existían: se respetaron sus contraseñas '
                'actuales (el comando nunca las sobrescribe).'
            )

    def crear_usuario(self, correo, nombre, rol, **extra):
        """Crea la cuenta demo una sola vez y nunca le cambia la contraseña.

        Ejecutar ``cargar_demo`` al arrancar no debe devolverle a nadie la
        contraseña pública ``demo1234`` si ya la cambió (hallazgo A2).
        """
        defaults = {'nombre': nombre, 'apellido': 'Demo', **extra}
        usuario, creado = Usuario.objects.get_or_create(
            correo=correo, defaults=defaults,
        )
        if creado:
            self.cuentas_nuevas += 1
            usuario.set_password(CLAVE_DEMO)
            usuario.full_clean()
            usuario.save()
        usuario.roles.add(rol)  # M2M: repetir el comando no duplica roles.
        return usuario
