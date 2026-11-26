from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from profesionales.models import Horario, Profesional
from servicios.models import OfertaServicio, Servicio
from usuarios.models import Usuario

from .models import Cita
from .services import crear_cita, reprogramar_cita


class CrearCitaTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cliente@correo.com', password='clave123', nombre='Ana',
        )
        profesional_usuario = Usuario.objects.create_user(
            correo='pro@correo.com', password='clave123', nombre='Carlos',
        )
        self.profesional = Profesional.objects.create(usuario=profesional_usuario)
        servicio = Servicio.objects.create(
            nombre='Corte de cabello', categoria='Peluquería',
        )
        self.oferta = OfertaServicio.objects.create(
            servicio=servicio, profesional=self.profesional,
            duracion=60, precio=50000,
        )
        # Antes las pruebas reservaban sin horario; ahora la regla lo exige,
        # así que se crean horarios válidos para los días usados por la suite.
        for offset in range(1, 8):
            dia = timezone.localdate() + timedelta(days=offset)
            Horario.objects.create(
                profesional=self.profesional,
                dia_semana=dia.isoweekday(),
                hora_inicio=time(9, 0),
                hora_fin=time(12, 0),
            )
        dia = timezone.localdate() + timedelta(days=1)
        self.inicio = timezone.make_aware(datetime.combine(dia, time(10, 0)))
        self.fin = self.inicio + timedelta(minutes=60)

    def test_crea_cita_y_toma_precio_de_la_oferta(self):
        cita = crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        self.assertEqual(cita.precio, self.oferta.precio)
        self.assertEqual(cita.estado, 'PENDIENTE')

    def test_rechaza_citas_solapadas_del_mismo_profesional(self):
        crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        solapada_inicio = self.inicio + timedelta(minutes=30)
        with self.assertRaises(ValidationError):
            crear_cita(
                self.cliente, self.oferta, solapada_inicio,
                solapada_inicio + timedelta(minutes=60),
            )

    def test_rechaza_duracion_incorrecta(self):
        with self.assertRaises(ValidationError):
            crear_cita(
                self.cliente, self.oferta, self.inicio,
                self.inicio + timedelta(minutes=30),
            )

    def test_formulario_web_reserva_cita(self):
        self.client.force_login(self.cliente)
        dia = timezone.localdate() + timedelta(days=3)
        fecha = timezone.make_aware(datetime.combine(dia, time(10, 0)))
        response = self.client.post('/citas/crear/', {
            'oferta': self.oferta.pk,
            'fecha_inicio': fecha.strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertRedirects(response, '/citas/')
        self.assertEqual(Cita.objects.count(), 1)

    def test_rechaza_fecha_pasada(self):
        pasado = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            crear_cita(
                self.cliente, self.oferta, pasado,
                pasado + timedelta(minutes=60),
            )
        self.assertEqual(Cita.objects.count(), 0)

    def test_valida_horario_del_profesional_cuando_existe(self):
        # Se quitan los horarios de la fixture para probar un intervalo concreto.
        self.profesional.horarios.all().delete()
        dia = timezone.localdate() + timedelta(days=3)
        Horario.objects.create(
            profesional=self.profesional,
            dia_semana=dia.isoweekday(),
            hora_inicio=time(9, 0),
            hora_fin=time(11, 0),
        )
        dentro = timezone.make_aware(datetime.combine(dia, time(10, 0)))
        fuera = timezone.make_aware(datetime.combine(dia, time(12, 0)))

        crear_cita(self.cliente, self.oferta, dentro, dentro + timedelta(minutes=60))
        with self.assertRaises(ValidationError):
            crear_cita(self.cliente, self.oferta, fuera, fuera + timedelta(minutes=60))

    def test_reprogramar_cita_actualiza_fechas_y_precio(self):
        cita = crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        nuevo_inicio = self.inicio + timedelta(days=1)
        reprogramar_cita(cita, oferta=self.oferta, fecha_inicio=nuevo_inicio)
        cita.refresh_from_db()
        self.assertEqual(cita.fecha_inicio, nuevo_inicio)
        self.assertEqual(cita.fecha_fin, nuevo_inicio + timedelta(minutes=60))

    def test_rechaza_cita_sin_horario_publicado(self):
        self.profesional.horarios.all().delete()
        with self.assertRaises(ValidationError) as error:
            crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        self.assertIn('horarios', str(error.exception))
        self.assertEqual(Cita.objects.count(), 0)

    def test_rechaza_reprogramacion_sin_horario_publicado(self):
        cita = crear_cita(self.cliente, self.oferta, self.inicio, self.fin)
        self.profesional.horarios.all().delete()
        with self.assertRaises(ValidationError) as error:
            reprogramar_cita(
                cita, oferta=self.oferta,
                fecha_inicio=self.inicio + timedelta(days=1),
            )
        self.assertIn('horarios', str(error.exception))


class PermisosCitasTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cli@correo.com', password='clave123', nombre='Ana',
        )
        self.otro_cliente = Usuario.objects.create_user(
            correo='otro@correo.com', password='clave123', nombre='Luis',
        )
        usuario_pro = Usuario.objects.create_user(
            correo='pro2@correo.com', password='clave123', nombre='Carlos',
        )
        profesional = Profesional.objects.create(usuario=usuario_pro)
        self.usuario_pro = usuario_pro
        self.admin = Usuario.objects.create_superuser(
            correo='admin@correo.com', password='clave123', nombre='Admin',
        )
        servicio = Servicio.objects.create(nombre='Manicura', categoria='Uñas')
        oferta = OfertaServicio.objects.create(
            servicio=servicio, profesional=profesional, duracion=60, precio=20000,
        )
        self.oferta = oferta
        for offset in range(2, 9):
            dia = timezone.localdate() + timedelta(days=offset)
            Horario.objects.create(
                profesional=profesional,
                dia_semana=dia.isoweekday(),
                hora_inicio=time(9, 0),
                hora_fin=time(12, 0),
            )
        dia = timezone.localdate() + timedelta(days=2)
        base = timezone.make_aware(datetime.combine(dia, time(10, 0)))
        self.cita = Cita.objects.create(
            cliente=self.cliente, oferta=oferta,
            fecha_inicio=base, fecha_fin=base + timedelta(minutes=60),
            precio=oferta.precio,
        )
        otra = base + timedelta(days=1)
        self.cita_ajena = Cita.objects.create(
            cliente=self.otro_cliente, oferta=oferta,
            fecha_inicio=otra, fecha_fin=otra + timedelta(minutes=60),
            precio=oferta.precio,
        )

    def test_anonimo_no_ve_citas(self):
        response = self.client.get('/citas/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/usuarios/entrar/', response['Location'])

    def test_cliente_solo_ve_las_suyas(self):
        self.client.force_login(self.cliente)
        response = self.client.get('/citas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['citas']), [self.cita])

    def test_profesional_ve_citas_de_sus_ofertas(self):
        self.client.force_login(self.usuario_pro)
        response = self.client.get('/citas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context['citas']), {self.cita, self.cita_ajena}
        )

    def test_admin_ve_todas_las_citas(self):
        self.client.force_login(self.admin)
        response = self.client.get('/citas/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context['citas']), {self.cita, self.cita_ajena}
        )

    def test_no_se_puede_cancelar_cita_completada(self):
        self.cita.estado = 'COMPLETADA'
        self.cita.save(update_fields=['estado'])
        self.client.force_login(self.cliente)
        response = self.client.post(f'/citas/{self.cita.pk}/cancelar/')
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'COMPLETADA')
        self.assertEqual(response.status_code, 302)

    def test_cliente_puede_reprogramar_su_cita(self):
        self.client.force_login(self.cliente)
        # El widget datetime-local no conserva los segundos y usa la hora local.
        esperado = (self.cita.fecha_inicio + timedelta(days=5)).replace(second=0)
        nueva = timezone.localtime(esperado).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(f'/citas/{self.cita.pk}/editar/', {
            'oferta': self.oferta.pk,
            'fecha_inicio': nueva,
        })
        self.cita.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.cita.fecha_inicio, esperado)

    def test_cliente_no_ve_detalle_de_cita_ajena(self):
        self.client.force_login(self.cliente)
        response = self.client.get(f'/citas/{self.cita_ajena.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_cliente_puede_cancelar_su_cita(self):
        self.client.force_login(self.cliente)
        respuesta = self.client.post(f'/citas/{self.cita.pk}/cancelar/')
        self.assertRedirects(respuesta, '/citas/', fetch_redirect_response=False)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'CANCELADA')

    def test_profesional_no_cancela_cita_ajena(self):
        self.client.force_login(self.usuario_pro)
        respuesta = self.client.post(f'/citas/{self.cita.pk}/cancelar/')
        self.assertEqual(respuesta.status_code, 404)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'PENDIENTE')

    def test_admin_no_cancela_cita_ajena(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(f'/citas/{self.cita.pk}/cancelar/')
        self.assertEqual(respuesta.status_code, 404)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'PENDIENTE')

    def test_profesional_no_reprograma_cita_ajena(self):
        self.client.force_login(self.usuario_pro)
        respuesta = self.client.post(f'/citas/{self.cita.pk}/editar/', {
            'oferta': self.oferta.pk,
            'fecha_inicio': (
                self.cita.fecha_inicio + timedelta(days=3)
            ).strftime('%Y-%m-%dT%H:%M'),
        })
        self.assertEqual(respuesta.status_code, 404)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, 'PENDIENTE')

    def test_profesional_ve_detalle_ajeno_pero_no_botones_de_cambio(self):
        self.client.force_login(self.usuario_pro)
        respuesta = self.client.get(f'/citas/{self.cita.pk}/')
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotContains(respuesta, 'Reprogramar')
