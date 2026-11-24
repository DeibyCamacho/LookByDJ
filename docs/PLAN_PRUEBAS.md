# Plan de pruebas LookBy (caja blanca / caja negra)

## Cómo ejecutar

```powershell
.\verificar.ps1                       # check + migraciones + tests
.\ejecutar.ps1                        # levanta el servidor en 127.0.0.1:8000
```

Usuarios demo (todos con contraseña `demo1234`): `admin@lookby.com` (admin),
`carlos@lookby.com` (profesional) y `ana@lookby.com` (cliente).

---

## Pruebas de caja negra (sin ver código, desde el navegador)

| # | Caso | Pasos | Resultado esperado |
|---|---|---|---|
| 1 | Registro | `/usuarios/registro/` con correo nuevo y contraseñas iguales | Redirige a `/usuarios/perfil/` y crea el usuario |
| 2 | Registro duplicado | Repetir el mismo correo con otra capitalización | Error: "Ya existe un usuario con ese correo" |
| 3 | Login/Logout | Entrar con `ana@lookby.com`, luego Salir | Perfil visible; tras Salir no se puede entrar a `/perfil/` |
| 4 | Local sin permiso | Usuario cliente intenta `/locales/<id>/editar/` | 403 (o redirección a login si no ha entrado) |
| 5 | Crear local | Cliente autenticado crea un local | Queda guardado con `idUsuario` = cliente; **el cliente NO se vuelve admin global** |
| 6 | Catálogos restringidos | Cliente intenta `/inventario/`, `/proveedores/` | Redirección a login / acceso denegado |
| 7 | Reservar cita | Cliente elige oferta y fecha futura | Redirige a `/citas/`, aparece la cita con precio de la oferta |
| 8 | Cita solapada | Reservar otra cita del mismo profesional 30 min después | Error de validación, no se guarda |
| 9 | Citas ajenas | Cliente A intenta ver `/citas/` de cliente B | Solo ve las suyas; anónimo no ve ninguna |
| 10 | Pedido con stock | Cliente crea pedido con producto de un local | Total calculado por el servidor, stock descontado |
| 11 | Pedido otro local | Enviar un `inventario` de otro local en el formulario | Error amigable, **nunca HTTP 500** |
| 12 | Calificación inválida | Enviar puntuación 6 o 0 | Error de validación (constraint 1-5) |
| 13 | Calificación duplicada | Calificar dos veces el mismo local con el mismo usuario | Error: ya existe calificación |
| 14 | Mapa | `/mapas/` | Solo marcadores de locales activos con coordenadas; sin marcadores en [0,0] |
| 15 | API mapa | `/mapas/api/locales/` | JSON válido, sin filas con lat/long nulas |
| 16 | Admin seguro | Desde `/admin/` intentar borrar un pedido CONFIRMADO | No se permite |

---

## Pruebas de caja blanca (conociendo el código)

- `citas/services.py`: `crear_cita()` valida duración exacta, oferta activa, solapamiento y
  fechas pasadas; usa `transaction.atomic` y bloqueo sobre el profesional.
- `pedidos/services.py`: valida stock con `select_for_update`, calcula el total en servidor
  y nunca recibe el total desde el formulario.
- `calificaciones/models.py`: validadores 1-5 + `CheckConstraint` + `UniqueConstraint`
  parciales por cliente/local y cliente/profesional.
- `usuarios/permisos.py`: `es_admin()` y `admin_required` protegen las vistas de catálogos.
- `locales/models.py`: `puede_administrar()` considera FK `usuario`, M2M y superusuarios.
- `mapas/migrations/0003_vista_mapa_locales.py`: la vista SQL filtra `activo` y coordenadas.

Comandos útiles:

```powershell
.\.venv\Scripts\python.exe lookby_proyecto\manage.py test
.\.venv\Scripts\python.exe lookby_proyecto\manage.py test citas pedidos calificaciones usuarios locales -v 2
.\.venv\Scripts\python.exe lookby_proyecto\manage.py shell
```

En el shell, ejemplos de comprobación rápida:

```python
from django.contrib.auth import get_user_model
from pedidos.models import Pedido
from citas.models import Cita
U = get_user_model()
print(U.objects.count(), Pedido.objects.count(), Cita.objects.count())
```
