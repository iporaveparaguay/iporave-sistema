@echo off
setlocal

cd /d C:\Users\USUARIO\iporave-sistema

echo ==========================================
echo  Pizarron visual Iporave
echo ==========================================
echo.
echo Se abrira un servidor local en:
echo http://localhost:8082/pizarron.html
echo.
echo IMPORTANTE:
echo No cierres la ventana "Servidor Pizarron Iporave"
echo mientras quieras usar el pizarron.
echo.

start "Servidor Pizarron Iporave" cmd /k "cd /d C:\Users\USUARIO\iporave-sistema && node serve-public.js 8082"

timeout /t 3 /nobreak >nul

start "" "http://localhost:8082/pizarron.html"

endlocal
