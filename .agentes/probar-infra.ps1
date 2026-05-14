# PRUEBA SEGURA DE INFRAESTRUCTURA DE AGENTES
# No lanza orquestadores en bucle. Sirve para validar antes de reiniciar todo.

$base = "C:\Users\USUARIO\iporave-sistema"
Set-Location $base

Write-Host "== Iporave: prueba segura de infraestructura ==" -ForegroundColor Cyan

$parada = Join-Path $base ".agentes\PARADA_CRITICA.txt"
if (Test-Path $parada) {
  Write-Host "OK: PARADA_CRITICA activa. Los agentes deben seguir dormidos." -ForegroundColor Yellow
} else {
  Write-Host "ADVERTENCIA: PARADA_CRITICA no existe. Crear antes de hacer pruebas largas." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "1) Validando frontend..." -ForegroundColor Cyan
node validate.js
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: validate.js fallo. No continuar." -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "2) Buscando Python..." -ForegroundColor Cyan
$pythonCmd = $null
$pythonExe = $null
$pythonPrefixArgs = @()
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
  $pythonCmd = "py -3"
  $pythonExe = "py"
  $pythonPrefixArgs = @("-3")
} else {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $pythonCmd = "python"
    $pythonExe = "python"
  } else {
    $qgisPython = @(
      "C:\Program Files\QGIS 3.38.0\apps\Python312\python.exe",
      "C:\Program Files\QGIS 3.38.0\bin\python.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($qgisPython) {
      $pythonCmd = $qgisPython
      $pythonExe = $qgisPython
    } else {
      $pythonCmd = $null
      $pythonExe = $null
    }
  }
}

if (-not $pythonCmd) {
  Write-Host "ERROR: Python no esta disponible. Los agentes Python no pueden arrancar." -ForegroundColor Red
  exit 1
}
Write-Host "OK: Python detectado: $pythonCmd" -ForegroundColor Green

Write-Host ""
Write-Host "3) Probando sintaxis Python..." -ForegroundColor Cyan
& $pythonExe @pythonPrefixArgs -m py_compile .agentes\model_pool.py .agentes\cerebro-monitor.py .agentes\telegram-bridge.py .agentes\orquestador-supervisor.py .agentes\orq_base.py
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: hay errores de sintaxis Python." -ForegroundColor Red
  exit 1
}
Write-Host "OK: sintaxis Python correcta." -ForegroundColor Green

Write-Host ""
Write-Host "4) Probando pool de modelos..." -ForegroundColor Cyan
& $pythonExe @pythonPrefixArgs .agentes\model_pool.py
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: model_pool.py fallo." -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "5) Probando cerebro-monitor una sola vez..." -ForegroundColor Cyan
& $pythonExe @pythonPrefixArgs .agentes\cerebro-monitor.py --test
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR: cerebro-monitor --test fallo." -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "TODO OK: infraestructura lista para reinicio controlado." -ForegroundColor Green
