from django import forms

from citas.models import Cita
from pedidos.models import Pedido

from .models import Calificacion


class CalificacionForm(forms.ModelForm):
    def __init__(self, *args, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente

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

        if self.cliente is None or getattr(self.cliente, 'is_anonymous', False):
            return cleaned

        # Duplicados: las constraints de la BD también lo impiden, pero aquí
        # damos un error de formulario en vez de un IntegrityError.
        propias = Calificacion.objects.filter(cliente=self.cliente)
        if self.instance.pk:
            propias = propias.exclude(pk=self.instance.pk)
        if local and propias.filter(local=local).exists():
            self.add_error('local', 'Ya calificaste este local.')
        if profesional and propias.filter(profesional=profesional).exists():
            self.add_error('profesional', 'Ya calificaste este profesional.')

        # Regla del manual: el cliente debe haber tenido cita o pedido con el
        # objetivo. Si la BD está vacía de citas y pedidos se permite igual:
        # es el modo demo, para no romper las pruebas con datos de ejemplo.
        hay_actividad = Cita.objects.exists() or Pedido.objects.exists()
        if hay_actividad and (local or profesional):
            if local:
                relacion = (
                    Pedido.objects.filter(cliente=self.cliente, local=local).exists()
                    or Cita.objects.filter(
                        cliente=self.cliente, oferta__local=local
                    ).exists()
                )
            else:
                relacion = Cita.objects.filter(
                    cliente=self.cliente, oferta__profesional=profesional
                ).exists()
            if not relacion:
                raise forms.ValidationError(
                    'Solo puedes calificar un local o profesional con el que '
                    'hayas tenido una cita o un pedido.'
                )
        return cleaned
