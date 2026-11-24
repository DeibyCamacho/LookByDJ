from django.test import TestCase

from usuarios.models import Usuario

from .forms import HorarioForm, ProfesionalForm
from .models import Horario, Profesional


class CrudProfesionalesTests(TestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            correo='cliente@ejemplo.com', password='clave123', nombre='Ana',
        )
        self.pro_usuario = Usuario.objects.create_user(
            correo='pro@ejemplo.com', password='clave123', nombre='Carlos',
        )
        self.profesional = Profesional.objects.create(usuario=self.pro_usuario)
        self.otro_profesional = Profesional.objects.create(
            usuario=Usuario.objects.create_user(
                correo='pro2@ejemplo.com', password='clave123', nombre='Luis',
            )
        )
        self.admin = Usuario.objects.create_superuser(
            correo='admin@ejemplo.com', password='clave123', nombre='Admin',
        )

    def test_admin_puede_crear_profesional(self):
        self.client.force_login(self.admin)
        usuario = Usuario.objects.create_user(
            correo='nuevo@ejemplo.com', password='clave123', nombre='Nuevo',
        )
        response = self.client.post('/profesionales/crear/', {
            'usuario': usuario.pk,
            'biografia': 'Especialista en color',
            'domicilio': 'on',
            'latitud': '4.711111',
            'longitud': '-74.072222',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Profesional.objects.filter(usuario=usuario).exists())

    def test_cliente_no_puede_crear_profesional(self):
        self.client.force_login(self.cliente)
        response = self.client.get('/profesionales/crear/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Profesional.objects.count(), 2)

    def test_profesional_puede_editar_su_perfil_pero_no_ajeno(self):
        self.client.force_login(self.pro_usuario)
        propio = self.client.post(f'/profesionales/{self.profesional.pk}/editar/', {
            'usuario': self.pro_usuario.pk,
            'biografia': 'Actualizada',
        })
        self.profesional.refresh_from_db()
        self.assertEqual(propio.status_code, 302)
        self.assertEqual(self.profesional.biografia, 'Actualizada')

        ajeno = self.client.get(f'/profesionales/{self.otro_profesional.pk}/editar/')
        self.assertEqual(ajeno.status_code, 403)

    def test_formulario_rechaza_coordenadas_incompletas(self):
        form = ProfesionalForm(data={
            'usuario': self.pro_usuario.pk,
            'biografia': 'Bio',
            'latitud': '4.71',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('latitud', form.errors)

    def test_formulario_rechaza_usuario_duplicado(self):
        form = ProfesionalForm(data={'usuario': self.pro_usuario.pk})
        self.assertFalse(form.is_valid())
        self.assertIn('usuario', form.errors)

    def test_lista_muestra_biografia_coordenadas_y_horarios(self):
        Horario.objects.create(
            profesional=self.profesional,
            dia_semana=1,
            hora_inicio='09:00',
            hora_fin='12:00',
        )
        self.profesional.biografia = 'Bio visible'
        self.profesional.latitud = '4.711111'
        self.profesional.longitud = '-74.072222'
        self.profesional.save()

        response = self.client.get('/profesionales/')
        self.assertEqual(response.status_code, 200)
        contenido = response.content.decode()
        self.assertIn('Bio visible', contenido)
        self.assertIn('711111', contenido)
        self.assertIn('09:00', contenido)

    def test_horario_rechaza_solapamiento(self):
        Horario.objects.create(
            profesional=self.profesional,
            dia_semana=1,
            hora_inicio='09:00',
            hora_fin='12:00',
        )
        form = HorarioForm(data={
            'profesional': self.profesional.pk,
            'dia_semana': 1,
            'hora_inicio': '10:00',
            'hora_fin': '11:00',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('hora_inicio', form.errors)

    def test_admin_puede_eliminar_y_profesional_no(self):
        self.client.force_login(self.pro_usuario)
        respuesta = self.client.post(f'/profesionales/{self.otro_profesional.pk}/eliminar/')
        self.assertEqual(respuesta.status_code, 403)

        self.client.force_login(self.admin)
        respuesta = self.client.post(f'/profesionales/{self.otro_profesional.pk}/eliminar/')
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Profesional.objects.filter(pk=self.otro_profesional.pk).exists())
