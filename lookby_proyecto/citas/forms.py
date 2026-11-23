from django import forms
from servicios.models import OfertaServicio


class CrearCitaForm(forms.Form):
    """Un cliente elige una oferta activa y la fecha/hora de su reserva."""

    oferta = forms.ModelChoiceField(
        queryset=OfertaServicio.objects.filter(activa=True).select_related(
            'servicio', 'profesional__usuario', 'local'
        ),
        label='Servicio',
        empty_label='Selecciona un servicio',
    )
    fecha_inicio = forms.DateTimeField(
        label='Fecha y hora',
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
        help_text='La duración se toma automáticamente del servicio elegido.',
    )
