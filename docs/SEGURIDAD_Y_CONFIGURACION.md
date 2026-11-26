# Seguridad, configuración y páginas de error — LookByDJ

**Fecha:** 26/11/2026. **Rama:** `feature/conectar-fks`.

## 1. Configuración por entorno

| Variable | Desarrollo | Producción | Uso |
|---|---|---|---|
| `DJANGO_DEBUG` | `1` | `0` (obligatorio) | Activa/desactiva modo debug y el resto de cabeceras seguras. |
| `DJANGO_SECRET_KEY` | valor local en `.env` | **obligatoria**, ≥ 50 caracteres aleatorios | Con `DEBUG=0`, si es corta la app falla al arrancar en vez de quedarse con una clave predecible. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | dominios reales separados por coma | Lista blanca de hosts. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` | — | SMTP real | Envío del correo de recuperación de contraseña. |
| `DEFAULT_FROM_EMAIL` | `LookBy <no-reply@lookby.local>` | remitente real | Remitente de los correos. |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` | — | `1` / `3600` por defecto | Redirección HTTPS y HSTS. |

En desarrollo el backend de correo es de **consola**: el enlace de recuperación se
imprime en la terminal, sin necesidad de servidor SMTP. En producción se usa SMTP.

## 2. `check --deploy`

Antes: **1 error + 6 avisos** (`mail.E001`, `security.W004/W008/W009/W012/W016/W018`,
más `W021` al endurecer HSTS). Después de los cambios:

```powershell
$env:DJANGO_DEBUG='0'
python lookby_proyecto\manage.py check --deploy
# System check identified no issues (0 silenced).
```

## 3. Páginas de error propias

`lookby_proyecto/urls.py` registra `handler400/403/404/413/500`. Las vistas viven
en `lookby_proyecto/vistas_error.py` y las plantillas en `templates/4xx.html`,
`templates/5xx.html`. Nunca muestran trazas, rutas absolutas ni SQL.

`ManejoPeticionesGrandesMiddleware` convierte `RequestDataTooBig` y
`TooManyFieldsSent` en un **413** con el diseño de LookBy. Los límites explícitos
son `DATA_UPLOAD_MAX_MEMORY_SIZE = 2 MB`, `DATA_UPLOAD_MAX_NUMBER_FIELDS = 200`
y `FILE_UPLOAD_MAX_MEMORY_SIZE = 2 MB`.

## 4. Login y contraseñas

- `EntrarView` cuenta intentos fallidos por IP + correo en caché. A los 5 intentos
  muestra: *"Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo."*
- El mensaje de error es genérico tanto para credenciales incorrectas como para
  cuentas inactivas: no se puede enumerar usuarios.
- Recuperación nativa de Django en `/usuarios/recuperar/`: mensaje genérico
  ("Si la cuenta existe…"), token de **una hora** (`PASSWORD_RESET_TIMEOUT=3600`),
  plantillas propias y cambio de clave autenticado en `/usuarios/cambiar-clave/`.
- `Usuario.EMAIL_FIELD = 'correo'`: sin esto, la recuperación de Django buscaba un
  campo `email` inexistente y fallaba con `FieldError`.
- `cargar_demo` solo asigna `demo1234` a cuentas **nuevas**; ejecutarlo otra vez ya
  no restablece contraseñas cambiadas a mano.
