from django.db import models


class VwMapaLocales(models.Model):
    """Vista SQL PostgreSQL VW_MAPA_LOCALES (no es una tabla administrada)."""

    id_local = models.IntegerField(primary_key=True, db_column='idLocal')
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200)
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    calificacion = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
    )

    class Meta:
        managed = False
        db_table = 'vw_mapa_locales'
        verbose_name = 'local del mapa'
        verbose_name_plural = 'locales del mapa'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
