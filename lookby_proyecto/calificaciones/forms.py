from django import forms

from citas.models import Cita
from pedidos.models import Pedido
from usuarios.validators import COMENTARIO_MAX

from .models import Calificacion

MENSAJE_ELEGIBILIDAD = (
    'Solo puedes calificar un local o profesional con el que hayas tenido '
    'una cita o un pedido; la cita debe estar completada o el pedido entregado.'
)

# Auditoría 26/11/2026: la regla estricta es Cita COMPLETADA o Pedido ENTREGADO.
# PENDIENTE: el flujo de la app todavía no ofrece ninguna acción para marcar esos
# estados (solo se pueden cambiar desde el admin de Django). Mientras tanto se
# mantiene activo, SOLO para datos demo/legacy, el fallback que admite el resto
# de estados. En cuanto exista la transición, cambiar esto a False: la misma
# regla pasará a exigir la finalización sin necesitar más cambios.
PERMITIR_DATOS_LEGACY_SIN_FINALIZAR = True


class CalificacionForm(forms.ModelForm):
    def __init__(self, *args, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente
        if self.instance.pk:
            # El objetivo queda fijo al crear. `disabled` ignora cualquier
            # valor manipulado en el POST y conserva el de la instancia.
            self.fields['local'].disabled = True
            self.fields['profesional'].disabled = True

    class Meta:
        model = Calificacion
        fields = ['local', 'profesional', 'puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comentario': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': COMENTARIO_MAX,
                'placeholder': 'Cuéntanos cómo fue tu experiencia...',
            }),
        }
        labels = {
            'puntuacion': 'Puntuación (1 a 5)',
        }
        help_texts = {
            'comentario': f'Máximo {COMENTARIO_MAX} caracteres.',
        }

    def _objetivo(self, cleaned):
        """En edición manda la instancia; el POST nunca cambia el objetivo."""
        if self.instance.pk:
            return self.instance.local, self.instance.profesional
        return cleaned.get('local'), cleaned.get('profesional')

    @staticmethod
    def _relaciones(cliente, local, profesional):
        """Consultas del cliente con el objetivo (citas y pedidos)."""
        if local is not None:
            pedidos = Pedido.objects.filter(cliente=cliente, local=local)
            citas = Cita.objects.filter(cliente=cliente, oferta__local=local)
        else:
            pedidos = Pedido.objects.none()
            citas = Cita.objects.filter(
                cliente=cliente, oferta__profesional=profesional
            )
        return pedidos, citas

    def clean(self):
        cleaned = super().clean()
        local, profesional = self._objetivo(cleaned)
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

        if self.instance.pk:
            # El objetivo es inmutable: no se revalida la elegibilidad al editar
            # el texto o la puntuación.
            return cleaned

        pedidos, citas = self._relaciones(self.cliente, local, profesional)
        finalizada = (
            pedidos.filter(estado='ENTREGADO').exists()
            or citas.filter(estado='COMPLETADA').exists()
        )
        if not finalizada:
            if not PERMITIR_DATOS_LEGACY_SIN_FINALIZAR:
                raise forms.ValidationError(MENSAJE_ELEGIBILIDAD)

            # Fallback legacy/demo: se toleran estados pendientes/confirmados
            # solo si hay relación con este objetivo, o si el cliente no tiene
            # ningún historial (base de ejemplo). Un cliente con pedidos/citas
            # ajenos al objetivo sí se rechaza, como antes, pero el chequeo ya
            # no depende de lo que haya en toda la base de datos.
            tiene_relacion = pedidos.exists() or citas.exists()
            tiene_historial = (
                Pedido.objects.filter(cliente=self.cliente).exists()
                or Cita.objects.filter(cliente=self.cliente).exists()
            )
            if tiene_historial and not tiene_relacion:
                raise forms.ValidationError(MENSAJE_ELEGIBILIDAD)
        return cleaned
