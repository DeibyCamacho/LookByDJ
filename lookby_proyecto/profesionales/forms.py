from django import forms

from usuarios.permisos import es_admin
from usuarios.validators import BIOGRAFIA_MAX, normalizar_espacios

from .models import Horario, Profesional


class ProfesionalForm(forms.ModelForm):
    """Alta y edición del perfil profesional."""

    class Meta:
        model = Profesional
        fields = ('usuario', 'biografia', 'domicilio', 'latitud', 'longitud')
        widgets = {
            'biografia': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': BIOGRAFIA_MAX,
                'placeholder': 'Máximo 500 caracteres.',
            }),
        }
        labels = {
            'usuario': 'Usuario',
            'biografia': 'Biografía',
            'domicilio': 'Ofrece servicio a domicilio',
            'latitud': 'Latitud',
            'longitud': 'Longitud',
        }

    def clean_usuario(self):
        usuario = self.cleaned_data.get('usuario')
        if usuario is None:
            return usuario
        repetidos = Profesional.objects.filter(usuario=usuario)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError('Ese usuario ya tiene un perfil profesional.')
        return usuario

    def clean(self):
        cleaned = super().clean()
        latitud = cleaned.get('latitud')
        longitud = cleaned.get('longitud')

        if (latitud is None) != (longitud is None):
            self.add_error(
                'latitud',
                'Indica la latitud y la longitud juntas, o deja ambas vacías.',
            )
        if latitud is not None and longitud is not None:
            if not -90 <= float(latitud) <= 90:
                self.add_error('latitud', 'La latitud debe estar entre -90 y 90.')
            if not -180 <= float(longitud) <= 180:
                self.add_error('longitud', 'La longitud debe estar entre -180 y 180.')

        cleaned['biografia'] = normalizar_espacios(cleaned.get('biografia')) or ''
        return cleaned


class HorarioForm(forms.ModelForm):
    """Alta y edición de horarios; un profesional no puede solapar turnos."""

    class Meta:
        model = Horario
        fields = ('profesional', 'local', 'dia_semana', 'hora_inicio', 'hora_fin')

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
        profesional = cleaned.get('profesional')
        dia = cleaned.get('dia_semana')
        inicio = cleaned.get('hora_inicio')
        fin = cleaned.get('hora_fin')
        local = cleaned.get('local')

        if inicio and fin and fin <= inicio:
            self.add_error('hora_fin', 'La hora final debe ser posterior a la inicial.')

        if profesional and dia and inicio and fin and fin > inicio:
            solapados = Horario.objects.filter(
                profesional=profesional,
                dia_semana=dia,
                hora_inicio__lt=fin,
                hora_fin__gt=inicio,
            )
            if local is None:
                solapados = solapados.filter(local__isnull=True)
            else:
                solapados = solapados.filter(local=local)
            if self.instance.pk:
                solapados = solapados.exclude(pk=self.instance.pk)
            if solapados.exists():
                self.add_error(
                    'hora_inicio',
                    'Ya existe un horario solapado para ese día y local.',
                )
        return cleaned
