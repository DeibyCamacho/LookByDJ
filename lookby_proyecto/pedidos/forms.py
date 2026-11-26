from django import forms
from inventario.models import InventarioLocal
from locales.models import Local
from usuarios.validators import (
    CANTIDAD_MAX,
    DIRECCION_MAX,
    validadores_cantidad,
    validadores_direccion,
)

from .models import Pedido

AYUDA_DIRECCION = (
    'Obligatoria. Entre 10 y 150 caracteres, con letras y al menos un número. '
    'Ejemplo: Calle 50 # 43-20, Medellín.'
)


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
        # Regla centralizada: 1 a CANTIDAD_MAX (1000). El tope también se
        # refleja en el widget, pero el validador es la defensa del servidor.
        validators=validadores_cantidad(),
        initial=1,
        widget=forms.NumberInput(attrs={
            'min': '1', 'max': str(CANTIDAD_MAX), 'step': '1',
        }),
    )
    direccion_entrega = forms.CharField(
        label='Dirección de entrega',
        max_length=DIRECCION_MAX,
        required=True,
        validators=validadores_direccion(),
        widget=forms.TextInput(attrs={'placeholder': 'Ej. Calle 50 # 43-20'}),
        help_text=AYUDA_DIRECCION,
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
                if not inventario.producto.activo:
                    self.add_error(
                        'inventario', 'El producto seleccionado no está activo.'
                    )
                if cantidad is not None and cantidad > inventario.stock_actual:
                    self.add_error(
                        'cantidad',
                        f'Solo hay {inventario.stock_actual} unidades disponibles.',
                    )
        return cleaned


class PedidoEditarForm(forms.ModelForm):
    """Solo se edita la dirección: ítems y total los fija el servidor."""

    direccion_entrega = forms.CharField(
        label='Dirección de entrega',
        max_length=DIRECCION_MAX,
        required=True,
        validators=validadores_direccion(),
        widget=forms.TextInput(attrs={'placeholder': 'Ej. Calle 50 # 43-20'}),
        help_text=AYUDA_DIRECCION,
    )

    class Meta:
        model = Pedido
        fields = ['direccion_entrega']
