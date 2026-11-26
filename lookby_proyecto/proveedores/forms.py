from django import forms

from usuarios.validators import (
    normalizar_espacios,
    validadores_correo,
    validadores_telefono,
)

from .models import Proveedor, ProveedorProducto


class ProveedorForm(forms.ModelForm):
    """Correo y teléfono validados con las mismas reglas que el resto del proyecto."""

    correo = forms.EmailField(
        label='Correo electrónico',
        max_length=150,
        validators=validadores_correo(),
        error_messages={'invalid': 'Escribe un correo electrónico válido.'},
        widget=forms.EmailInput(attrs={'placeholder': 'ventas@ejemplo.com'}),
    )
    telefono = forms.CharField(
        label='Teléfono',
        max_length=50,
        validators=validadores_telefono(),
        widget=forms.TextInput(attrs={'placeholder': 'Ej. 3019998888'}),
    )

    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Distribuidora Belleza'}),
        }

    def clean(self):
        datos = super().clean()
        datos['nombre'] = normalizar_espacios(datos.get('nombre'))
        datos['telefono'] = normalizar_espacios(datos.get('telefono')) or ''
        return datos


class ProveedorProductoForm(forms.ModelForm):
    """Precio de mayoreo de un producto suministrado por un proveedor."""

    class Meta:
        model = ProveedorProducto
        fields = ['idProveedor', 'producto', 'precioMayoreo']
        labels = {
            'idProveedor': 'Proveedor',
            'precioMayoreo': 'Precio de mayoreo',
        }
        # El precio hereda validadores_precio del modelo: 0 permitido, negativos no.
        error_messages = {
            'precioMayoreo': {
                'min_value': 'El precio de mayoreo no puede ser negativo. Usa 0 si es gratuito.',
                'max_value': 'El precio de mayoreo supera el máximo permitido.',
                'decimal_places': 'El precio de mayoreo admite máximo 2 decimales.',
            },
        }
        widgets = {
            'precioMayoreo': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

    def clean(self):
        datos = super().clean()
        proveedor = datos.get('idProveedor')
        producto = datos.get('producto')

        if proveedor is not None and producto is not None:
            repetidos = ProveedorProducto.objects.filter(
                idProveedor=proveedor, producto=producto
            )
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                mensaje = 'Ese proveedor ya tiene registrado este producto.'
                self.add_error('producto', mensaje)
                self.add_error(None, mensaje)

        return datos
