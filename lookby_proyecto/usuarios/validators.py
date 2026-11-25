r"""Validadores de la norma de calidad de nombres y correos de LookBy.

Historia
--------
Requerimiento integrado el 25/11/2026 a petición del liderazgo del proyecto:
"los nombres de usuario no deben llevar caracteres especiales, con la longitud
preestablecida por calidad".

Regla oficial
-------------
=================  ==========================================================
Campo              Regla
=================  ==========================================================
``nombre``         De 3 a 30 caracteres. Solamente letras y espacios. Sin
                   números, guiones, puntos, arrobas, guiones bajos ni otros
                   signos. No se permiten espacios al inicio ni al final
                   (los formularios hacen ``strip`` antes de validar).
``correo``         De 3 a 30 caracteres. Formato de correo con una sola ``@``
                   y dominio con punto. Se admiten letras, números, ``.``,
                   ``-``, ``_`` y ``+`` como parte del correo; se rechazan
                   otros signos como ``#``, ``$``, ``!`` o comillas.
=================  ==========================================================

Notas de diseño
---------------
* Las tildes y la ``ñ`` se consideran **letras**, no caracteres especiales.
  Por eso ``José`` y ``Dueño`` son válidos y no se rompen los datos demo ni
  las pruebas existentes.
* ``[^\W\d_]`` es la forma Unicode de decir "letra": ``\w`` incluye letras,
  números y guion bajo, así que se excluyen explícitamente los dos últimos.
* Los validadores están decorados con :func:`~django.utils.deconstruct.
  deconstructible` para que Django pueda serializarlos en la migración
  ``0004_alter_usuario_correo_alter_usuario_nombre.py``.
* Django ejecuta estos validadores al validar formularios (registro, perfil y
  administración) y al llamar a ``Usuario.full_clean()``. Una escritura
  directa por ``QuerySet.update()`` o SQL crudo no pasa por ellos, igual que
  ocurre con cualquier validador de Django.
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

#: Longitud mínima aceptada para ``nombre`` y ``correo``.
NOMBRE_MIN = 3
#: Longitud máxima aceptada para ``nombre`` (también es el ``max_length`` del campo).
NOMBRE_MAX = 30
#: Longitud mínima aceptada para ``correo``.
CORREO_MIN = 3
#: Longitud máxima aceptada para ``correo`` (también es el ``max_length`` del campo).
CORREO_MAX = 30

# Una o más letras, separadas por grupos de espacios. Las tildes y la ñ entran
# en [^\W\d_] porque son letras Unicode.
_SOLO_LETRAS_Y_ESPACIOS = re.compile(r'^[^\W\d_]+(?: +[^\W\d_]+)*$')

# Los únicos signos permitidos son los que forman parte de un correo habitual.
# El dominio debe terminar en un TLD alfabético (com, co, org, edu, ...).
_CORREO_PERMITIDO = re.compile(
    r'^[A-Za-z0-9][A-Za-z0-9._+-]*@'
    r'[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?'
    r'(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$'
)


@deconstructible
class ValidarSoloLetrasYEspacios:
    """Rechaza números, signos y espacios sobrantes en el nombre de usuario.

    Se usa como validador del campo ``Usuario.nombre``. Recibe el valor ya
    limpio por el formulario (sin espacios al inicio ni al final), pero también
    hace ``strip()`` para funcionar correctamente si se llama desde ``full_clean()``.

    Raises:
        ValidationError: si el valor está vacío, contiene algo que no sea letra
            o espacio, o deja espacios entre palabras mal formados.
    """

    message = _(
        'El nombre solo puede contener letras y espacios. '
        'No se permiten números ni caracteres especiales.'
    )
    code = 'nombre_no_valido'

    def __call__(self, value):
        """Valida ``value``; los valores vacíos los gestiona Django por separado."""
        if value and not _SOLO_LETRAS_Y_ESPACIOS.match(str(value).strip()):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        """Necesario para que Django compare bien los validadores en migraciones."""
        return isinstance(other, self.__class__)


@deconstructible
class ValidarCorreoPermitido:
    """Exige un correo bien formado y sin signos ajenos al formato de correo.

    Django ya valida el formato básico con ``EmailValidator``; este validador
    añade la restricción extra de la norma de calidad (solo ``@``, punto,
    guión, guion bajo y más como signos permitidos).

    Raises:
        ValidationError: si el correo tiene signos no permitidos o no tiene
            dominio con punto.
    """

    message = _(
        'El correo debe ser válido y usar solamente letras, números, punto, '
        'guión, guion bajo y la arroba. Sin otros caracteres especiales.'
    )
    code = 'correo_no_valido'

    def __call__(self, value):
        """Valida ``value`` contra el patrón de correo permitido."""
        if value and not _CORREO_PERMITIDO.match(str(value).strip()):
            raise ValidationError(self.message, code=self.code)

    def __eq__(self, other):
        """Necesario para que Django compare bien los validadores en migraciones."""
        return isinstance(other, self.__class__)


def validadores_nombre():
    """Devuelve los validadores del campo ``nombre``.

    La longitud máxima no se incluye aquí porque Django la añade solo con
    ``max_length`` del modelo; así se evita duplicar el error en los formularios.

    Returns:
        list: ``MinLengthValidator(3)`` y ``ValidarSoloLetrasYEspacios``.
    """
    return [MinLengthValidator(NOMBRE_MIN), ValidarSoloLetrasYEspacios()]


def validadores_correo():
    """Devuelve los validadores del campo ``correo``.

    Returns:
        list: ``MinLengthValidator(3)`` y ``ValidarCorreoPermitido``.
        Django añade por su cuenta el validador de longitud máxima (30) y el
        validador de formato de correo.
    """
    return [MinLengthValidator(CORREO_MIN), ValidarCorreoPermitido()]
