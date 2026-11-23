from django import forms
from inventario.models import InventarioLocal
from locales.models import Local


class CrearPedidoForm(forms.Form):
    """Datos mínimos para registrar un pedido. El total lo calcula el servidor."""

    local = forms.ModelChoiceField(
        queryset=Local.objects.filter(activo=True),
        label='Local',
        empty_label='Selecciona un local',
    )
    inventario = forms.ModelChoiceField(
        queryset=InventarioLocal.objects.filter(
            stock_actual__gt=0, producto__activo=True
        ).select_related('producto', 'local'),
        label='Producto disponible',
        empty_label='Selecciona un producto',
    )
    cantidad = forms.IntegerField(label='Cantidad', min_value=1, initial=1)
    direccion_entrega = forms.CharField(
        label='Dirección de entrega', max_length=255, required=False,
    )
