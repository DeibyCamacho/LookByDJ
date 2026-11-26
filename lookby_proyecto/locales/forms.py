"""Alta y edición de locales.

La validación de fondo (teléfono, dirección y longitud de textos) vive en
``usuarios.validators``. Aquí solo se dan pistas al navegador y se normalizan
los espacios para que el usuario vea el mismo texto que se va a guardar.
"""

from django import forms

from usuarios.validators import (
    DESCRIPCION_MAX,
    DIRECCION_MAX,
    TELEFONO_MAX,
    _DIRECCION as PATRON_DIRECCION,
    _TELEFONO as PATRON_TELEFONO,
    normalizar_espacios,
)

from .models import Local

MAX_NOMBRE = '80'
MAX_CIUDAD = '100'
MAX_DIRECCION = str(DIRECCION_MAX)
MAX_TELEFONO = str(TELEFONO_MAX)
MAX_DESCRIPCION = str(DESCRIPCION_MAX)


class LocalForm(forms.ModelForm):
    """Formulario de local con mensajes en español junto a cada campo."""

    CAMPOS_NORMALIZABLES = ('nombre', 'descripcion', 'direccion', 'ciudad', 'telefono')

    class Meta:
        model = Local
        fields = [
            'nombre', 'descripcion', 'direccion', 'ciudad',
            'telefono', 'latitud', 'longitud',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. LookBy Centro',
                'maxlength': MAX_NOMBRE,
                'inputmode': 'text',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': MAX_DESCRIPCION,
                'placeholder': 'Describe los servicios y el ambiente del local...',
            }),
            # El patrón se reutiliza de usuarios.validators: no hay una segunda
            # expresión regular que pueda quedar desactualizada.
            'direccion': forms.TextInput(attrs={
                'placeholder': 'Ej. Calle 50 # 43-20',
                'maxlength': MAX_DIRECCION,
                'pattern': PATRON_DIRECCION.pattern,
                'inputmode': 'text',
            }),
            'ciudad': forms.TextInput(attrs={
                'placeholder': 'Ej. Medellín',
                'maxlength': MAX_CIUDAD,
                'inputmode': 'text',
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': 'Ej. 300 123 4567',
                'maxlength': MAX_TELEFONO,
                'pattern': PATRON_TELEFONO.pattern,
                'inputmode': 'tel',
            }),
            'latitud': forms.NumberInput(attrs={
                'step': 'any', 'min': '-90', 'max': '90',
                'inputmode': 'decimal', 'placeholder': '6.251800',
            }),
            'longitud': forms.NumberInput(attrs={
                'step': 'any', 'min': '-180', 'max': '180',
                'inputmode': 'decimal', 'placeholder': '-75.563600',
            }),
        }
        error_messages = {
            'nombre': {
                'required': 'Escribe el nombre del local.',
                'max_length': 'El nombre del local no puede superar los 80 caracteres.',
            },
            'descripcion': {
                'max_length': (
                    f'La descripción no puede superar los {DESCRIPCION_MAX} caracteres.'
                ),
            },
            'direccion': {
                'required': 'Escribe la dirección del local.',
                'max_length': (
                    f'La dirección no puede superar los {DIRECCION_MAX} caracteres.'
                ),
            },
            'ciudad': {
                'required': 'Escribe la ciudad donde queda el local.',
                'max_length': 'La ciudad no puede superar los 100 caracteres.',
            },
            'telefono': {
                'max_length': f'El teléfono no puede superar los {TELEFONO_MAX} caracteres.',
            },
            'latitud': {
                'invalid': 'Escribe una latitud válida, por ejemplo 6.251800.',
            },
            'longitud': {
                'invalid': 'Escribe una longitud válida, por ejemplo -75.563600.',
            },
        }

    def clean(self):
        """Normaliza espacios y exige las coordenadas en pareja."""
        datos = super().clean()
        for campo in self.CAMPOS_NORMALIZABLES:
            if campo in datos and datos[campo] is not None:
                datos[campo] = normalizar_espacios(datos[campo])

        # Las coordenadas van juntas o ninguna; el aviso se pone junto a la
        # que falta para que se sepa qué hay que corregir.
        if (datos.get('latitud') is None) != (datos.get('longitud') is None):
            campo_faltante = 'latitud' if datos.get('latitud') is None else 'longitud'
            self.add_error(campo_faltante, (
                'Indica la latitud y la longitud juntas, o deja ambas vacías. '
                'Las dos hacen falta para mostrar el local en el mapa.'
            ))
        return datos
