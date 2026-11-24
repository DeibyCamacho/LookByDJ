from django import forms

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
                'placeholder': 'Describe brevemente el producto...',
            }),
            'categoria': forms.TextInput(attrs={'placeholder': 'Ej. Cuidado personal'}),
        }

    def clean(self):
        datos = super().clean()
        nombre = (datos.get('nombre') or '').strip()
        categoria = (datos.get('categoria') or '').strip()

        if nombre:
            nombre = ' '.join(nombre.split())
            datos['nombre'] = nombre
            repetidos = Producto.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                self.add_error('nombre', 'Ya existe un producto con ese nombre.')

        if categoria:
            datos['categoria'] = ' '.join(categoria.split())

        return datos
