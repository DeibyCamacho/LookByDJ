from django import forms
from inventario.models import InventarioLocal
from locales.models import Local

from .models import Pedido


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
    cantidad = forms.IntegerField(
        label='Cantidad',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'min': '1', 'step': '1'}),
    )
    direccion_entrega = forms.CharField(
        label='Dirección de entrega',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ej. Calle 50 # 43-20'}),
    )

    def clean(self):
        """El producto debe pertenecer al local elegido (evita el 500 al crear)."""
        cleaned = super().clean()
        local = cleaned.get('local')
        inventario = cleaned.get('inventario')
        cantidad = cleaned.get('cantidad')

        if local and inventario:
            if inventario.local_id != local.pk:
                self.add_error(
                    'inventario',
                    'El producto seleccionado pertenece a otro local. '
                    'Elige un producto disponible en el local indicado.',
                )
            else:
                if not local.activo:
                    self.add_error('local', 'El local seleccionado no está activo.')
                if cantidad is not None and cantidad > inventario.stock_actual:
                    self.add_error(
                        'cantidad',
                        f'Solo hay {inventario.stock_actual} unidades disponibles.',
                    )
        return cleaned


class PedidoEditarForm(forms.ModelForm):
    """Solo se edita la dirección: ítems y total los fija el servidor."""

    class Meta:
        model = Pedido
        fields = ['direccion_entrega']
        labels = {'direccion_entrega': 'Dirección de entrega'}
