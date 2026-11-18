from django import forms

from .models import Local


class LocalForm(forms.ModelForm):
    class Meta:
        model = Local
        fields = [
            'nombre', 'descripcion', 'direccion', 'ciudad',
            'telefono', 'latitud', 'longitud',
        ]
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def clean(self):
        datos = super().clean()
        # Las coordenadas van juntas o ninguna
        if (datos.get('latitud') is None) != (datos.get('longitud') is None):
            raise forms.ValidationError('Indica latitud y longitud, o deja ambas vacías.')
        return datos
