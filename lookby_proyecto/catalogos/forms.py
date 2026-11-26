from django import forms

from inventario.models import InventarioLocal
from usuarios.validators import DESCRIPCION_MAX, normalizar_espacios

from .models import Catalogo, CatalogoProducto


class CatalogoForm(forms.ModelForm):
    class Meta:
        model = Catalogo
        fields = ['nombre', 'descripcion', 'local']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Catálogo de verano'}),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': DESCRIPCION_MAX,
                'placeholder': 'Máximo 500 caracteres.',
            }),
        }

    def clean(self):
        datos = super().clean()
        nombre = normalizar_espacios(datos.get('nombre'))
        local = datos.get('local')
        datos['descripcion'] = normalizar_espacios(datos.get('descripcion')) or ''

        if nombre:
            datos['nombre'] = nombre
            repetidos = Catalogo.objects.filter(nombre__iexact=nombre)
            if local is not None:
                repetidos = repetidos.filter(local=local)
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                self.add_error('nombre', 'Ese local ya tiene un catálogo con ese nombre.')

        return datos


class CatalogoProductoForm(forms.ModelForm):
    """Solo permite inventario del mismo local del catálogo elegido."""

    class Meta:
        model = CatalogoProducto
        fields = ['catalogo', 'inventario']
        labels = {'inventario': 'Producto del inventario del local'}

    def __init__(self, *args, catalogo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if catalogo is not None:
            self.fields['catalogo'].queryset = Catalogo.objects.filter(pk=catalogo.pk)
            self.fields['catalogo'].initial = catalogo.pk
            self.fields['inventario'].queryset = InventarioLocal.objects.filter(
                local=catalogo.local
            ).select_related('producto', 'local')
        else:
            self.fields['inventario'].queryset = InventarioLocal.objects.all() \
                .select_related('producto', 'local')

    def clean(self):
        datos = super().clean()
        catalogo = datos.get('catalogo')
        inventario = datos.get('inventario')

        if catalogo is not None and inventario is not None:
            if inventario.local_id != catalogo.local_id:
                self.add_error(
                    'inventario',
                    'El producto pertenece a otro local. Solo puedes agregar '
                    'inventario del mismo local del catálogo.',
                )
            else:
                repetidos = CatalogoProducto.objects.filter(
                    catalogo=catalogo, inventario=inventario
                )
                if self.instance.pk:
                    repetidos = repetidos.exclude(pk=self.instance.pk)
                if repetidos.exists():
                    self.add_error(
                        'inventario', 'Ese producto ya está en este catálogo.'
                    )

        return datos
