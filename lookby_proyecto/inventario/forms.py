from django import forms

from .models import InventarioLocal


class InventarioForm(forms.ModelForm):
    """Stock y precio de un producto en un local (par local/producto único)."""

    class Meta:
        model = InventarioLocal
        fields = ['local', 'producto', 'precio_venta', 'stock_actual']
        # Precio y stock heredan los validadores compartidos del modelo:
        # precio >= 0 con 2 decimales y tope; stock entre 0 y 100000.
        error_messages = {
            'precio_venta': {
                'min_value': 'El precio de venta no puede ser negativo. Usa 0 si es gratuito.',
                'max_value': 'El precio de venta supera el máximo permitido.',
                'decimal_places': 'El precio de venta admite máximo 2 decimales.',
            },
            'stock_actual': {
                'min_value': 'El stock no puede ser negativo. Usa 0 si no hay existencias.',
                'max_value': 'El stock no puede superar las 100000 unidades.',
            },
        }
        widgets = {
            'precio_venta': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={
                'min': '0', 'max': '100000', 'step': '1',
            }),
        }

    def clean(self):
        datos = super().clean()
        local = datos.get('local')
        producto = datos.get('producto')

        # El modelo ya tiene unique_together; aquí damos un mensaje legible.
        if local is not None and producto is not None:
            repetidos = InventarioLocal.objects.filter(local=local, producto=producto)
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                mensaje = (
                    'Ya existe un registro de inventario para este local y producto. '
                    'Edita el registro existente en vez de crear otro.'
                )
                self.add_error('producto', mensaje)
                self.add_error(None, mensaje)

        return datos
