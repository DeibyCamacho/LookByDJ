# LookByDJ

Plataforma web de servicios y productos de belleza construida con **Django 6.1** y **PostgreSQL 17**.
Incluye registro de usuarios, locales, profesionales, servicios, citas, productos, inventario,
proveedores, catálogos, pedidos, calificaciones y mapa (vista SQL `vw_mapa_locales`).

---

## 1. Requisitos

- Python 3.12+ (probado con Python 3.14)
- PostgreSQL 17 (instalado en `C:\Program Files\PostgreSQL\17`)
- Las dependencias de `requirements.txt`

## 2. Instalación rápida (Windows / PowerShell)

Desde la carpeta del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env      # si no existe; ajusta credenciales si quieres
cd lookby_proyecto
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py cargar_demo
..\.venv\Scripts\python.exe manage.py runserver
cd ..
```

Abrir <http://127.0.0.1:8000/>.

También puedes usar el script `.\ejecutar.ps1` que hace todo lo anterior.

## 3. Base de datos

`lookby_proyecto/lookby_proyecto/settings.py` lee la configuración del archivo `.env`
(que **no se sube a GitHub**, está en `.gitignore`):

| Variable | Valor por defecto |
|---|---|
| `DB_NAME` | `lookby` |
| `DB_USER` | `lookby` |
| `DB_PASSWORD` | `lookby123` |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |

Para crear la base y el usuario desde cero como superusuario `postgres`:

```sql
CREATE USER lookby WITH PASSWORD 'lookby123' CREATEDB;
CREATE DATABASE lookby OWNER lookby;
GRANT ALL PRIVILEGES ON DATABASE lookby TO lookby;
```

En PostgreSQL 15+ además ejecutar dentro de la base `lookby`:

```sql
GRANT ALL ON SCHEMA public TO lookby;
```

## 4. Usuarios de demostración

El comando `cargar_demo` crea datos de prueba (idempotente: se puede ejecutar varias veces).

| Correo | Contraseña | Rol |
|---|---|---|
| admin@lookby.com | `demo1234` | ADMINISTRADOR |
| carlos@lookby.com | `demo1234` | PROFESIONAL |
| ana@lookby.com | `demo1234` | CLIENTE |

`demo1234` es la contraseña **inicial**, solo para desarrollo. `cargar_demo` ya no
sobrescribe contraseñas cambiadas: si vuelves a ejecutarlo, tus claves se conservan.
Antes de desplegar, cambia las tres claves y define `DJANGO_DEBUG=0`, una
`DJANGO_SECRET_KEY` larga y `DJANGO_ALLOWED_HOSTS`.

### Recuperación y cambio de contraseña

- `/usuarios/recuperar/` envía un enlace válido por una hora (en desarrollo se
  imprime en la consola; en producción usa SMTP por variables de entorno).
- `/usuarios/cambiar-clave/` permite cambiar la contraseña estando logueado.
- El login bloquea temporalmente tras 5 intentos fallidos y nunca revela si una
  cuenta existe o está desactivada.

### Norma de nombres de usuario (calidad)

Se aplica igual en el registro, en "Mi perfil" y en la edición desde el administrador:

| Campo | Regla |
|---|---|
| `nombre` | De **3 a 30 caracteres**. Solo **letras y espacios**. Sin números ni signos (`@`, `.`, `-`, `_`, etc.). Las tildes y la `ñ` cuentan como letras, así que `José` y `Dueño` son válidos. |
| `correo` | De **3 a 30 caracteres**, con formato de correo. Solo letras, números, punto, guión, guion bajo, más y la arroba. |
| `apellido` | De **3 a 30 caracteres**, con la **misma regla que `nombre`** (letras y espacios). |
| `telefono` | De **7 a 15 dígitos**; se admite `+` inicial y espacios. Un celular colombiano de 10 dígitos debe empezar por 3. |

- Válidos: `Ana María`, `José Dueño`, `ana@lookby.com`, `300 123 4567`.
- Inválidos: `Ana1`, `Ana@`, `Juan-Pérez`, `ana#1@lookby.com`, `*+?-}{1234`, `hola soyun numero`.

La regla está en `usuarios/validators.py`, se aplica en el modelo (migraciones
`0004` y `0005`) y se muestra como texto de ayuda en los formularios. La migración
`0005` sanea los datos legacy antes de encoger las columnas.
Documentación completa: [`docs/NORMA_NOMBRES_USUARIO.md`](docs/NORMA_NOMBRES_USUARIO.md).

### Verificación integral del 26/11/2026

- [`docs/VERIFICACION_CORRECCIONES_2026-11-26.md`](docs/VERIFICACION_CORRECCIONES_2026-11-26.md): hallazgos, cambios, migraciones, 195 pruebas y verificación manual de cada corrección.
- [`docs/SEGURIDAD_Y_CONFIGURACION.md`](docs/SEGURIDAD_Y_CONFIGURACION.md): variables de entorno, `check --deploy`, páginas de error, login y contraseñas.

## 5. Módulos y rutas

| Módulo | Ruta principal |
|---|---|
| Inicio | `/` |
| Usuarios | `/usuarios/` |
| Locales | `/locales/` |
| Profesionales | `/profesionales/` |
| Servicios y ofertas | `/servicios/` |
| Citas | `/citas/` |
| Productos | `/productos/` |
| Inventario | `/inventario/` |
| Proveedores | `/proveedores/` |
| Catálogos | `/catalogos/` |
| Pedidos | `/pedidos/` |
| Calificaciones | `/calificaciones/` |
| Mapa | `/mapas/` |
| API JSON del mapa | `/mapas/api/locales/` |
| Administración | `/admin/` |

## 6. Reglas de negocio implementadas

- **Citas**: no se permiten solapamientos del mismo profesional, la duración debe coincidir
  con la oferta, no se aceptan fechas pasadas y se valida el horario cuando existe.
- **Pedidos**: el servidor calcula el total (nunca se confía en el navegador), se valida el
  stock con bloqueo de fila (`select_for_update`) y el inventario debe pertenecer al local
  del pedido. Los pedidos confirmados no se borran desde el admin.
- **Calificaciones**: puntuación entera 1 a 5, se exige local o profesional y se evitan
  duplicados del mismo cliente sobre el mismo objetivo (constraints en PostgreSQL).
- **Permisos**: las acciones de escritura exigen inicio de sesión; la administración de
  catálogos exige rol ADMINISTRADOR; cada cliente solo ve sus citas y pedidos.
- **Mapa**: la vista SQL `vw_mapa_locales` solo publica locales activos con coordenadas.

## 7. Pruebas

```powershell
cd lookby_proyecto
..\.venv\Scripts\python.exe manage.py test
..\.venv\Scripts\python.exe manage.py check
cd ..
```

O simplemente ejecuta `.\verificar.ps1` desde la raíz: hace `check`,
`makemigrations --check --dry-run` y la suite completa.

## 8. Estructura

```
LookByDJ/
├── .env                       # credenciales locales (NO versionar)
├── .env.example
├── ejecutar.ps1
├── verificar.ps1
├── requirements.txt
└── lookby_proyecto/
    ├── manage.py
    ├── lookby_proyecto/       # settings, urls, wsgi, asgi
    ├── templates/base.html
    ├── usuarios/ locales/ profesionales/ servicios/ citas/
    ├── productos/ inventario/ proveedores/ catalogos/ pedidos/
    └── calificaciones/ mapas/ inicio/
```
