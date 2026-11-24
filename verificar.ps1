# Comprobaciones rápidas antes de la prueba de caja blanca/negra.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $raiz '.venv\Scripts\python.exe'
$proyecto = Join-Path $raiz 'lookby_proyecto'

Push-Location $proyecto
try {
    Write-Host '== django check ==' -ForegroundColor Cyan
    & $py manage.py check
    Write-Host '== migraciones pendientes ==' -ForegroundColor Cyan
    & $py manage.py makemigrations --check --dry-run
    Write-Host '== tests ==' -ForegroundColor Cyan
    & $py manage.py test --noinput
}
finally {
    Pop-Location
}
