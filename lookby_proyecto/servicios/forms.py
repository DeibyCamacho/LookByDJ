from django import forms

from usuarios.permisos import es_admin
from usuarios.validators import DESCRIPCION_MAX, normalizar_espacios

from profesionales.models import Profesional

from .models import OfertaServicio, Servicio


class ServicioForm(forms.ModelForm):
    """Alta y edición del catálogo de servicios."""

    class Meta:
        model = Servicio
        fields = ('nombre', 'categoria', 'descripcion')
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': DESCRIPCION_MAX,
                'placeholder': 'Máximo 500 caracteres.',
            }),
        }

    def clean(self):
        cleaned = super().clean()
        nombre = normalizar_espacios(cleaned.get('nombre'))
        categoria = normalizar_espacios(cleaned.get('categoria'))
        cleaned['nombre'] = nombre
        cleaned['categoria'] = categoria
        cleaned['descripcion'] = normalizar_espacios(cleaned.get('descripcion')) or ''

        if nombre:
            repetidos = Servicio.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                repetidos = repetidos.exclude(pk=self.instance.pk)
            if repetidos.exists():
                self.add_error('nombre', 'Ya existe un servicio con ese nombre.')
        return cleaned


class OfertaServicioForm(forms.ModelForm):
    """Alta y edición de ofertas; el profesional dueño solo gestiona las suyas."""

    class Meta:
        model = OfertaServicio
        fields = ('servicio', 'profesional', 'local', 'precio', 'duracion', 'activa')
        labels = {
            'duracion': 'Duración (minutos)',
            'activa': 'Oferta activa',
        }
        # El precio hereda los validadores compartidos del modelo (validadores_precio):
        # 0 es válido, los negativos y más de 2 decimales se rechazan.
        error_messages = {
            'precio': {
                'min_value': 'El precio no puede ser negativo. Usa 0 si es gratuito.',
                'max_value': 'El precio supera el máximo permitido.',
                'decimal_places': 'El precio admite máximo 2 decimales.',
            },
        }
        widgets = {
            'precio': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usuario = usuario
        if usuario is not None and not es_admin(usuario):
            perfiles = Profesional.objects.filter(usuario=usuario)
            self.fields['profesional'].queryset = perfiles
            if not self.instance.pk and perfiles.exists():
                self.fields['profesional'].initial = perfiles.first().pk

    def clean(self):
        cleaned = super().clean()
        duracion = cleaned.get('duracion')
        servicio = cleaned.get('servicio')
        profesional = cleaned.get('profesional')
        local = cleaned.get('local')
        activa = cleaned.get('activa', False)

        if duracion is not None:
            if duracion <= 0:
                self.add_error('duracion', 'La duración debe ser mayor que cero.')
            elif duracion > 480:
                self.add_error('duracion', 'La duración no puede superar 480 minutos.')

        if servicio and profesional and activa:
            repetidas = OfertaServicio.objects.filter(
                servicio=servicio,
                profesional=profesional,
                activa=True,
                local=local,
            )
            if self.instance.pk:
                repetidas = repetidas.exclude(pk=self.instance.pk)
            if repetidas.exists():
                self.add_error(
                    'servicio',
                    'Ya existe una oferta activa igual para ese profesional y local.',
                )
        return cleaned
