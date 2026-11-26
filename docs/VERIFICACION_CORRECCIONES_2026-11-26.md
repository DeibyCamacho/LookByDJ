# Verificación de correcciones — LookByDJ (26/11/2026)

**Rama:** `feature/conectar-fks` · **Base:** `533d3f9` · **Repositorio:** `C:\Users\89_10102518578\OneDrive - Servicio Nacional de Aprendizaje\Documentos\LookBy`

Alcance acordado con el líder del proyecto: **todos los hallazgos P0 → P2 excepto A1**
(reparación de las relaciones legacy de `0002_conectar_fks`, diferida por riesgo).
Para los datos sucios se aplicó la opción elegida: **rellenar apellidos vacíos con
`Demo` y sanear los valores inválidos**.

---

## 1. Hallazgos confirmados antes de editar

La auditoría previa (25/11) enumeró 22 hallazgos P0/P1/P2 en
`VERIFICACION_QA_LookByDJ.md`. Antes de tocar código se confirmaron en la base real:

| Hallazgo | Evidencia real |
|---|---|
| Nombres/apellidos sucios | `juanyaracamelo04@gmail.com` → nombre `juan`, apellido `*+?-}{1234`, teléfono `hola soyun numero`; visible en Pedido #2 y Calificación #2. 5 apellidos vacíos (3 de demo). |
| Local sin límites | Local #2 con nombre de 150 caracteres, dirección de 200, teléfono de 25 con letras/signos y descripción de 27.368. |
| Textos sin tope | Calificación #2 con comentario de 15.505 caracteres; Catálogo #1 con descripción de 15.505. |
| Fallas de validación | Registro permitía `Ana1`, apellido vacío y teléfonos con letras; el servicio de pedidos confiaba en el total del navegador. |
| Login/contraseñas | No había recuperación ni cambio de clave; mensajes distintos para cuenta inexistente/inactiva; `cargar_demo` sobrescribía contraseñas. |
| Petición grande | Sin `DATA_UPLOAD_MAX_*` ni página 413 propia: un POST enorme podía terminar en traceback. |
| Mapa | Tiles de OpenStreetMap devolvían 403; un error de la vista SQL se silenciaba como "sin datos". |
| Permisos | Administradores ajenos podían editar/borrar calificaciones y gestionar inventario/catálogos de otros locales. |

## 2. Cambios por área (y por qué)

| Área | Archivos principales | Motivo |
|---|---|---|
| Validador único | `usuarios/validators.py` | Una sola definición reutilizable para nombre, apellido, correo, teléfono, dirección, precio, cantidad y textos largos. Clases `@deconstructible` con `__eq__` para que las migraciones no cambien solas. Mensajes en español, junto al campo. |
| Usuarios | `usuarios/{models,forms,views,urls}.py`, `usuarios/templates/**`, `usuarios/management/commands/cargar_demo.py` | Apellido obligatorio con la misma regla que nombre; teléfono 7–15 dígitos; normalización al guardar; `EMAIL_FIELD='correo'`; bloqueo de login tras 5 fallos; recuperación/cambio de clave nativos con plantillas propias; `demo1234` solo en cuentas nuevas. |
| Configuración y errores | `lookby_proyecto/{settings,urls,middleware,vistas_error}.py`, `templates/{400,403,404,413,500}.html`, `.env.example` | Cabeceras/cookies seguras, límites de petición, `PASSWORD_RESET_TIMEOUT=3600`, correo console/SMTP, logging, páginas de error sin trazas. |
| Locales y mapa | `locales/**`, `mapas/**` | Límites y validadores en modelo/formulario; ruta duplicada `locales:eliminar` eliminada (queda `desactivar`); `referrerPolicy`, `tileerror`, listado de respaldo con `textContent` (sin `innerHTML`) y estados `ok`/`sin_datos`/`fallo` con logging. |
| Pedidos, citas y calificaciones | `pedidos/**`, `citas/**`, `calificaciones/**` | Dirección obligatoria y cantidad 1–1000 en formulario **y servicio**; local/producto activos; total calculado en servidor; `atomic` + `select_for_update`; comentario ≤300; puntuación 1–5; solo el autor edita/borra; horario publicado obligatorio; cancelación atómica. |
| Resto del catálogo | `catalogos/**`, `inventario/**`, `productos/**`, `profesionales/**`, `proveedores/**`, `servicios/**` | Biografías/descripciones ≤500, precios ≥0 con tope, stock ≤100000, correo y teléfono de proveedor validados, comprobación de propiedad del local (IDOR), `select_related`/`prefetch_related`, paginación de 20 y consultas estables con `order_by('pk')`. |
| Interfaz y accesibilidad | plantillas de las apps, `inicio/static/inicio/css/home.css`, `templates/base.html` | Tablas desplazables con `scope`, estados vacíos, errores con `role="alert"`, contador de caracteres en `textarea[maxlength]`, `aria-live`, foco visible y diseño responsive. |

