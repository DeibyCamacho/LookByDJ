r"""Validadores reutilizables de LookBy (una sola definición, todo el proyecto).

Historia
--------
El 25/11/2026 se integró la norma de calidad del nombre y el correo del usuario.
El 26/11/2026, tras la prueba funcional, se amplió el módulo para cubrir también
apellido, teléfono, dirección, precios, cantidades y textos largos. Así evitamos
que cada app repita expresiones regulares con mensajes distintos.

Reglas
------
===================  =========================================================
Campo                Regla
===================  =========================================================
nombre/apellido      3 a 30 caracteres; solo letras (tildes y ñ incluidas) y
                     espacios entre palabras; sin números ni signos.
correo               3 a 30 caracteres; formato válido; solo letras, números,
                     ``@``, punto, guión, guion bajo y ``+``.
teléfono             7 a 15 dígitos; se admite un ``+`` inicial y espacios;
                     si tiene 10 dígitos debe ser un celular CO que empieza por 3.
dirección            10 a 150 caracteres; debe tener letras y al menos un número;
                     se permiten ``#``, ``-``, ``.``, ``,`` y ``°``.
precio               Decimal mayor o igual a 0, máximo 2 decimales y tope.
cantidad             Entero entre 1 y ``CANTIDAD_MAX``.
===================  =========================================================

Notas de diseño
---------------
* Las clases llevan ``@deconstructible`` y ``__eq__`` para que Django pueda
  serializarlas en las migraciones sin generar cambios espuros.
* ``[^\W\d_]`` es la forma Unicode de decir "letra": ``\w`` incluye letras,
  números y guion bajo, así que se excluyen explícitamente los dos últimos.
* Un validador es la defensa del servidor; ``maxlength``/``pattern`` en HTML son
  solo ayuda de usabilidad. Los formularios además hacen ``strip`` antes de
  validar y guardan el valor normalizado (ver :func:`normalizar_espacios`).
"""

import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import (
    DecimalValidator,
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
)
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

#: Longitud mínima de un nombre o apellido de persona.
NOMBRE_MIN = 3
#: Longitud máxima de un nombre o apellido de persona.
NOMBRE_MAX = 30
#: Longitud mínima del correo.
CORREO_MIN = 3
#: Longitud máxima del correo.
CORREO_MAX = 30
#: Longitud máxima del teléfono guardado en la base.
TELEFONO_MAX = 20
#: Dígitos mínimos y máximos del teléfono (sin contar el ``+`` ni los espacios).
TELEFONO_DIGITOS_MIN = 7
TELEFONO_DIGITOS_MAX = 15
#: Longitud de la dirección de entrega.
DIRECCION_MIN = 10
DIRECCION_MAX = 150
#: Tope de precio y de cantidad.
PRECIO_MAX = Decimal('999999999.99')
CANTIDAD_MAX = 1000
#: Límites de los textos libres que antes no tenían tope.
DESCRIPCION_MAX = 500
BIOGRAFIA_MAX = 500
COMENTARIO_MAX = 300

_SOLO_LETRAS_Y_ESPACIOS = re.compile(r'^[^\W\d_]+(?: +[^\W\d_]+)*$')
_CORREO_PERMITIDO = re.compile(
    r'^[A-Za-z0-9][A-Za-z0-9._+-]*@'
    r'[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?'
    r'(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$'
)
_TELEFONO = re.compile(r'^\+?[0-9]+(?: [0-9]+)*$')
_DIRECCION = re.compile(r'^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9#°.,/\-\s]+$')


def normalizar_espacios(valor):
    """Recorta espacios extremos y colapsa los internos repetidos.

    Se usa en los formularios antes de validar y al guardar, para que un valor
    como ``'  Ana   María '`` se almacene como ``'Ana María'`` y no se vea con
    basura en pedidos, calificaciones ni listados.
    """
    if valor is None:
        return valor
    return re.sub(r'\s+', ' ', str(valor)).strip()


@deconstructible
class ValidarNombrePersona:
    """Valida un nombre de persona con el mensaje adecuado al campo.

    Args:
        campo: nombre del campo en los mensajes ('nombre' o 'apellido').
    """

    def __init__(self, campo='nombre'):
        self.campo = campo

    @property
    def message(self):
        """Mensaje en español, claro y accionable."""
        return _(
            f'El {self.campo} solo puede contener letras y espacios. '
            'No se permiten números ni caracteres especiales.'
        )

    code = 'nombre_persona_no_valido'

    def __call__(self, value):
        """Rechaza vacíos, números, signos y espacios mal puestos."""
        valor = normalizar_espacios(value)
        if not valor:
            raise ValidationError(
                _(f'El {self.campo} es obligatorio.'), code='campo_obligatorio'
            )
        if not _SOLO_LETRAS_Y_ESPACIOS.match(valor):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        """Comparación estable para las migraciones."""
        return (
            isinstance(other, ValidarNombrePersona)
            and self.campo == other.campo
        )


