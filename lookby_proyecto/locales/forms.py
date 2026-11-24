from django import forms

from .models import Local


class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = [
            'nombre', 'descripcion', 'direccion', 'ciudad',
            'telefono', 'latitud', 'longitud',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. LookBy Centro'}),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe los servicios y el ambiente del local...',
            }),
            'direccion': forms.TextInput(attrs={'placeholder': 'Ej. Calle 50 # 43-20'}),
            'ciudad': forms.TextInput(attrs={'placeholder': 'Ej. Medellín'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Ej. 3001234567'}),
            'latitud': forms.NumberInput(attrs={'step': 'any', 'placeholder': '6.2518'}),
            'longitud': forms.NumberInput(attrs={'step': 'any', 'placeholder': '-75.5636'}),
        }
        help_texts = {
            'latitud': 'Ej. 6.2518. Deja ambas coordenadas vacías si no las conoces.',
            'longitud': 'Ej. -75.5636.',
        }

    def clean(self):
        datos = super().clean()
        # Las coordenadas van juntas o ninguna
        if (datos.get('latitud') is None) != (datos.get('longitud') is None):
            raise forms.ValidationError('Indica latitud y longitud, o deja ambas vacías.')
        return datos