## 3. Migraciones y datos reales

Migraciones nuevas (todas **aplicadas** en la base local):

- `usuarios.0005` y `0006`: sanea apellidos y teléfonos, luego encoge columnas; la `0006` vacía teléfonos cortos que la primera versión conservaba.
- `locales.0005`: **RunPython de limpieza antes de los `AlterField`**; recorta nombre/dirección/ciudad/descripción y vacía teléfonos inválidos.
- `mapas.0004` y `0005`: quitan y recrean `VW_MAPA_LOCALES` alrededor de `locales.0005` (PostgreSQL no permite alterar columnas usadas por una vista).
- `calificaciones.0004` y `catalogos.0002`: recortan comentarios/descripciones antes de aplicar los validadores.
- `pedidos.0003`, `productos.0003`, `proveedores.0003`, `inventario.0003`, `profesionales.0002`, `servicios.0002`: límites y validadores.

Resultado verificado en la base real:

- Usuarios: apellidos `Demo`, sin apellidos vacíos ni teléfonos con letras.
- Local #2: nombre 80, dirección 149, teléfono vacío, descripción 500.
- Calificación #2: comentario 300. Catálogo #1: descripción 500.
- `VW_MAPA_LOCALES` existe y devuelve filas.

Copia de seguridad previa: `%TEMP%\lookby_backup_antes_migraciones_20261126.sql` (145 KB).

## 4. Verificación automática

Ejecutado desde `LookBy\lookby_proyecto` con el virtualenv del proyecto:

```
python manage.py check                       # System check identified no issues
python manage.py makemigrations --check --dry-run   # No changes detected
python manage.py test                        # Ran 195 tests ... OK
$env:DJANGO_DEBUG='0'; python manage.py check --deploy  # no issues (0 silenced)
```

Antes: `check --deploy` daba 1 error + 6 avisos (`mail.E001`, `security.W004/W008/W009/W012/W016/W018`, más `W021` al endurecer HSTS).
El único mensaje `ERROR lookby: No se pudo consultar VW_MAPA_LOCALES` durante los tests es **provocado a propósito** por el test que simula un fallo de BD; verifica que se registra en el log y no se filtra al visitante.

## 5. Verificación manual de cada corrección

