param(
    [string]$VenvActivate = "H:\\venv\\ecommerce\\Scripts\\Activate.ps1",
    [string]$BackendDir = ".\\backend",
    [string]$ServerHost = "0.0.0.0:8000"
)

try {
    $activateFull = Resolve-Path $VenvActivate -ErrorAction Stop
} catch {
    Write-Error "No se encontró el archivo de activación: $VenvActivate"
    exit 1
}

Write-Host "Activando entorno virtual: $($activateFull.Path)"
. $activateFull.Path

if (-not (Test-Path $BackendDir)) {
    Write-Error "No existe el directorio $BackendDir"
    exit 1
}
Set-Location $BackendDir

Write-Host "Ejecutando: python manage.py runserver $ServerHost"
python manage.py runserver $ServerHost
