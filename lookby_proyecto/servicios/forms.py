from django import forms

from usuarios.permisos import es_admin

from profesionales.models import Profesional

from .models import OfertaServicio, Servicio


class ServicioForm(forms.ModelForm):
    """Alta y edición del catálogo de servicios."""

    class Meta:
        model = Servicio
        fields = ('nombre', 'categoria', 'descripcion')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        nombre = (cleaned.get('nombre') or '').strip()
        categoria = (cleaned.get('categoria') or '').strip()
        cleaned['nombre'] = nombre
        cleaned['categoria'] = categoria

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
        precio = cleaned.get('precio')
        duracion = cleaned.get('duracion')
        servicio = cleaned.get('servicio')
        profesional = cleaned.get('profesional')
        local = cleaned.get('local')
        activa = cleaned.get('activa', False)

        if precio is not None and precio <= 0:
            self.add_error('precio', 'El precio debe ser mayor que cero.')
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