1. **Nombre y apellido** — Registro, "Mi perfil" y admin: escribe `Ana   María` y guarda; queda `Ana María`. Prueba `Ana1`, `Juan-Pérez` y un apellido vacío: aparece el error junto al campo. `José Dueño` y `José Núñez` son válidos.
2. **Teléfono** — `300 123 4567` y `+573001234567` son válidos. `hola soyun numero`, `123456` y `3012345678` son rechazados. El teléfono de la cuenta demo sucia aparece vacío.
3. **Datos legacy** — Lista de usuarios y detalle de Pedido #2 / Calificación #2: el apellido ya es `Demo` y no aparecen signos raros.
4. **Login y contraseñas** — `/usuarios/recuperar/` con un correo existente: en desarrollo el enlace se imprime en consola; ábrelo (caduca en 1 hora) y cambia la clave. Repite con un correo inexistente: el mensaje es idéntico. En `/usuarios/cambiar-clave/` cambia la clave estando logueado. Falla 5 veces el login: aparece "Demasiados intentos fallidos…"; desactiva una cuenta y comprueba que el error es el mismo genérico. Ejecuta `python manage.py cargar_demo` otra vez: tus claves cambiadas se conservan.
5. **Límites de local y 413** — En "Registrar/editar local", supera 80 caracteres en nombre, 150 en dirección o 500 en descripción: el navegador limita y el servidor rechaza con mensaje en español. Envía un POST >2 MB (o >200 campos): se muestra la página 413 con el diseño de LookBy, sin traceback.
6. **Biografía y textareas** — Abre formularios de profesional/servicio/producto/catálogo/local/calificación: cada textarea muestra `n / 500 caracteres` (300 en comentarios) y el contador se acerca al límite. Guarda 501 caracteres por POST directo: el servidor lo rechaza.
7. **Pedidos** — Crea un pedido sin dirección o con menos de 10 caracteres: error en el campo. Pon cantidad 1001: error. Desactiva el local o el producto desde el admin y vuelve a intentarlo: mensaje claro, sin 500. Verifica que el total mostrado coincide con `precio × cantidad` calculado por el servidor y que el stock baja solo en ese local. Cancela dos veces la misma cita: la segunda falla con "Solo se pueden cancelar citas pendientes o confirmadas".
8. **Calificaciones** — Escribe 301 caracteres en el comentario: rechazado; usa puntuación 6 o 0: rechazado. Con un admin que no es el autor, intenta editar/borrar una calificación ajena: 404. En edición, manipula el POST para cambiar `local`/`profesional`: se conserva el objetivo original.
9. **Mapa** — Abre `/mapas/`: los tiles cargan sin 403 y la atribución © OpenStreetMap contributors sigue visible. Simula un error de tile (sin red): aparece el aviso y el listado de respaldo. Si la vista SQL no existiera, aparece "No pudimos consultar los datos del mapa…" sin trazas; `/mapas/api/` sigue devolviendo `{"locales": [...]}` con la misma forma.
10. **Stock por local y permisos** — Crea inventario del mismo producto en dos locales, administra solo el primero y comprueba que el segundo no se puede crear/editar/borrar (403). Confirma que un pedido de cada local descuenta únicamente su propio stock y que un `inventario_id` de otro local se rechaza. En móvil, las tablas se desplazan horizontalmente y los encabezados tienen `scope`.

## 6. Pendientes y decisiones documentadas

- **A1 (diferido por decisión explícita):** reparar relaciones legacy creadas por `0002_conectar_fks` con `RunPython`. Requiere decidir qué hacer con pedidos/citas huérfanos; se deja para una fase aparte.
- **Elegibilidad estricta de calificaciones:** `calificaciones/forms.py` mantiene `PERMITIR_DATOS_LEGACY_SIN_FINALIZAR = True` porque la app todavía no expone ninguna acción para marcar `Cita COMPLETADA` ni `Pedido ENTREGADO` (solo se puede desde el admin). Cuando exista esa transición, cambiar la constante a `False`: la regla se endurece sin más cambios.
- **Producción:** definir `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` ≥ 50 caracteres aleatorios, `DJANGO_ALLOWED_HOSTS`, SMTP real y HTTPS. La app falla al arrancar si se usa una clave corta con `DEBUG=0`.
- **Entorno local:** se otorgó `SUPERUSER` al rol `lookby` para poder aplicar migraciones DDL. En producción usa un rol con permisos de esquema, no superusuario. `pg_hba.conf` fue modificado temporalmente y **restaurado**; se recargó con `pg_reload_conf()` y vuelve a exigir contraseña (`scram-sha-256`).
- **Tiles externos:** el mapa depende de OpenStreetMap; el fallback cubre el error de tiles, pero no sustituye a un proveedor propio si se requiere funcionamiento sin internet.
- **Claves demo:** `demo1234` sigue siendo la clave inicial de desarrollo; cámbialas antes de cualquier despliegue.
