# INICIAR SUPERVISOR + TELEGRAM BRIDGE + CEREBRO
# Uso: desde C:\Users\USUARIO\iporave-sistema ejecutar:
# .\.agentes\iniciar-todos.ps1

$base = "C:\Users\USUARIO\iporave-sistema"

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
  $pythonCmd = "py -3"
  $pythonExe = "py"
  $pythonArgs = "-3"
} else {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $pythonCmd = "python"
    $pythonExe = "python"
    $pythonArgs = ""
  } else {
    $qgisPython = @(
      "C:\Program Files\QGIS 3.38.0\apps\Python312\python.exe",
      "C:\Program Files\QGIS 3.38.0\bin\python.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($qgisPython) {
      $pythonCmd = $qgisPython
      $pythonExe = $qgisPython
      $pythonArgs = ""
    } else {
      Write-Host "No se encontro Python en PATH ni en QGIS. Instala Python o agrega python/py al PATH antes de iniciar agentes." -ForegroundColor Red
      exit 1
    }
  }
}

$pythonCall = "`"$pythonExe`""
if ($pythonArgs) { $pythonCall = "$pythonCall $pythonArgs" }

$parada = Join-Path $base ".agentes\PARADA_CRITICA.txt"
if (Test-Path $parada) {
  Write-Host "PARADA_CRITICA activa. No se inicia ningun agente." -ForegroundColor Red
  Write-Host "Archivo: $parada" -ForegroundColor Yellow
  Write-Host "Borrarlo solo cuando las pruebas manuales pasen correctamente." -ForegroundColor Yellow
  exit 1
}

Write-Host "Iniciando Supervisor Iporave..." -ForegroundColor Cyan
Write-Host "El supervisor lanza y vigila los orquestadores." -ForegroundColor Gray

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$base'; $pythonCall .agentes\orquestador-supervisor.py" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "Iniciando Cerebro-Monitor (analisis cada 30 min)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$base'; $pythonCall .agentes\cerebro-monitor.py" -WindowStyle Normal

Write-Host ""
Write-Host "Listo. Supervisor + Cerebro-Monitor iniciados." -ForegroundColor Green
Write-Host "Alertas: .agentes\alerts.json" -ForegroundColor DarkCyan
Write-Host "Cerebro: Gemini AI Studio, ciclo 30 min / 10 min con errores" -ForegroundColor DarkCyan
Write-Host "Pizarron: https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
