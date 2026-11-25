from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from .validators import (
    CORREO_MAX,
    NOMBRE_MAX,
    validadores_correo,
    validadores_nombre,
)


# Longitud máxima de los apellidos. El nombre tiene su propio límite (30) según
# la norma de calidad de usuarios; ver usuarios/validators.py.
LONGITUD_MAXIMA_NOMBRE = 40


class Rol(models.Model):
    """Rol de un usuario. Una persona puede tener varios (tabla intermedia)."""

    CLIENTE = 'CLIENTE'
    PROFESIONAL = 'PROFESIONAL'
    ADMINISTRADOR = 'ADMINISTRADOR'

    NOMBRES = [
        (CLIENTE, 'Cliente'),
        (PROFESIONAL, 'Profesional'),
        (ADMINISTRADOR, 'Administrador'),
    ]

    nombre = models.CharField(max_length=20, choices=NOMBRES, unique=True)

    class Meta:
        verbose_name = 'rol'
        verbose_name_plural = 'roles'

    def __str__(self):
        return self.get_nombre_display()


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _crear(self, correo, password, **extra):
        """Crea el usuario y valida la norma de nombres antes de guardarlo.

        ``full_clean()`` hace que la regla también se aplique cuando el alta no
        pasa por un formulario (shell, tests o ``createsuperuser``). Se llama
        después de ``set_password()`` porque el campo ``password`` no admite
        estar vacío y ``full_clean()`` lo validaría como campo obligatorio.

        Raises:
            ValueError: si no se indica correo.
            ValidationError: si ``nombre`` o ``correo`` incumplen la norma.
        """
        if not correo:
            raise ValueError('El correo es obligatorio.')
        correo = self.normalize_email(correo).lower()
        usuario = self.model(correo=correo, **extra)
        usuario.set_password(password)  # guarda el hash, nunca texto plano
        usuario.full_clean()  # aplica la norma de nombres también por ORM/admin
        usuario.save(using=self._db)
        return usuario

    def create_user(self, correo, password=None, **extra):
        extra.setdefault('is_staff', False)
        extra.setdefault('is_superuser', False)
        return self._crear(correo, password, **extra)

    def create_superuser(self, correo, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        if not extra['is_staff'] or not extra['is_superuser']:
            raise ValueError('El superusuario debe tener is_staff e is_superuser.')
        return self._crear(correo, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuario de LookBy. Inicia sesión con el correo.

    ``nombre`` y ``correo`` cumplen la norma de calidad descrita en
    :mod:`usuarios.validators` (3-30 caracteres; nombre con letras y espacios;
    correo con formato y signos permitidos). ``apellido`` conserva el límite
    de 40 caracteres añadido por el equipo.
    """

    correo = models.EmailField(
        'correo electrónico',
        unique=True,
        max_length=CORREO_MAX,
        validators=validadores_correo(),
    )
    nombre = models.CharField(
        max_length=NOMBRE_MAX,
        validators=validadores_nombre(),
    )
    apellido = models.CharField(max_length=LONGITUD_MAXIMA_NOMBRE, blank=True)
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField('activo', default=True)
    is_staff = models.BooleanField('acceso al admin', default=False)
    roles = models.ManyToManyField(Rol, blank=True, related_name='usuarios')

    objects = UsuarioManager()

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.nombre_completo or self.correo

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'.strip()

    def tiene_rol(self, nombre_rol):
        return self.roles.filter(nombre=nombre_rol).exists()

    def agregar_rol(self, nombre_rol):
        rol, _ = Rol.objects.get_or_create(nombre=nombre_rol)
        self.roles.add(rol)
