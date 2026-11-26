"""Formularios de altas y edición de usuarios de LookBy.

Los formularios que escriben ``nombre`` o ``correo`` muestran la norma de
calidad como texto de ayuda y delegan la validación en los validadores del
modelo (ver :mod:`usuarios.validators`). Así la regla es idéntica en el
registro, en el perfil y en la administración.
"""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm

from .models import Rol, Usuario
from .validators import (
    CORREO_MAX,
    CORREO_MIN,
    NOMBRE_MAX,
    NOMBRE_MIN,
    TELEFONO_MAX,
    normalizar_espacios,
)

MAX_NOMBRE_USUARIO = str(NOMBRE_MAX)
MAX_APELLIDO = str(NOMBRE_MAX)
MAX_TELEFONO = str(TELEFONO_MAX)

# Textos construidos con las constantes de la norma para que no se desactualicen.
AYUDA_NOMBRE = (
    f'De {NOMBRE_MIN} a {NOMBRE_MAX} caracteres. Solo letras y espacios; '
    'sin números ni caracteres especiales.'
)
AYUDA_APELLIDO = AYUDA_NOMBRE.replace('nombre', 'apellido')
AYUDA_CORREO = (
    f'De {CORREO_MIN} a {CORREO_MAX} caracteres. Use un correo válido '
    '(por ejemplo ana@lookby.com), sin otros signos.'
)
AYUDA_TELEFONO = (
    'De 7 a 15 dígitos. Puedes usar + y espacios. Ejemplo: 300 123 4567.'
)


class NormalizacionCamposMixin:
    """Recorta y colapsa espacios en los campos de texto antes de validar."""

    CAMPOS_NORMALIZABLES = ('nombre', 'apellido', 'telefono')

    def clean(self):
        """Normaliza lo que el usuario escribió y deja el valor limpio en el form."""
        datos = super().clean()
        for campo in self.CAMPOS_NORMALIZABLES:
            if campo in datos and datos[campo] is not None:
                datos[campo] = normalizar_espacios(datos[campo])
        return datos


class RegistroForm(NormalizacionCamposMixin, forms.ModelForm):
    """Alta de clientes: valida la norma y comprueba contraseñas y correo único."""

    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Mínimo 8 caracteres',
        }),
        help_text='Usa al menos 8 caracteres; evita datos personales y contraseñas comunes.',
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'placeholder': 'Repite tu contraseña',
        }),
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'telefono']
        help_texts = {
            'nombre': AYUDA_NOMBRE,
            'apellido': AYUDA_APELLIDO,
            'correo': AYUDA_CORREO,
            'telefono': AYUDA_TELEFONO,
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Tu nombre', 'maxlength': MAX_NOMBRE_USUARIO,
                'autocomplete': 'given-name',
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Tu apellido', 'maxlength': MAX_APELLIDO,
                'autocomplete': 'family-name',
            }),
            'correo': forms.EmailInput(attrs={'placeholder': 'tu@correo.com'}),
            'telefono': forms.TextInput(attrs={
                'placeholder': '3001234567', 'maxlength': MAX_TELEFONO,
                'inputmode': 'tel', 'autocomplete': 'tel',
            }),
        }

    def clean_correo(self):
        correo = self.cleaned_data['correo'].strip().lower()
        if Usuario.objects.filter(correo__iexact=correo).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return correo

    def clean(self):
        datos = super().clean()
        p1, p2 = datos.get('password1'), datos.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        elif p1:
            # Se valida contra el usuario para detectar contraseñas parecidas al correo/nombre
            usuario = Usuario(
                correo=datos.get('correo', ''),
                nombre=datos.get('nombre', ''),
            )
            try:
                password_validation.validate_password(p1, usuario)
            except forms.ValidationError as error:
                self.add_error('password1', error)
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data['password1'])
        if commit:
            usuario.save()
            usuario.agregar_rol('CLIENTE')
        return usuario


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'autocomplete': 'email',
            'placeholder': 'tu@correo.com',
        }),
    )
    password = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Tu contraseña',
        }),
    )

    error_messages = {
        # Mensaje genérico: no revela si el correo existe ni si la cuenta está
        # desactivada (evita enumeración de cuentas).
        'invalid_login': 'Correo o contraseña incorrectos.',
        'inactive': 'Correo o contraseña incorrectos.',
    }


class PerfilForm(NormalizacionCamposMixin, forms.ModelForm):
    """Edición de los datos personales; el correo no se puede cambiar aquí."""

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'telefono']
        help_texts = {
            'nombre': AYUDA_NOMBRE,
            'apellido': AYUDA_APELLIDO,
            'telefono': AYUDA_TELEFONO,
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Tu nombre', 'maxlength': MAX_NOMBRE_USUARIO,
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Tu apellido', 'maxlength': MAX_APELLIDO,
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '3001234567', 'maxlength': MAX_TELEFONO,
                'inputmode': 'tel',
            }),
        }


class UsuarioEdicionForm(PerfilForm):
    """Edición del propio perfil: nunca expone roles ni estado activo."""

    def __init__(self, *args, editor=None, **kwargs):
        self.editor = editor
        super().__init__(*args, **kwargs)

    def clean(self):
        datos = super().clean()
        if not datos.get('nombre', '').strip():
            self.add_error('nombre', 'El nombre es obligatorio.')
        return datos


class UsuarioAdminForm(NormalizacionCamposMixin, forms.ModelForm):
    """Edición administrativa de una cuenta (incluye roles y baja lógica)."""

    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Roles',
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'is_active', 'roles']
        help_texts = {
            'nombre': AYUDA_NOMBRE,
            'apellido': AYUDA_APELLIDO,
            'correo': AYUDA_CORREO,
            'telefono': AYUDA_TELEFONO,
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre', 'maxlength': MAX_NOMBRE_USUARIO,
            }),
            'apellido': forms.TextInput(attrs={
                'placeholder': 'Apellido', 'maxlength': MAX_APELLIDO,
            }),
            'telefono': forms.TextInput(attrs={
                'placeholder': '3001234567', 'maxlength': MAX_TELEFONO,
                'inputmode': 'tel',
            }),
        }

    def __init__(self, *args, editor=None, **kwargs):
        self.editor = editor
        super().__init__(*args, **kwargs)

    def clean_correo(self):
        correo = self.cleaned_data['correo'].strip().lower()
        repetidos = Usuario.objects.filter(correo__iexact=correo)
        if self.instance.pk:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return correo

    def clean(self):
        datos = super().clean()
        if not datos.get('nombre', '').strip():
            self.add_error('nombre', 'El nombre es obligatorio.')

        # Nadie puede ascender a sí mismo, ni siquiera enviando 'roles' a mano
        # en una petición que no debería tener ese campo.
        if self.editor is not None and self.instance.pk == self.editor.pk:
            actuales = set(self.instance.roles.values_list('nombre', flat=True))
            elegidos = set(
                datos.get('roles', Rol.objects.none()).values_list('nombre', flat=True)
            )
            if Rol.ADMINISTRADOR in elegidos - actuales:
                self.add_error(
                    'roles', 'No puedes asignarte el rol de administrador a ti mismo.'
                )
            if not datos.get('is_active', True):
                self.add_error(
                    'is_active', 'Usa la baja de cuentas para desactivar tu propia cuenta.'
                )
        return datos
