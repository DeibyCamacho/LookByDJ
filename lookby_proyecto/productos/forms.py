from django import forms

from usuarios.validators import DESCRIPCION_MAX, normalizar_espacios

from .models import Producto


class ProductoForm(forms.ModelForm):
    """Alta y edición del catálogo base de productos."""

    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Champú hidratante'}),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': DESCRIPCION_MAX,
                'placeholder': 'Describe brevemente el producto (máximo 500 caracteres)...',
            }),
            'categoria': forms.TextInput(attrs={'placeholder': 'Ej. Cuidado personal'}),
        }

    def clean(self):
        datos = super().clean()
        nombre = normalizar_espacios(datos.get('nombre'))
        categoria = normalizar_espacios(datos.get('categoria'))
        datos['descripcion'] = normalizar_espacios(datos.get('descripcion')) or ''

        if nombre:
            datos['nombre'] = nombre
            repetidos = Producto.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                self.add_error('nombre', 'Ya existe un producto con ese nombre.')

        if categoria:
            datos['categoria'] = categoria

        return datos
