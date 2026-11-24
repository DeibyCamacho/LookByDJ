"""Genera el informe final del proyecto LookBy en PDF."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "INFORME_FINAL_LookBy.pdf"

PURPLE = colors.HexColor("#873DE0")
PURPLE_DARK = colors.HexColor("#51228F")
PURPLE_LIGHT = colors.HexColor("#F3E9FC")
BLACK = colors.HexColor("#100D20")
GRAY = colors.HexColor("#5B5566")
BORDER = colors.HexColor("#D8D2DF")
OK = colors.HexColor("#166534")
OK_BG = colors.HexColor("#DCFCE7")

styles = getSampleStyleSheet()
s_title = ParagraphStyle(
    "Titulo", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=31, textColor=PURPLE_DARK, spaceAfter=6,
)
s_subtitle = ParagraphStyle(
    "Subtitulo", parent=styles["Normal"], fontName="Helvetica",
    fontSize=12, leading=17, textColor=GRAY, alignment=TA_CENTER,
)
s_h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=14, leading=18, textColor=PURPLE_DARK,
    spaceBefore=16, spaceAfter=8,
)
s_h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11.5, leading=15, textColor=PURPLE_DARK,
    spaceBefore=11, spaceAfter=5,
)
s_body = ParagraphStyle(
    "Cuerpo", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.7, leading=14.2, textColor=BLACK, alignment=TA_LEFT,
    spaceAfter=5,
)
s_bullet = ParagraphStyle(
    "Viñeta", parent=s_body, leftIndent=14, bulletIndent=4, spaceAfter=3,
)
s_small = ParagraphStyle(
    "Pequeño", parent=s_body, fontSize=8.6, leading=12, textColor=GRAY,
)
s_cell = ParagraphStyle("Celda", parent=s_body, fontSize=9, leading=12.5, spaceAfter=0)
s_cell_head = ParagraphStyle(
    "CeldaCabecera", parent=s_cell, fontName="Helvetica-Bold",
    textColor=colors.white, fontSize=9,
)


def par(texto, estilo=s_body):
    return Paragraph(texto, estilo)


def bullet(texto):
    return Paragraph(texto, s_bullet, bulletText="•")


def tabla(cabeceras, filas, anchos):
    datos = [[par(c, s_cell_head) for c in cabeceras]]
    datos += [[par(c, s_cell) for c in fila] for fila in filas]
    t = Table(datos, colWidths=anchos, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE_DARK),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PURPLE_LIGHT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(estilo))
    return t


def cabecera_pie(canvas, doc):
    canvas.saveState()
    ancho, alto = A4
    canvas.setFillColor(PURPLE_DARK)
    canvas.rect(0, alto - 0.35 * cm, ancho, 0.35 * cm, stroke=0, fill=1)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(PURPLE_DARK)
    canvas.drawString(2 * cm, alto - 0.85 * cm, "LOOKBY  |  INFORME FINAL DEL PROYECTO")
    canvas.drawRightString(ancho - 2 * cm, alto - 0.85 * cm, "feature/conectar-fks")
    canvas.setStrokeColor(BORDER)
    canvas.line(2 * cm, 1.25 * cm, ancho - 2 * cm, 1.25 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(2 * cm, 0.85 * cm, "Generado el 23 de noviembre de 2026")
    canvas.drawRightString(ancho - 2 * cm, 0.85 * cm, "Página %d" % doc.page)
    canvas.restoreState()


historia = []

# --- Portada ---
historia += [Spacer(1, 2.2 * cm)]
historia += [par("LookBy", s_title)]
historia += [par("Informe final de desarrollo, integración y verificación", s_subtitle)]
historia += [Spacer(1, 0.5 * cm)]
historia += [HRFlowable(width="100%", thickness=1.2, color=PURPLE)]
historia += [Spacer(1, 1.0 * cm)]

estado = Table(
    [[par("ESTADO DEL PROYECTO", s_cell_head),
      par("COMPLETADO Y EN FUNCIONAMIENTO", ParagraphStyle(
          "EstadoValor", parent=s_cell, fontName="Helvetica-Bold",
          textColor=OK, fontSize=10.5))]],
    colWidths=[6 * cm, 10.5 * cm],
)
estado.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (0, 0), PURPLE_DARK),
    ("BACKGROUND", (1, 0), (1, 0), OK_BG),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 9),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
]))
historia += [estado, Spacer(1, 0.9 * cm)]

historia += [tabla(
    ["Dato", "Detalle"],
    [
        ["Proyecto", "LookByDJ — aplicación web de servicios de belleza y barbería"],
        ["Rama Git", "feature/conectar-fks (actualizada y sin cambios pendientes)"],
        ["Último commit", "f9069e4 — Unifica el diseño de catálogos y listados con el tema global"],
        ["Servidor", "http://127.0.0.1:8000/ (activo)"],
        ["Base de datos", "PostgreSQL 17 — base lookby, usuario lookby, puerto 5432"],
        ["Pruebas", "118/118 tests superados contra PostgreSQL real"],
    ],
    [4 * cm, 12.5 * cm],
)]

historia += [Spacer(1, 0.8 * cm)]
historia += [par(
    "Este documento resume todo el trabajo realizado para dejar la aplicación terminada, "
    "conectada a PostgreSQL, visualmente corregida y lista para las pruebas de caja blanca "
    "y caja negra.", s_body)]

historia += [PageBreak()]

# --- 1. Resumen ejecutivo ---
historia += [par("1. Resumen ejecutivo", s_h1)]
historia += [par(
    "Se completaron los 13 módulos funcionales de LookBy, se corrigieron los fallos críticos "
    "detectados, se migró la persistencia a PostgreSQL con todas sus migraciones aplicadas y "
    "se cargaron datos de demostración. Posteriormente se corrigió el diseño de las pantallas "
    "de acceso (inicio de sesión y registro), que se superponían, y se unificó el aspecto de "
    "los catálogos y listados con el resto de la aplicación.", s_body)]
historia += [par(
    "El resultado es una aplicación estable, ejecutándose en local y con todo el código "
    "publicado en la rama <b>feature/conectar-fks</b> del repositorio GitHub.", s_body)]

# --- 2. Estado final ---
historia += [par("2. Estado final del sistema", s_h1)]
historia += [tabla(
    ["Componente", "Estado", "Verificación"],
    [
        ["Servidor web", "Activo", "HTTP 200 en / , /productos/ y /catalogos/"],
        ["PostgreSQL", "Conectado", "Migraciones aplicadas, incluida la vista vw_mapa_locales"],
        ["Datos demo", "Cargados", "Comando cargar_demo idempotente"],
        ["Tests", "OK", "118/118 en 241 s contra base real"],
        ["django check", "OK", "0 errores, 0 avisos"],
        ["Navegador", "OK", "9 páginas sin errores de consola + API JSON del mapa"],
        ["Git", "Sincronizado", "Rama limpia, push confirmado"],
    ],
    [3.6 * cm, 3 * cm, 9.9 * cm],
)]

# --- 3. Módulos ---
historia += [par("3. Módulos completados", s_h1)]
historia += [par(
    "Los 13 módulos quedaron operativos con sus operaciones CRUD, validaciones y reglas de "
    "negocio: <b>usuarios, locales, profesionales, servicios, citas, productos, inventario, "
    "proveedores, catálogos, pedidos, calificaciones, mapas e inicio</b>.", s_body)]

historia += [par("3.1 Correcciones funcionales relevantes", s_h2)]
for texto in [
    "Evitada la fuga de citas ajenas: cada usuario solo ve las suyas.",
    "Corregida la escalada de privilegios al crear un local.",
    "Eliminado el HTTP 500 en pedidos cuando el inventario pertenecía a otro local.",
    "Corregidos los precios vacíos en el listado de productos.",
    "Bloqueado el borrado de pedidos ya confirmados.",
    "Añadidas validaciones de horarios, solapes de citas, stock y calificaciones.",
    "Filtrado correcto del mapa (solo locales activos con coordenadas válidas).",
]:
    historia += [bullet(texto)]

# --- 4. Base de datos ---
historia += [par("4. Base de datos y migraciones", s_h1)]
historia += [par(
    "Se instaló PostgreSQL 17 y se creó la base <b>lookby</b> con el usuario <b>lookby</b> "
    "(contraseña <b>lookby123</b>) en el puerto <b>5432</b>. Se aplicaron todas las migraciones "
    "de los 17 grupos de aplicaciones, incluida la migración <b>locales/0004_alter_local_usuario.py</b> "
    "y la vista SQL <b>vw_mapa_locales</b> del módulo de mapas.", s_body)]
historia += [par(
    "Las credenciales reales se guardan únicamente en el archivo local <b>.env</b>, que está "
    "excluido del repositorio. En GitHub solo se versionó <b>.env.example</b> como plantilla.", s_body)]

historia += [PageBreak()]

# --- 5. Diseño ---
historia += [par("5. Correcciones de diseño e interfaz", s_h1)]

historia += [par("5.1 Inicio de sesión y registro", s_h2)]
historia += [par(
    "Los enlaces «Registrarse» e «Iniciar sesión» se apilaban uno encima del otro y desbordaban "
    "el ancho de la página porque <b>.nav-actions</b> no tenía ninguna regla CSS. Se corrigió "
    "con un contenedor flex, separación de 8 px y alineación superior (un poco más arriba que el "
    "resto del menú, como se solicitó). Además, ambos formularios se encuadraron en una tarjeta "
    "centrada de 460 px. Se añadió un cache-buster (<b>?v=3</b>) al CSS para evitar que el "
    "navegador sirviera una versión antigua.", s_body)]

historia += [par("5.2 Catálogos y listados", s_h2)]
historia += [par(
    "Las páginas de productos, catálogos, inventario y pedidos tenían estilos inline propios "
    "(otra fuente, otro fondo y títulos con borde rojo) que las hacían ver distintas al resto. "
    "Se eliminaron esos estilos y se rehicieron con las clases globales (<b>.contenido</b>, tabla "
    "y badges del tema morado). Ahora las cinco vistas comparten tipografía DM Sans, fondo, "
    "estilo de título y tabla, sin estilos inline.", s_body)]

historia += [par(
    "La verificación en navegador confirmó: mismos valores computados de fuente y color de "
    "fondo, ausencia de estilos inline, una tabla por listado y ningún desbordamiento horizontal.", s_small)]

# --- 6. Pruebas ---
historia += [par("6. Validación y pruebas", s_h1)]
historia += [tabla(
    ["Comprobación", "Resultado"],
    [
        ["manage.py check", "0 errores"],
        ["makemigrations --check", "Sin migraciones pendientes"],
        ["Suite completa", "118/118 tests OK (241,1 s)"],
        ["Rutas públicas", "200: /, /locales/, /profesionales/, /servicios/, /productos/, /catalogos/, /calificaciones/, /mapas/, /mapas/api/locales/"],
        ["Rutas protegidas", "302 a login sin sesión; 200 con sesión iniciada"],
        ["Mapa / API", "JSON con locales activos y coordenadas válidas"],
        ["Consola del navegador", "0 errores en las 9 páginas revisadas"],
    ],
    [4.3 * cm, 12.2 * cm],
)]

# --- 7. Entrega ---
historia += [par("7. Cómo usar la aplicación", s_h1)]
historia += [par(
    "Con la máquina encendida, el servicio PostgreSQL arranca automáticamente. Para levantar la "
    "aplicación basta con ejecutar desde la carpeta del proyecto:", s_body)]
historia += [par("<b>.\\ejecutar.ps1</b>", s_bullet)]
historia += [par(
    "Ese script instala dependencias si hace falta, aplica migraciones, carga los datos demo y "
    "levanta el servidor en <b>http://127.0.0.1:8000/</b>. Para verificar el estado se ejecuta "
    "<b>.\\verificar.ps1</b> (check, migraciones y tests).", s_body)]

historia += [par("7.1 Cuentas de demostración", s_h2)]
historia += [tabla(
    ["Correo", "Contraseña", "Rol"],
    [
        ["admin@lookby.com", "demo1234", "Administrador"],
        ["carlos@lookby.com", "demo1234", "Profesional"],
        ["ana@lookby.com", "demo1234", "Cliente"],
    ],
    [6.5 * cm, 4.5 * cm, 5.5 * cm],
)]

# --- 8. Git ---
historia += [par("8. Control de versiones", s_h1)]
historia += [par(
    "Todo el código fue publicado en la rama <b>feature/conectar-fks</b> del repositorio "
    "<b>https://github.com/DeibyCamacho/LookByDJ.git</b>. La rama quedó sincronizada con el "
    "remoto (sin cambios pendientes).", s_body)]
historia += [tabla(
    ["Commit", "Descripción"],
    [
        ["673f739", "Finaliza todos los módulos de LookBy y conecta PostgreSQL"],
        ["c054209", "Corrige comandos de instalación en README"],
        ["14429c6", "Corrige el diseño de acceso y la barra de navegación"],
        ["f9069e4", "Unifica el diseño de catálogos y listados con el tema global"],
    ],
    [3.2 * cm, 13.3 * cm],
)]

# --- 9. Conclusión ---
historia += [par("9. Conclusión", s_h1)]
historia += [par(
    "El proyecto LookBy está terminado, funcionando contra PostgreSQL y listo para la "
    "presentación y las pruebas. Las incidencias visuales reportadas (acceso superpuesto y "
    "catálogo con otro estilo) fueron corregidas y verificadas en navegador. El código está "
    "respaldado en la rama indicada y la documentación de apoyo se encuentra en "
    "<b>README.md</b> y <b>docs/PLAN_PRUEBAS.md</b> (16 casos de caja negra y checklist de "
    "caja blanca).", s_body)]

doc = SimpleDocTemplate(
    str(SALIDA), pagesize=A4,
    rightMargin=2 * cm, leftMargin=2 * cm,
    topMargin=1.7 * cm, bottomMargin=1.7 * cm,
    title="Informe final del proyecto LookBy",
    author="Equipo de desarrollo LookBy",
    subject="Desarrollo, integración y verificación final",
)
doc.build(historia, onFirstPage=cabecera_pie, onLaterPages=cabecera_pie)
print(f"PDF generado: {SALIDA}")
