$ErrorActionPreference = "Stop"

$base = "C:\Users\USUARIO\iporave-sistema"
$logDir = Join-Path $base ".agentes\logs"
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$logFile = Join-Path $logDir ("monitor-codex-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")

$pizUrl = "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron"
$agentes = @("orquestador-supervisor.py","telegram-bridge.py","cerebro-monitor.py")

function Write-Log([string]$line) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $msg = "[$ts] $line"
  Add-Content -Path $logFile -Value $msg
  Write-Host $msg
}

function Get-PizarronResumen {
  try {
    $r = Invoke-WebRequest -Uri $pizUrl -UseBasicParsing -TimeoutSec 20
    $json = $r.Content | ConvertFrom-Json
    if ($json -is [System.Array]) { $arr = $json } else { $arr = @($json.registros) }
    $count = @($arr).Count
    if ($count -gt 0) {
      $last = $arr[$count - 1]
      return "ok registros=$count ultimo_agente=$($last.agente) ultimo_estado=$($last.estado) ultima_tarea=$($last.tarea)"
    }
    return "ok registros=0"
  } catch {
    return "error pizarron=" + $_.Exception.Message
  }
}

function Get-AgentesResumen {
  try {
    $procs = Get-Process | Where-Object { $_.ProcessName -match 'python|py|powershell' }
    $matches = @()
    foreach ($p in $procs) {
      $cmd = ""
      try { $cmd = (Get-CimInstance Win32_Process -Filter ("ProcessId=" + $p.Id)).CommandLine } catch {}
      foreach ($a in $agentes) {
        if ($cmd -like "*$a*") { $matches += "$a(pid=$($p.Id))" }
      }
    }
    if ($matches.Count -eq 0) { return "warning agentes_no_detectados_por_cmdline" }
    return "ok agentes=" + ($matches -join ", ")
  } catch {
    return "error agentes=" + $_.Exception.Message
  }
}

function Check-Once([string]$fase) {
  $pz = Get-PizarronResumen
  $ag = Get-AgentesResumen
  Write-Log ("fase=$fase | " + $pz + " | " + $ag)
}

Write-Log "inicio monitor codex"

# Fase 1: cada 5 min por 10 min (2 chequeos)
for ($i = 1; $i -le 2; $i++) {
  Check-Once "F1_5m_10m_$i"
  if ($i -lt 2) { Start-Sleep -Seconds 300 }
}

# Fase 2: cada 5 min por 10 min (2 chequeos)
for ($i = 1; $i -le 2; $i++) {
  Check-Once "F2_5m_10m_$i"
  if ($i -lt 2) { Start-Sleep -Seconds 300 }
}

# Fase 3: cada 10 min por 20 min (2 chequeos)
for ($i = 1; $i -le 2; $i++) {
  Check-Once "F3_10m_20m_$i"
  if ($i -lt 2) { Start-Sleep -Seconds 600 }
}

# Fase 4: cada 15 min dos veces
for ($i = 1; $i -le 2; $i++) {
  Check-Once "F4_15m_x2_$i"
  if ($i -lt 2) { Start-Sleep -Seconds 900 }
}

# Fase 5: cada 20 min indefinido
while ($true) {
  Check-Once "F5_20m_continuo"
  Start-Sleep -Seconds 1200
}
