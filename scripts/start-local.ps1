# Arranca API (puerto 8000) y Vite (5173) en ventanas nuevas. Ejecutar desde la raíz del repo:
#   .\scripts\start-local.ps1
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $ProjectRoot "backend"
$Frontend = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path (Join-Path $Backend "app\main.py"))) {
    Write-Error "No se encuentra backend\app\main.py. Ejecuta este script desde el repo EnmascaradoDatos (scripts\start-local.ps1)."
}

$venvActivate = Join-Path $Backend ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Host "Creando entorno virtual en backend\.venv ..." -ForegroundColor Yellow
    Push-Location $Backend
    try {
        python -m venv .venv
        & .\.venv\Scripts\pip.exe install -r requirements.txt
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "Instalando dependencias npm ..." -ForegroundColor Yellow
    Push-Location $Frontend
    try {
        npm install
    } finally {
        Pop-Location
    }
}

Write-Host "Iniciando backend en :8000 ..." -ForegroundColor Cyan
$backendCmd = "Set-Location '$Backend'; . '.venv\Scripts\Activate.ps1'; Write-Host 'Enmask API -> http://127.0.0.1:8000/docs' -ForegroundColor Green; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
$pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
$shellExe = if ($pwsh) { $pwsh.Source } else { "powershell" }
Start-Process -FilePath $shellExe -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

Write-Host "Iniciando frontend en :5173 ..." -ForegroundColor Cyan
$frontendCmd = "Set-Location '$Frontend'; Write-Host 'Enmask UI -> http://localhost:5173' -ForegroundColor Green; npm run dev"
Start-Process -FilePath $shellExe -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "Listo. Abre http://localhost:5173 y regístrate." -ForegroundColor Green
Write-Host "Si el login fallaba antes: cierra otros programas que usen el puerto 8000." -ForegroundColor DarkYellow