@deconstructible
class ValidarSoloLetrasYEspacios(ValidarNombrePersona):
    """Compatibilidad con la migración ``0004`` (nombre de usuario)."""

    def __init__(self):
        super().__init__('nombre')

    def __eq__(self, other):
        return isinstance(other, ValidarSoloLetrasYEspacios)


@deconstructible
class ValidarCorreoPermitido:
    """Exige un correo bien formado y sin signos ajenos al formato de correo."""

    message = _(
        'El correo debe ser válido y usar solamente letras, números, punto, '
        'guión, guion bajo y la arroba. Sin otros caracteres especiales.'
    )
    code = 'correo_no_valido'

    def __call__(self, value):
        """Valida ``value`` contra el patrón de correo permitido."""
        if value and not _CORREO_PERMITIDO.match(str(value).strip().lower()):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


@deconstructible
class ValidarTelefono:
    """Teléfono con 7 a 15 dígitos; ``+`` inicial y espacios permitidos."""

    message = _(
        'Escribe un teléfono válido: entre 7 y 15 dígitos. '
        'Puedes empezar con + y separar con espacios. Ejemplo: 300 123 4567.'
    )
    code = 'telefono_no_valido'

    def __call__(self, value):
        """Rechaza letras y signos, y comprueba la longitud real de dígitos."""
        if not value:
            return
        valor = normalizar_espacios(value)
        if not _TELEFONO.match(valor):
            raise ValidationError(self.message, code=self.code)
        digitos = valor.lstrip('+').replace(' ', '')
        if not TELEFONO_DIGITOS_MIN <= len(digitos) <= TELEFONO_DIGITOS_MAX:
            raise ValidationError(self.message, code=self.code)
        if len(digitos) == 10 and not digitos.startswith('3'):
            raise ValidationError(
                _('Un celular colombiano de 10 dígitos debe empezar por 3. '
                  'Ejemplo: 3001234567.'),
                code='celular_colombiano_no_valido',
            )

    def __eq__(self, other):
        return isinstance(other, self.__class__)


@deconstructible
class ValidarDireccion:
    """Dirección con letras, un número y caracteres usuales de Colombia."""

    message = _(
        'Escribe una dirección válida con letras y número. '
        'Ejemplo: Calle 50 # 43-20, Medellín.'
    )
    code = 'direccion_no_valida'

    def __call__(self, value):
        """Rechaza texto sin sentido como 'mhv mvjhgm'."""
        if not value:
            return
        valor = normalizar_espacios(value)
        if not DIRECCION_MIN <= len(valor) <= DIRECCION_MAX:
            raise ValidationError(self.message, code=self.code)
        if not _DIRECCION.match(valor):
            raise ValidationError(self.message, code=self.code)
        if not re.search(r'[^\W\d_]', valor) or not re.search(r'\d', valor):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


def validadores_persona(campo):
    """Devuelve los validadores compartidos para nombre y apellido."""
    # La longitud máxima la añade Django desde ``max_length`` del modelo/form;
    # repetirla aquí mostraría dos errores distintos para el mismo problema.
    return [MinLengthValidator(NOMBRE_MIN), ValidarNombrePersona(campo)]


def validadores_nombre():
    """Validadores del campo ``nombre`` de ``Usuario``."""
    return validadores_persona('nombre')


def validadores_apellido():
    """Validadores del campo ``apellido`` de ``Usuario``."""
    return validadores_persona('apellido')


def validadores_correo():
    """Validadores del campo ``correo`` de ``Usuario``."""
    return [MinLengthValidator(CORREO_MIN), ValidarCorreoPermitido()]


def validadores_telefono():
    """Validador de teléfono reutilizable en todos los formularios."""
    return [ValidarTelefono()]


def validadores_direccion():
    """Validador de dirección reutilizable en pedidos y locales."""
    return [ValidarDireccion()]


def validadores_precio():
    """Precio decimal no negativo, con dos decimales y un tope razonable."""
    return [
        DecimalValidator(10, 2),
        MinValueValidator(Decimal('0')),
        MaxValueValidator(PRECIO_MAX),
    ]


def validadores_cantidad(maximo=CANTIDAD_MAX):
    """Cantidad entera entre 1 y ``maximo``."""
    return [MinValueValidator(1), MaxValueValidator(maximo)]


def validador_texto_largo(maximo):
    """Validador de longitud para ``TextField`` que antes no tenían límite."""
    return MaxLengthValidator(maximo)
