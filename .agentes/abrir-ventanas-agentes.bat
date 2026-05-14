@echo off
setlocal
cd /d C:\Users\USUARIO\iporave-sistema

echo Abriendo ventanas de agentes...

start "Supervisor Iporave" cmd /k "cd /d C:\Users\USUARIO\iporave-sistema && py -3 .agentes\orquestador-supervisor.py"
timeout /t 1 /nobreak >nul
start "Telegram Bridge Iporave" cmd /k "cd /d C:\Users\USUARIO\iporave-sistema && py -3 .agentes\telegram-bridge.py"
timeout /t 1 /nobreak >nul
start "Cerebro Monitor Iporave" cmd /k "cd /d C:\Users\USUARIO\iporave-sistema && py -3 .agentes\cerebro-monitor.py"
timeout /t 1 /nobreak >nul
start "Monitor Codex Pizarron" cmd /k "cd /d C:\Users\USUARIO\iporave-sistema && powershell -NoProfile -ExecutionPolicy Bypass -File .agentes\monitor-pizarron-codex.ps1"

echo Listo.
endlocal
