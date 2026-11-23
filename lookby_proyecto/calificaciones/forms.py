from django import forms
from .models import Calificacion


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['local', 'profesional', 'puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Cuéntanos cómo fue tu experiencia...',
            }),
        }
        labels = {
            'puntuacion': 'Puntuación (1 a 5)',
        }

    def clean(self):
        cleaned = super().clean()
        local = cleaned.get('local')
        profesional = cleaned.get('profesional')
        if bool(local) == bool(profesional):
            raise forms.ValidationError(
                'Debes elegir un local o un profesional (solo uno).'
            )
        return cleaned
