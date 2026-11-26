# Norma de nombres de usuario — LookByDJ

**Estado:** integrada en la rama `feature/conectar-fks` el 25/11/2026.
**Solicitada por:** Deiby Camacho (líder del proyecto).
**Objetivo:** evitar nombres de usuario con caracteres especiales y fijar una longitud estándar de calidad.

---

## 1. La regla

| Campo | Longitud | Caracteres permitidos | Caracteres prohibidos |
|---|---|---|---|
| `nombre` (nombre visible del usuario) | **3 a 30** | Letras (incluidas tildes y `ñ`) y espacios entre palabras | Números, `@`, `.`, `-`, `_`, `'`, `#`, cualquier otro signo. Espacios al inicio o al final |
| `correo` (login del usuario) | **3 a 30** | Letras, números, `@`, punto, guión, guion bajo y `+` | `#`, `$`, `!`, comillas, `%`, etc. Dos `@`, dominio sin punto |
| `apellido` (26/11/2026) | **3 a 30** | La **misma regla que `nombre`**: letras (tildes y `ñ`) y espacios | Números y signos. No puede quedar vacío |
| `telefono` (26/11/2026) | **7 a 15 dígitos** | Un `+` inicial, espacios y dígitos; celular CO de 10 dígitos empieza por 3 | Letras y signos distintos de `+` |

### Ejemplos

| Valor | Resultado | Motivo |
|---|---|---|
| `Ana` | ✅ válido | 3 letras |
| `Ana María` | ✅ válido | letras y un espacio |
| `José Dueño` | ✅ válido | las tildes y la `ñ` son letras |
| `ana@lookby.com` | ✅ válido | correo con signos permitidos |
| `An` | ❌ inválido | menos de 3 caracteres |
| `A` × 31 | ❌ inválido | más de 30 caracteres |
| `Ana1` | ❌ inválido | contiene un número |
| `Ana@` | ❌ inválido | contiene `@` |
| `Juan-Pérez` | ❌ inválido | contiene guión |
| `ana#1@lookby.com` | ❌ inválido | contiene `#` |

> **Decisión documentada:** las tildes y la `ñ` se tratan como letras, no como caracteres
> especiales. Si el equipo decide prohibirlas, se cambia el patrón
> `_SOLO_LETRAS_Y_ESPACIOS` en `usuarios/validators.py` por un patrón ASCII y se
> revisan los datos existentes antes de aplicar el cambio.

> **Actualización del 26/11/2026:** el apellido pasó de 40 a **30** caracteres y usa
> exactamente el mismo validador que el nombre (`ValidarNombrePersona`). Ya no hay
> dos reglas distintas para `nombre` y `apellido`. La migración `0005` sanea los
> datos legacy antes de encoger la columna: apellidos vacíos o con signos pasan a
> `Demo`, y teléfonos con letras pierden los caracteres no numéricos.

---

## 2. Dónde se aplica

| Punto de entrada | Mecanismo | Archivo |
|---|---|---|
| Registro web | `RegistroForm` → validadores del modelo | `usuarios/forms.py`, `usuarios/templates/usuarios/registro.html` |
| Edición de perfil | `PerfilForm` / `UsuarioEdicionForm` | `usuarios/forms.py`, `usuarios/templates/usuarios/perfil.html` |
| Edición desde administración | `UsuarioAdminForm` | `usuarios/forms.py`, `usuarios/templates/usuarios/form.html` |
| Django admin | `ModelForm` del admin usa el modelo | `usuarios/models.py` |
| Alta por código / shell / `createsuperuser` | `UsuarioManager._crear()` llama a `full_clean()` | `usuarios/models.py` |
| Base de datos | `max_length=30` en ambas columnas | `usuarios/migrations/0004_alter_usuario_correo_alter_usuario_nombre.py` |

La regla se define **una sola vez** en `usuarios/validators.py` y la consumen el modelo y los formularios. No hay copias del patrón en distintos archivos.

### Mensajes que ve el usuario

- Nombre inválido: *"El nombre solo puede contener letras y espacios. No se permiten números ni caracteres especiales."*
- Correo inválido: *"El correo debe ser válido y usar solamente letras, números, punto, guión, guion bajo y la arroba. Sin otros caracteres especiales."*
- Fuera de rango: los mensajes estándar de Django de longitud mínima (3) y máxima (30).

