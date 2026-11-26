import re
from io import StringIO

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from locales.models import Local

from .forms import PerfilForm, RegistroForm, UsuarioAdminForm
from .models import LONGITUD_MAXIMA_NOMBRE, Rol, Usuario
from .templatetags.permisos import es_admin_filtro
from .validators import CORREO_MAX, NOMBRE_MAX

CLAVE = 'Clave-Segura-2026'


def datos_registro(**extra):
    datos = {
        'nombre': 'Ana', 'apellido': 'Pérez', 'correo': 'ana@example.com',
        'telefono': '3001234567', 'password1': CLAVE, 'password2': CLAVE,
    }
    datos.update(extra)
    return datos


class RegistroTests(TestCase):
    def test_registro_crea_usuario_cliente_y_abre_sesion(self):
        r = self.client.post(reverse('usuarios:registro'), datos_registro())
        self.assertRedirects(r, reverse('usuarios:perfil'))
        u = Usuario.objects.get(correo='ana@example.com')
        self.assertTrue(u.tiene_rol('CLIENTE'))
        self.assertNotEqual(u.password, CLAVE)  # guardada como hash
        self.assertTrue(u.check_password(CLAVE))
        self.assertIn('_auth_user_id', self.client.session)

    def test_correo_duplicado_sin_importar_mayusculas(self):
        Usuario.objects.create_user('ana@example.com', CLAVE, nombre='Ana')
        r = self.client.post(reverse('usuarios:registro'), datos_registro(correo='ANA@Example.com'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 1)

    def test_campos_obligatorios(self):
        r = self.client.post(reverse('usuarios:registro'), {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_contrasenas_distintas(self):
        r = self.client.post(reverse('usuarios:registro'), datos_registro(password2='otra'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_contrasena_debil_rechazada(self):
        r = self.client.post(reverse('usuarios:registro'), datos_registro(password1='12345678', password2='12345678'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)


class SesionTests(TestCase):
    def setUp(self):
        self.u = Usuario.objects.create_user('ana@example.com', CLAVE, nombre='Ana')

    def test_login_correcto(self):
        r = self.client.post(reverse('usuarios:entrar'), {'username': 'ana@example.com', 'password': CLAVE})
        self.assertRedirects(r, reverse('usuarios:perfil'))

    def test_login_incorrecto(self):
        r = self.client.post(reverse('usuarios:entrar'), {'username': 'ana@example.com', 'password': 'mal'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_post_cierra_sesion(self):
        self.client.force_login(self.u)
        self.client.post(reverse('usuarios:salir'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_get_no_permitido(self):
        self.client.force_login(self.u)
        self.assertEqual(self.client.get(reverse('usuarios:salir')).status_code, 405)

    def test_perfil_requiere_login(self):
        r = self.client.get(reverse('usuarios:perfil'))
        self.assertRedirects(r, f"{reverse('usuarios:entrar')}?next={reverse('usuarios:perfil')}")

    def test_perfil_actualiza_datos_pero_no_correo(self):
        self.client.force_login(self.u)
        self.client.post(reverse('usuarios:perfil'), {
            'nombre': 'Ana María', 'apellido': 'Gómez', 'telefono': '3001234567',
            'correo': 'otro@example.com',
        })
        self.u.refresh_from_db()
        self.assertEqual(self.u.nombre, 'Ana María')
        self.assertEqual(self.u.correo, 'ana@example.com')

    def test_un_usuario_puede_tener_varios_roles(self):
        self.u.agregar_rol('CLIENTE')
        self.u.agregar_rol('PROFESIONAL')
        self.assertEqual(self.u.roles.count(), 2)


class CuentasCRUDTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            'admin@example.com', CLAVE, nombre='Admin',
        )
        self.admin_por_rol = Usuario.objects.create_user(
            'adminrol@example.com', CLAVE, nombre='Admin por rol',
        )
        self.admin_por_rol.agregar_rol(Rol.ADMINISTRADOR)
        self.cliente = Usuario.objects.create_user(
            'cliente@example.com', CLAVE, nombre='Cliente',
        )
        self.otro = Usuario.objects.create_user(
            'otro@example.com', CLAVE, nombre='Otro',
        )
        self.rol_admin = Rol.objects.get(nombre=Rol.ADMINISTRADOR)

    def test_listado_requiere_login_y_es_admin(self):
        url = reverse('usuarios:lista')
        r = self.client.get(url)
        self.assertRedirects(r, f"{reverse('usuarios:entrar')}?next={url}")

        self.client.force_login(self.cliente)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('usuarios:entrar'), r.url)

        self.client.force_login(self.admin_por_rol)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.cliente.correo)

    def test_detalle_propio_permitido_y_ajeno_prohibido(self):
        self.client.force_login(self.cliente)
        propio = reverse('usuarios:detalle', args=[self.cliente.pk])
        ajeno = reverse('usuarios:detalle', args=[self.otro.pk])
        self.assertEqual(self.client.get(propio).status_code, 200)
        self.assertEqual(self.client.get(ajeno).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(ajeno).status_code, 200)

    def test_edicion_propia_no_permite_asignarse_admin(self):
        self.client.force_login(self.cliente)
        url = reverse('usuarios:editar', args=[self.cliente.pk])
        r = self.client.post(url, {
            'nombre': 'Cliente Nuevo',
            'apellido': 'Pérez',
            'telefono': '3000000000',
            # Campos espurios: un usuario normal no debe poder alterarlos.
            'roles': [self.rol_admin.pk],
            'is_active': '',
            'correo': 'hackeado@example.com',
        })
        self.assertRedirects(r, reverse('usuarios:detalle', args=[self.cliente.pk]))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Cliente Nuevo')
        self.assertEqual(self.cliente.correo, 'cliente@example.com')
        self.assertTrue(self.cliente.is_active)
        self.assertFalse(self.cliente.tiene_rol(Rol.ADMINISTRADOR))

    def test_admin_puede_cambiar_roles_de_otro_usuario(self):
        self.client.force_login(self.admin)
        rol_pro = Rol.objects.get(nombre=Rol.PROFESIONAL)
        url = reverse('usuarios:editar', args=[self.otro.pk])
        r = self.client.post(url, {
            'nombre': 'Otro', 'apellido': 'Pérez', 'telefono': '',
            'correo': self.otro.correo, 'is_active': 'on',
            'roles': [rol_pro.pk],
        })
        self.assertRedirects(r, reverse('usuarios:detalle', args=[self.otro.pk]))
        self.assertTrue(self.otro.tiene_rol(Rol.PROFESIONAL))
        self.assertFalse(self.otro.tiene_rol(Rol.ADMINISTRADOR))

    def test_admin_sin_rol_admin_no_puede_ascenderse_a_si_mismo(self):
        root = Usuario.objects.create_superuser('root2@example.com', CLAVE, nombre='Root')
        self.client.force_login(root)
        url = reverse('usuarios:editar', args=[root.pk])
        r = self.client.post(url, {
            'nombre': 'Root', 'apellido': 'Pérez', 'telefono': '',
            'correo': root.correo, 'is_active': 'on',
            'roles': [self.rol_admin.pk],
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(root.tiene_rol(Rol.ADMINISTRADOR))

    def test_desactivar_respeta_permisos_y_conserva_la_cuenta(self):
        url = reverse('usuarios:desactivar', args=[self.otro.pk])
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.otro.refresh_from_db()
        self.assertTrue(self.otro.is_active)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)
        r = self.client.post(url)
        self.assertRedirects(r, reverse('usuarios:lista'))
        self.otro.refresh_from_db()
        self.assertFalse(self.otro.is_active)
        self.assertTrue(Usuario.objects.filter(pk=self.otro.pk).exists())

    def test_usuario_puede_desactivar_su_propia_cuenta(self):
        self.client.force_login(self.cliente)
        r = self.client.post(
            reverse('usuarios:desactivar', args=[self.cliente.pk])
        )
        self.assertRedirects(r, reverse('locales:lista'))
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.is_active)
        self.assertNotIn('_auth_user_id', self.client.session)


class FiltroPermisosTests(TestCase):
    def test_filtro_es_admin_es_seguro_con_anonimo(self):
        self.assertFalse(es_admin_filtro(AnonymousUser()))
        self.assertFalse(es_admin_filtro(None))

        admin = Usuario.objects.create_superuser(
            'root3@example.com', CLAVE, nombre='Root',
        )
        self.assertTrue(es_admin_filtro(admin))


class CargarDemoTests(TestCase):
    def test_cargar_demo_es_idempotente_y_no_restablece_contraseñas(self):
        call_command('cargar_demo', verbosity=0)
        antes = (Usuario.objects.count(), Rol.objects.count(), Local.objects.count())
        admin = Usuario.objects.get(correo='admin@lookby.com')
        admin.set_password('Contraseña-Nueva-2026')
        admin.save()
        salida = StringIO()
        call_command('cargar_demo', stdout=salida)
        despues = (Usuario.objects.count(), Rol.objects.count(), Local.objects.count())
        self.assertEqual(despues, antes)
        admin.refresh_from_db()
        self.assertTrue(admin.check_password('Contraseña-Nueva-2026'))
        self.assertIn('se respetaron sus contraseñas', salida.getvalue())
        self.assertIn('admin@lookby.com', Usuario.objects.values_list('correo', flat=True))


class LongitudNombresTests(TestCase):
    """Longitud de la norma: nombre y apellido 3-30, correo hasta 30."""

    def test_modelo_tiene_los_limites_de_la_norma(self):
        self.assertEqual(LONGITUD_MAXIMA_NOMBRE, NOMBRE_MAX)
        self.assertEqual(NOMBRE_MAX, 30)
        self.assertEqual(CORREO_MAX, 30)
        limites = {
            'nombre': NOMBRE_MAX,
            'apellido': NOMBRE_MAX,
            'correo': CORREO_MAX,
        }
        for campo, maximo in limites.items():
            with self.subTest(campo=campo):
                self.assertEqual(Usuario._meta.get_field(campo).max_length, maximo)

    def test_registro_guarda_nombre_y_apellido_de_30(self):
        nombre, apellido = 'N' * NOMBRE_MAX, 'A' * NOMBRE_MAX
        respuesta = self.client.post(reverse('usuarios:registro'), datos_registro(
            nombre=nombre, apellido=apellido, correo='largo@example.com',
        ))
        self.assertRedirects(respuesta, reverse('usuarios:perfil'))
        usuario = Usuario.objects.get(correo='largo@example.com')
        self.assertEqual(usuario.nombre, nombre)
        self.assertEqual(usuario.apellido, apellido)

    def test_registro_rechaza_nombre_y_apellido_de_31(self):
        casos = (('nombre', NOMBRE_MAX + 1), ('apellido', NOMBRE_MAX + 1))
        for campo, longitud in casos:
            with self.subTest(campo=campo):
                datos = datos_registro(correo=f'{campo}_largo@example.com')
                datos[campo] = 'X' * longitud
                formulario = RegistroForm(data=datos)
                self.assertFalse(formulario.is_valid())
                self.assertIn(campo, formulario.errors)

    def test_formularios_de_perfil_y_admin_usan_los_mismos_limites(self):
        instancia = Usuario(correo='ejemplo@example.com', nombre='Ejemplo')
        limites = {'nombre': str(NOMBRE_MAX), 'apellido': str(NOMBRE_MAX)}
        for clase in (PerfilForm, UsuarioAdminForm):
            with self.subTest(formulario=clase.__name__):
                formulario = clase(instance=instancia)
                for campo, maximo in limites.items():
                    self.assertEqual(formulario.fields[campo].max_length, int(maximo))
                    self.assertEqual(
                        formulario.fields[campo].widget.attrs['maxlength'], maximo
                    )


class NormaNombresTests(TestCase):
    """Nombre: 3-30 letras/espacios. Correo: 3-30, formato válido, sin signos raros."""

    def registrar(self, **extra):
        return self.client.post(reverse('usuarios:registro'), datos_registro(**extra))

    def test_registro_acepta_nombre_y_correo_dentro_de_la_norma(self):
        respuesta = self.registrar(nombre='Ana María', correo='ana.maria@lookby.com')
        self.assertRedirects(respuesta, reverse('usuarios:perfil'))
        self.assertTrue(Usuario.objects.filter(correo='ana.maria@lookby.com').exists())

    def test_registro_acepta_tildes_y_enie_porque_son_letras(self):
        respuesta = self.registrar(nombre='José Dueño')
        self.assertRedirects(respuesta, reverse('usuarios:perfil'))

    def test_registro_rechaza_numeros_y_caracteres_especiales(self):
        nombres = ('Ana@', 'Ana_1', 'Ana-123', "O'Brien", 'Ana.Maria', 'Juan2')
        for nombre in nombres:
            with self.subTest(nombre=nombre):
                respuesta = self.registrar(nombre=nombre)
                self.assertEqual(respuesta.status_code, 200)
                self.assertContains(respuesta, 'solo puede contener letras y espacios')
        self.assertEqual(Usuario.objects.count(), 0)

    def test_registro_rechaza_nombre_corto_y_largo(self):
        for nombre in ('An', 'A' * (NOMBRE_MAX + 1)):
            with self.subTest(longitud=len(nombre)):
                respuesta = self.registrar(nombre=nombre)
                self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_registro_rechaza_correo_mas_largo_de_30(self):
        respuesta = self.registrar(correo='a' * 20 + '@lookby.com')  # 31 caracteres
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_registro_rechaza_correo_con_signos_no_permitidos(self):
        respuesta = self.registrar(correo='ana#1@lookby.com')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Usuario.objects.count(), 0)

    def test_perfil_no_guarda_un_nombre_que_viola_la_norma(self):
        usuario = Usuario.objects.create_user('ana@example.com', CLAVE, nombre='Ana')
        self.client.force_login(usuario)
        respuesta = self.client.post(reverse('usuarios:perfil'), {
            'nombre': 'Ana@', 'apellido': 'Pérez', 'telefono': '3001234567',
        })
        self.assertEqual(respuesta.status_code, 200)
        usuario.refresh_from_db()
        self.assertEqual(usuario.nombre, 'Ana')

    def test_full_clean_rechaza_nombre_y_correo_invalidos(self):
        usuario = Usuario(correo='ana#1@example.com', nombre='Ana1')
        usuario.set_password(CLAVE)
        with self.assertRaises(ValidationError) as error:
            usuario.full_clean()
        self.assertIn('nombre', error.exception.message_dict)
        self.assertIn('correo', error.exception.message_dict)

    def test_create_user_tambien_aplica_la_norma(self):
        with self.assertRaises(ValidationError) as error:
            Usuario.objects.create_user('ana@example.com', CLAVE, nombre='Ana@')
        self.assertIn('nombre', error.exception.message_dict)


class ApellidoTelefonoTests(TestCase):
    """El apellido usa la misma regla del nombre; el teléfono es digits-only."""

    def test_apellido_acepta_tildes_enie_y_espacios(self):
        for apellido in ('Pérez', 'Muñoz', 'García Gómez'):
            with self.subTest(apellido=apellido):
                formulario = RegistroForm(data=datos_registro(apellido=apellido))
                self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_apellido_rechaza_numeros_signos_vacio_y_largo(self):
        casos = ('Pérez2', '*+?-}{1234', "O'Brien", '', 'A' * (NOMBRE_MAX + 1))
        for apellido in casos:
            with self.subTest(apellido=apellido):
                formulario = RegistroForm(data=datos_registro(apellido=apellido))
                self.assertFalse(formulario.is_valid())
                self.assertIn('apellido', formulario.errors)

    def test_mensaje_de_apellido_habla_del_campo_correcto(self):
        formulario = RegistroForm(data=datos_registro(apellido='Pérez2'))
        self.assertIn('El apellido solo puede contener letras', str(formulario.errors))

    def test_telefono_valido_y_normalizado(self):
        formulario = RegistroForm(data=datos_registro(telefono=' 300 123 4567 '))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        usuario = formulario.save()
        self.assertEqual(usuario.telefono, '300 123 4567')

    def test_telefono_rechaza_letras_corto_y_fijo_colombiano_de_10(self):
        casos = ('hola soyun numero', '300', '6011234567', '3001234567890123456')
        for telefono in casos:
            with self.subTest(telefono=telefono):
                formulario = RegistroForm(data=datos_registro(telefono=telefono))
                self.assertFalse(formulario.is_valid())
                self.assertIn('telefono', formulario.errors)

    def test_modelo_normaliza_al_guardar(self):
        usuario = Usuario.objects.create_user(
            'limpio@example.com', CLAVE, nombre='  Ana   María ',
            apellido='  Pérez  ', telefono='  3001234567  ',
        )
        usuario.refresh_from_db()
        self.assertEqual(usuario.nombre, 'Ana María')
        self.assertEqual(usuario.apellido, 'Pérez')
        self.assertEqual(usuario.telefono, '3001234567')
        self.assertEqual(usuario.nombre_completo, 'Ana María Pérez')


class RecuperacionClaveTests(TestCase):
    """Flujo completo de recuperación con mensaje genérico y token de una hora."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            'ana@example.com', CLAVE, nombre='Ana', apellido='Pérez',
        )

    def test_pedir_enlace_no_revela_si_el_correo_existe(self):
        for correo in ('ana@example.com', 'desconocido@example.com'):
            with self.subTest(correo=correo):
                respuesta = self.client.post(
                    reverse('usuarios:recuperar'), {'email': correo}
                )
                self.assertRedirects(respuesta, reverse('usuarios:recuperar_enviado'))
                self.assertContains(
                    self.client.get(reverse('usuarios:recuperar_enviado')),
                    'Si la cuenta existe',
                )

    def test_enlace_cambia_la_contraseña(self):
        self.client.post(reverse('usuarios:recuperar'), {'email': self.usuario.correo})
        self.assertEqual(len(mail.outbox), 1)
        enlace = re.search(r'/usuarios/recuperar/[^\s]+/', mail.outbox[0].body).group(0)
        # Django redirige a .../set-password/ para no filtrar el token en el
        # referer; seguimos esa redirección antes de enviar la nueva clave.
        respuesta = self.client.get(enlace, follow=True)
        self.assertEqual(respuesta.status_code, 200)
        url_final = respuesta.redirect_chain[-1][0] if respuesta.redirect_chain else enlace
        respuesta = self.client.post(url_final, {
            'new_password1': 'Otra-Clave-Segura-2026',
            'new_password2': 'Otra-Clave-Segura-2026',
        })
        self.assertRedirects(respuesta, reverse('usuarios:recuperar_listo'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Otra-Clave-Segura-2026'))

    def test_cambio_de_contraseña_requiere_login(self):
        url = reverse('usuarios:cambiar_clave')
        self.assertRedirects(
            self.client.get(url), f"{reverse('usuarios:entrar')}?next={url}"
        )
        self.client.force_login(self.usuario)
        respuesta = self.client.post(url, {
            'old_password': CLAVE,
            'new_password1': 'Otra-Clave-Segura-2026',
            'new_password2': 'Otra-Clave-Segura-2026',
        })
        self.assertRedirects(respuesta, reverse('usuarios:cambiar_clave_listo'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('Otra-Clave-Segura-2026'))


class BloqueoLoginTests(TestCase):
    """Cinco intentos fallidos bloquean temporalmente el formulario."""

    def setUp(self):
        cache.clear()
        self.usuario = Usuario.objects.create_user(
            'ana@example.com', CLAVE, nombre='Ana', apellido='Pérez',
        )
        self.url = reverse('usuarios:entrar')

    def tearDown(self):
        cache.clear()

    def test_seisimo_intento_es_redirigido_y_no_entra(self):
        datos = {'username': 'ana@example.com', 'password': 'mal'}
        for _ in range(5):
            self.assertEqual(self.client.post(self.url, datos).status_code, 200)
        respuesta = self.client.post(self.url, {**datos, 'password': CLAVE})
        self.assertRedirects(respuesta, self.url)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_usuario_inactivo_no_revela_su_estado(self):
        self.usuario.is_active = False
        self.usuario.save()
        respuesta = self.client.post(self.url, {
            'username': self.usuario.correo, 'password': CLAVE,
        })
        self.assertContains(respuesta, 'Correo o contraseña incorrectos.')
        self.assertNotContains(respuesta, 'desactivada')
