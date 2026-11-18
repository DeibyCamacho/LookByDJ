from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


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
        if not correo:
            raise ValueError('El correo es obligatorio.')
        correo = self.normalize_email(correo).lower()
        usuario = self.model(correo=correo, **extra)
        usuario.set_password(password)  # guarda el hash, nunca texto plano
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
    """Usuario de LookBy. Inicia sesión con el correo."""

    correo = models.EmailField('correo electrónico', unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
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
