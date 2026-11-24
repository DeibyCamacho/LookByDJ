# Ejecuta LookBy: migra PostgreSQL, carga datos demo y levanta el servidor.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $raiz '.venv\Scripts\python.exe'
$proyecto = Join-Path $raiz 'lookby_proyecto'
$manage = Join-Path $proyecto 'manage.py'

if (-not (Test-Path $py)) {
    python -m venv (Join-Path $raiz '.venv')
}
if (-not (Test-Path (Join-Path $raiz '.env'))) {
    Copy-Item (Join-Path $raiz '.env.example') (Join-Path $raiz '.env')
}

& $py -m pip install -r (Join-Path $raiz 'requirements.txt')
Push-Location $proyecto
try {
    & $py manage.py migrate
    & $py manage.py cargar_demo
    & $py manage.py runserver 127.0.0.1:8000
}
finally {
    Pop-Location
}
