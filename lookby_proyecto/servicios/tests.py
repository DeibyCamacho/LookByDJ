from decimal import Decimal

from django.test import TestCase

from profesionales.models import Profesional
from usuarios.models import Usuario

from .forms import OfertaServicioForm, ServicioForm
from .models import OfertaServicio, Servicio


class CrudServiciosTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cliente@ejemplo.com', password='clave123', nombre='Ana',
        )
        self.pro_usuario = Usuario.objects.create_user(
            correo='pro@ejemplo.com', password='clave123', nombre='Carlos',
        )
        self.profesional = Profesional.objects.create(usuario=self.pro_usuario)
        self.otra_oferta = None
        self.admin = Usuario.objects.create_superuser(
            correo='admin@ejemplo.com', password='clave123', nombre='Admin',
        )
        self.servicio = Servicio.objects.create(
            nombre='Corte', categoria='Peluquería', descripcion='Corte clásico',
        )

    def test_admin_puede_crear_y_editar_servicio(self):
        self.client.force_login(self.admin)
        creacion = self.client.post('/servicios/crear/', {
            'nombre': 'Tinte', 'categoria': 'Color', 'descripcion': 'Tinte profesional',
        })
        self.assertEqual(creacion.status_code, 302)
        servicio = Servicio.objects.get(nombre='Tinte')

        edicion = self.client.post(f'/servicios/{servicio.pk}/editar/', {
            'nombre': 'Tinte premium', 'categoria': 'Color', 'descripcion': 'Mejorado',
        })
        servicio.refresh_from_db()
        self.assertEqual(edicion.status_code, 302)
        self.assertEqual(servicio.nombre, 'Tinte premium')

    def test_cliente_no_puede_crear_servicio(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.get('/servicios/crear/')
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Servicio.objects.count(), 1)

    def test_formulario_servicio_rechaza_nombre_duplicado(self):
        form = ServicioForm(data={'nombre': 'CORTE', 'categoria': 'Peluquería'})
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)

    def test_profesional_crea_y_desactiva_su_oferta(self):
        self.client.force_login(self.pro_usuario)
        creacion = self.client.post('/servicios/ofertas/crear/', {
            'servicio': self.servicio.pk,
            'profesional': self.profesional.pk,
            'precio': '15000',
            'duracion': '45',
            'activa': 'on',
        })
        self.assertEqual(creacion.status_code, 302)
        oferta = OfertaServicio.objects.get()

        desactivacion = self.client.post(f'/servicios/ofertas/{oferta.pk}/eliminar/')
        oferta.refresh_from_db()
        self.assertEqual(desactivacion.status_code, 302)
        self.assertFalse(oferta.activa)
        self.assertTrue(OfertaServicio.objects.filter(pk=oferta.pk).exists())

    def test_cliente_no_puede_editar_oferta_ajena(self):
        oferta = OfertaServicio.objects.create(
            servicio=self.servicio, profesional=self.profesional,
            precio=Decimal('15000'), duracion=45,
        )
        self.client.force_login(self.cliente)
        respuesta = self.client.get(f'/servicios/ofertas/{oferta.pk}/editar/')
        self.assertEqual(respuesta.status_code, 403)

    def test_formulario_oferta_valida_precio_y_duplicados(self):
        form = OfertaServicioForm(data={
            'servicio': self.servicio.pk,
            'profesional': self.profesional.pk,
            'precio': '-1',
            'duracion': '0',
            'activa': 'on',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('precio', form.errors)
        self.assertIn('duracion', form.errors)

        OfertaServicio.objects.create(
            servicio=self.servicio, profesional=self.profesional,
            precio=Decimal('15000'), duracion=45,
        )
        form = OfertaServicioForm(data={
            'servicio': self.servicio.pk,
            'profesional': self.profesional.pk,
            'precio': '15000',
            'duracion': '45',
            'activa': 'on',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('servicio', form.errors)

    def test_listado_incluye_seccion_de_precios(self):
        OfertaServicio.objects.create(
            servicio=self.servicio, profesional=self.profesional,
            precio=Decimal('15000'), duracion=45,
        )
        respuesta = self.client.get('/servicios/')
        contenido = respuesta.content.decode()
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Precios de servicios activos', contenido)
        self.assertIn('15000', contenido)
