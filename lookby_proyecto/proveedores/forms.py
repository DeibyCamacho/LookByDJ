import re

from django import forms

from .models import Proveedor, ProveedorProducto


class ProveedorForm(forms.ModelForm):
    """El modelo guarda correo como CharField; aquí se valida como email."""

    correo = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'ventas@ejemplo.com'}),
    )

    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'correo']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Distribuidora Belleza'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej. 3019998888'}),
        }

    def clean(self):
        datos = super().clean()
        nombre = (datos.get('nombre') or '').strip()
        telefono = (datos.get('telefono') or '').strip()

        if nombre:
            datos['nombre'] = ' '.join(nombre.split())

        if telefono:
            if not re.fullmatch(r'[\d\s()+.\-]{7,25}', telefono):
                self.add_error(
                    'telefono',
                    'Usa solo números, espacios y los símbolos + ( ) - .',
                )
            elif len(re.sub(r'\D', '', telefono)) < 7:
                self.add_error('telefono', 'El teléfono debe tener al menos 7 dígitos.')
            else:
                datos['telefono'] = telefono

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
        widgets = {
            'precioMayoreo': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

    def clean(self):
        datos = super().clean()
        proveedor = datos.get('idProveedor')
        producto = datos.get('producto')
        precio = datos.get('precioMayoreo')

        if precio is not None and precio <= 0:
            self.add_error('precioMayoreo', 'El precio de mayoreo debe ser mayor que cero.')

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
