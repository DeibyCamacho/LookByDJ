from django import forms

from .models import InventarioLocal


class InventarioForm(forms.ModelForm):
    """Stock y precio de un producto en un local (par local/producto único)."""

    class Meta:
        model = InventarioLocal
        fields = ['local', 'producto', 'precio_venta', 'stock_actual']
        widgets = {
            'precio_venta': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'min': '0', 'step': '1'}),
        }

    def clean(self):
        datos = super().clean()
        local = datos.get('local')
        producto = datos.get('producto')
        precio = datos.get('precio_venta')
        stock = datos.get('stock_actual')

        if stock is not None and stock < 0:
            self.add_error(
                'stock_actual',
                'El stock no puede ser negativo. Usa 0 si no hay existencias.',
            )

        if precio is not None and precio <= 0:
            self.add_error(
                'precio_venta',
                'El precio de venta debe ser mayor que cero.',
            )

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
