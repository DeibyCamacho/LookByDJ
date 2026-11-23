from django.db import models
from productos.models import Producto

class InventarioLocal(models.Model):
    # Nota: cuando el módulo de locales de Jhon esté integrado, esta clave foránea apuntará al modelo Local.
    # Por ahora dejamos un campo genérico o referencia para que no te detengas.
    local_id = models.IntegerField(help_text="ID temporal del local hasta integrar el módulo de Jhon")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('local_id', 'producto')

    def __str__(self):
        return f"Local {self.local_id} - {self.producto.nombre} (Stock: {self.stock_actual})"