Los formularios muestran además un texto de ayuda generado a partir de las constantes `NOMBRE_MIN`, `NOMBRE_MAX`, `CORREO_MIN` y `CORREO_MAX`, así que no se desactualiza si cambian los límites.

---

## 3. Cambios realizados

| Archivo | Cambio |
|---|---|
| `lookby_proyecto/usuarios/validators.py` | **Nuevo.** Constantes, patrones y clases de validación de la norma. |
| `lookby_proyecto/usuarios/models.py` | Campos `nombre` y `correo` con nuevos límites y validadores; `full_clean()` en `_crear()`. |
| `lookby_proyecto/usuarios/forms.py` | Textos de ayuda y docstrings; sin lógica duplicada. |
| `lookby_proyecto/usuarios/migrations/0004_...py` | **Nueva.** `AlterField` de `correo` y `nombre` (la `0003` ya era del equipo). |
| `lookby_proyecto/usuarios/tests.py` | 9 pruebas nuevas (`NormaNombresTests`) y 4 pruebas de longitud ajustadas a nombre 30 / apellido 40 (`LongitudNombresTests`). |
| `lookby_proyecto/locales/tests.py` | Un dato de prueba cambiado de `Dueño 2` a `Dueño Dos` para cumplir la regla. |
| `README.md` | Apartado "Norma de nombres de usuario (calidad)". |
| `docs/NORMA_NOMBRES_USUARIO.md` | **Nuevo.** Este documento. |

---

## 4. Verificación ejecutada

| Comprobación | Resultado |
|---|---|
| `manage.py check` | ✅ 0 errores, 0 avisos |
| `manage.py makemigrations --check --dry-run` | ✅ `No changes detected` |
| `manage.py migrate` | ✅ `usuarios.0004_alter_usuario_correo_alter_usuario_nombre... OK` |
| `python -m compileall -q lookby_proyecto` | ✅ exit 0 |
| `manage.py test --noinput -v 1` | ✅ **131/131 tests OK** en 97,4 s (la rama tenía 122; se añadieron 9 de la norma) |

### Pruebas nuevas

1. Registro con nombre y correo válidos.
2. Registro con tildes y `ñ` (`José Dueño`).
3. Registro rechaza números y caracteres especiales (`Ana@`, `Ana_1`, `Ana-123`, `O'Brien`, `Ana.Maria`, `Juan2`).
4. Registro rechaza nombre corto (2) y largo (31).
5. Registro rechaza correo de 31 caracteres.
6. Registro rechaza correo con `#`.
7. La edición del perfil no guarda un nombre inválido.
8. `full_clean()` del modelo rechaza nombre y correo inválidos.
9. `Usuario.objects.create_user()` también aplica la norma.

---

## 5. Notas para el equipo

- **Antes de migrar una base con datos reales:** revisa que no existan nombres de más de 30 caracteres ni correos de más de 30 caracteres. PostgreSQL no puede acortar la columna si hay valores más largos. Consulta rápida:
  ```sql
  SELECT correo, length(correo) FROM usuarios_usuario WHERE length(correo) > 30;
  SELECT nombre, length(nombre) FROM usuarios_usuario WHERE length(nombre) > 30;
  ```
- La validación es de aplicación, como la mayoría de validadores de Django. Un `QuerySet.update()` o SQL directo puede escribir valores que no cumplen la regla; para esos casos usa `full_clean()` antes de guardar.
- Si se cambia el patrón de caracteres, hay que regenerar la migración porque los validadores forman parte del estado del modelo.
- Para aplicar el cambio en otro clon: `git apply CAMBIOS_NORMA_NOMBRES.patch` y luego `python manage.py migrate`.

---

## 6. Reversión

Para volver al estado anterior:

1. Borrar `0004_alter_usuario_correo_alter_usuario_nombre.py` y `usuarios/validators.py`.
2. Restaurar `nombre = models.CharField(max_length=100)` y `correo = models.EmailField('correo electrónico', unique=True)`.
3. Quitar `usuario.full_clean()` de `_crear()` y los `help_texts`.
4. Ejecutar `manage.py makemigrations usuarios` y aplicar la migración resultante (PostgreSQL permite ampliar la columna sin problema).
