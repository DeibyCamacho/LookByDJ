from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from usuarios.validators import (
    DESCRIPCION_MAX,
    DIRECCION_MAX,
    TELEFONO_MAX,
    normalizar_espacios,
    validador_texto_largo,
    validadores_direccion,
    validadores_telefono,
)


class Local(models.Model):
    nombre = models.CharField(
        max_length=80,
        help_text='Nombre visible del establecimiento. Máximo 80 caracteres.',
        error_messages={
            'max_length': 'El nombre del local no puede superar los 80 caracteres.',
        },
    )
    descripcion = models.TextField(
        blank=True,
        validators=[validador_texto_largo(DESCRIPCION_MAX)],
        help_text=(
            'Cuenta qué ofrece el local: servicios, ambiente o horarios. '
            f'Máximo {DESCRIPCION_MAX} caracteres.'
        ),
        error_messages={
            'max_length': (
                f'La descripción no puede superar los {DESCRIPCION_MAX} caracteres.'
            ),
        },
    )
    direccion = models.CharField(
        'dirección',
        max_length=DIRECCION_MAX,
        validators=validadores_direccion(),
        help_text=(
            'Ej. Calle 50 # 43-20. Escribe letras y el número; entre 10 y '
            f'{DIRECCION_MAX} caracteres.'
        ),
        error_messages={
            'max_length': f'La dirección no puede superar los {DIRECCION_MAX} caracteres.',
        },
    )
    ciudad = models.CharField(
        max_length=100,
        help_text='Ciudad donde queda el local. Ej. Medellín.',
        error_messages={
            'max_length': 'La ciudad no puede superar los 100 caracteres.',
        },
    )
    telefono = models.CharField(
        'teléfono',
        max_length=TELEFONO_MAX,
        blank=True,
        validators=validadores_telefono(),
        help_text=(
            'Opcional. Entre 7 y 15 dígitos; puedes empezar con + y separar '
            'con espacios. Ej. 300 123 4567.'
        ),
        error_messages={
            'max_length': f'El teléfono no puede superar los {TELEFONO_MAX} caracteres.',
        },
    )
    # Coordenadas: las usa el mapa de Sol (VW_MAPA_LOCALES)
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Ej. 6.251800. Deja ambas coordenadas vacías si no las conoces.',
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text='Ej. -75.563600.',
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # MER: LOCAL.idUsuario FK (dueño del local). Se conserva además la M2M
    # 'administradores' para cumplir la regla del manual de varios administradores.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # El dueño puede darse de baja sin borrar el historial del local.
        on_delete=models.SET_NULL,
        related_name='locales',
        db_column='idUsuario',
        null=True,
        blank=True,
    )
    administradores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='locales_administrados',
        blank=True,
    )

    CAMPOS_TEXTO = ('nombre', 'descripcion', 'direccion', 'ciudad', 'telefono')

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.ciudad})'

    def save(self, *args, **kwargs):
        """Guarda los campos de texto sin espacios sobrantes.

        Si se usa ``update_fields`` solo se normalizan los campos que se van a
        escribir, para no dejar el objeto en memoria distinto de la base.
        """
        campos_actualizados = kwargs.get('update_fields')
        for campo in self.CAMPOS_TEXTO:
            if campos_actualizados is not None and campo not in campos_actualizados:
                continue
            valor = getattr(self, campo, None)
            if valor is not None:
                setattr(self, campo, normalizar_espacios(valor))
        return super().save(*args, **kwargs)

    def puede_administrar(self, usuario):
        """True si el usuario puede editar o desactivar este local.

        El dueño según el MER (FK idUsuario) manda aunque no esté en la M2M;
        también mandan los administradores explícitos y los superusuarios.
        Si la M2M viene precargada (``prefetch_related``) se consulta la caché
        y no se lanza una consulta por local en los listados.
        """
        if usuario is None or not getattr(usuario, 'is_authenticated', False):
            return False
        if getattr(usuario, 'is_superuser', False):
            return True
        if usuario.pk is not None and self.usuario_id == usuario.pk:
            return True
        cache = getattr(self, '_prefetched_objects_cache', {})
        if 'administradores' in cache:
            return any(admin.pk == usuario.pk for admin in cache['administradores'])
        return self.administradores.filter(pk=usuario.pk).exists()
