from django import forms
from django.utils import timezone
from servicios.models import OfertaServicio


class _FechaCitaMixin:
    def clean_fecha_inicio(self):
        fecha = self.cleaned_data.get('fecha_inicio')
        if fecha is not None and fecha < timezone.now():
            raise forms.ValidationError('No se puede elegir una fecha pasada.')
        return fecha


class CrearCitaForm(_FechaCitaMixin, forms.Form):
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


class ReprogramarCitaForm(_FechaCitaMixin, forms.Form):
    """Cambia la oferta y/o la fecha de una cita pendiente o confirmada."""

    oferta = forms.ModelChoiceField(
        queryset=OfertaServicio.objects.filter(activa=True).select_related(
            'servicio', 'profesional__usuario', 'local'
        ),
        label='Servicio',
    )
    fecha_inicio = forms.DateTimeField(
        label='Nueva fecha y hora',
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M'],
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M',
        ),
    )
