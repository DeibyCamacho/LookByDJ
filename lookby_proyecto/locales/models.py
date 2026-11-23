from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Local(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    direccion = models.CharField('dirección', max_length=200)
    ciudad = models.CharField(max_length=100)
    telefono = models.CharField('teléfono', max_length=30, blank=True)
    # Coordenadas: las usa el mapa de Sol (VW_MAPA_LOCALES)
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # MER: LOCAL.idUsuario FK (dueño del local). Se conserva además la M2M
    # 'administradores' para cumplir la regla del manual de varios administradores.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
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

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.ciudad})'

    def puede_administrar(self, usuario):
        """True si el usuario puede editar o desactivar este local."""
        if not usuario.is_authenticated:
            return False
        if usuario.is_superuser:
            return True
        return self.administradores.filter(pk=usuario.pk).exists()
