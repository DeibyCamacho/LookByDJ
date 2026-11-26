from django.db import models

from usuarios.validators import DESCRIPCION_MAX, validador_texto_largo


class Catalogo(models.Model):
    """MER: CATALOGO (idLocal FK)."""

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(
        blank=True,
        validators=[validador_texto_largo(DESCRIPCION_MAX)],
        help_text=f'Describe el catálogo en {DESCRIPCION_MAX} caracteres como máximo.',
        error_messages={
            'max_length': f'La descripción no puede superar los {DESCRIPCION_MAX} caracteres.',
        },
    )
    local = models.ForeignKey(
        'locales.Local',
        on_delete=models.CASCADE,
        related_name='catalogos',
        db_column='idLocal',
    )

    def __str__(self):
        return f'{self.nombre} ({self.local.nombre})'


class CatalogoProducto(models.Model):
    """MER: CATALOGO_PRODUCTO (idCatalogo FK, idInventario FK)."""

    catalogo = models.ForeignKey(
        Catalogo,
        on_delete=models.CASCADE,
        related_name='productos',
        db_column='idCatalogo',
    )
    inventario = models.ForeignKey(
        'inventario.InventarioLocal',
        on_delete=models.CASCADE,
        related_name='catalogos',
        db_column='idInventario',
    )

    class Meta:
        # Se conserva `unique_together` (legacy): convertirlo en UniqueConstraint
        # nominal exigiría una migración adicional y no aporta aquí ninguna regla nueva.
        unique_together = ('catalogo', 'inventario')

    @property
    def producto(self):
        return self.inventario.producto

    def __str__(self):
        return f'{self.catalogo.nombre} - {self.producto.nombre}'
