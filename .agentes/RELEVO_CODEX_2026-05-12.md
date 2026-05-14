# Relevo Codex - 2026-05-12

## Estado general

Los agentes quedan dormidos porque existe:

`C:\Users\USUARIO\iporave-sistema\.agentes\PARADA_CRITICA.txt`

Contenido visto:

`PAUSA MANUAL: agentes dormidos hasta corregir y validar infraestructura.`

No se reiniciaron agentes. No se borro la parada critica.

## Objetivo del trabajo

Revisar y estabilizar la infraestructura multi-agente de Iporave antes de volver a ponerla en marcha.

Prioridades indicadas por el usuario:

- No romper archivos.
- No gastar tokens innecesariamente.
- No hacer commits o deploys automaticos sin control.
- Asegurar que las notificaciones lleguen.
- Mejorar coordinacion entre supervisor, cerebro, telegram bridge y orquestadores.
- Mantener todo dormido hasta que la infraestructura este validada.

## Cambios aplicados

### .gitignore

Se agregaron exclusiones para archivos temporales/sensibles de agentes:

- `.agentes/__pycache__/`
- `.agentes/**/__pycache__/`
- `.agentes/locks/`
- `.agentes/logs/`
- `.agentes/pool_estado.json`
- `.agentes/alerts.json`
- `.agentes/PARADA_CRITICA.txt`
- `.agentes/telegram-memoria.json`
- `.agentes/telegram-config.json`
- `.agentes/*.pyc`
- `.aider.chat.history.md`
- `.aider.input.history`

Motivo: evitar subir estados, locks, memoria de Telegram, parada critica y configuracion sensible.

### .agentes/cerebro-monitor.py

Se corrigio para que las senales deterministicas detectadas sin IA entren al prompt del analisis:

- Se usa `senales_str`.
- Se agrego bloque `SENALES DETERMINISTICAS DETECTADAS SIN IA`.

Tambien se ajusto el modo prueba:

- `--test` / `--once` ya no envia notificacion falsa de inicio a Telegram.
- En modo prueba solo ejecuta un ciclo y sale.

Motivo: ahorrar ruido, evitar falsas alarmas y mejorar diagnostico.

### .agentes/probar-infra.ps1

Se agrego fallback de Python usando QGIS si `py` o `python` no estan disponibles:

- `C:\Program Files\QGIS 3.38.0\apps\Python312\python.exe`
- `C:\Program Files\QGIS 3.38.0\bin\python.exe`

Motivo: esta PC no tenia `py`/`python` disponible desde algunas consolas, pero si tiene Python 3.12 de QGIS.

### .agentes/iniciar-todos.ps1

Se agrego el mismo fallback de Python de QGIS.

Tambien se ajusto la forma de ejecutar los scripts con ruta entre comillas.

Motivo: permitir iniciar supervisor, Telegram Bridge y Cerebro Monitor aunque Python no este en PATH.

### Orquestadores protegidos contra push automatico

Se agrego control `IPORAVE_AUTO_COMMIT=1` en:

- `.agentes/orquestador.py`
- `.agentes/orquestador-paginas.py`
- `.agentes/orquestador-features.py`
- `.agentes/orquestador-catalog.py`
- `.agentes/orquestador-worker.py`
- `.agentes/codex-solucionador.py`

Comportamiento nuevo:

- Si `IPORAVE_AUTO_COMMIT` no vale `1`, los agentes pueden aplicar cambios pero no hacen `git commit` ni `git push`.
- Esto evita publicaciones accidentales mientras el sistema esta en etapa de estabilizacion.

## Validaciones realizadas

### Frontend

Comando:

`node validate.js`

Resultado:

- Bloque script principal encontrado.
- Sin `</script>` sin escapar.
- Balance de llaves correcto.
- HTML bien cerrado.
- CDN Supabase presente.
- CDN Mapbox presente.
- Sintaxis JavaScript valida.
- `doLogin` presente.
- `PAGES.catalogo` presente.
- `DL.saveProducto` presente.
- `exportOrdersPDF` presente.

Resultado final:

`Todo OK - seguro para commit/deploy`

### Sintaxis Python

Se compilaron correctamente los scripts principales con:

`C:\Program Files\QGIS 3.38.0\apps\Python312\python.exe`

Archivos validados:

- `.agentes/model_pool.py`
- `.agentes/cerebro-monitor.py`
- `.agentes/telegram-bridge.py`
- `.agentes/orquestador-supervisor.py`
- `.agentes/orq_base.py`
- `.agentes/orquestador.py`
- `.agentes/orquestador-paginas.py`
- `.agentes/orquestador-features.py`
- `.agentes/orquestador-catalog.py`
- `.agentes/orquestador-worker.py`
- `.agentes/codex-solucionador.py`

Resultado:

OK.

### Prueba segura de infraestructura

Comando:

`powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\USUARIO\iporave-sistema\.agentes\probar-infra.ps1`

Resultado:

- Parada critica activa.
- Frontend validado OK.
- Python detectado.
- Sintaxis Python correcta.
- Pool de modelos OK.
- API key AI Studio cargada OK.
- Telegram configurado.
- Cerebro Monitor en modo prueba respeta parada critica y salta ciclo.

Resultado final:

`TODO OK: infraestructura lista para reinicio controlado.`

## Estado actual del sistema

- Agentes dormidos: SI.
- `PARADA_CRITICA.txt` sigue activo: SI.
- Frontend `public/index.html` sano: SI.
- Scripts Python principales compilan: SI.
- Pool Gemini carga API key: SI.
- Telegram configurado: SI.
- Auto-commit/push bloqueado por defecto: SI.

## Comando para reinicio controlado cuando el usuario autorice

No ejecutar hasta que el usuario lo confirme.

```powershell
cd C:\Users\USUARIO\iporave-sistema
Remove-Item .\.agentes\PARADA_CRITICA.txt
powershell -NoProfile -ExecutionPolicy Bypass -File .\.agentes\iniciar-todos.ps1
```

## Recomendacion de reinicio

1. Mantener `IPORAVE_AUTO_COMMIT` desactivado inicialmente.
2. Borrar `PARADA_CRITICA.txt` solo cuando el usuario lo confirme.
3. Arrancar con `iniciar-todos.ps1`.
4. Observar Telegram y pizarron durante 10 a 15 minutos.
5. Si todo funciona, decidir despues si conviene activar auto-commit con:

```powershell
$env:IPORAVE_AUTO_COMMIT="1"
```

Por ahora no se recomienda activar auto-commit.

## Pendientes recomendados

- Probar Telegram Bridge en modo controlado si se agrega un modo `--test`.
- Revisar que las alertas reales se escriban tambien en `alerts.json`.
- Revisar si los orquestadores deben trabajar con cola estricta por archivo para evitar choques.
- Evaluar commit manual de los cambios de infraestructura cuando el usuario autorice.

## Actualizacion 2026-05-12 11:24

El usuario logro abrir Node-RED con:

```powershell
cd C:\Users\USUARIO
npx.cmd node-red -u C:\Users\USUARIO\.node-red
```

Node-RED quedo escuchando en:

`http://localhost:1880/`

Verificacion de puerto:

- `0.0.0.0:1880` escuchando.
- PID visto: `12936`.

Estado de agentes:

- Node-RED/pizarron: activo.
- Agentes Python/orquestadores: deben seguir dormidos.
- `PARADA_CRITICA.txt`: sigue activo.

Importante:

No borrar `PARADA_CRITICA.txt` ni arrancar todos los agentes hasta que el usuario confirme.

Proxima tarea pedida por el usuario:

- Crear una vista visual del pizarron para que el usuario pueda entender reportes sin mirar JSON.
- Ideal: pagina visible para admin, con tabla/cards, filtros por agente/estado, fecha, resumen y resaltado de errores.
- Enlace JSON actual del pizarron:

`https://iporave-api.iporaveparaguay.workers.dev/api/pizarron`

## Actualizacion 2026-05-12 11:30

El usuario aviso que Antigravity esta trabajando en paralelo y que le dio la orden de registrar en el pizarron todos los cambios del sistema.

Acciones de Codex:

- Se reviso `git status`.
- Se detecto que `public/index.html` fue modificado por otro flujo/agente.
- No se revirtio ni se piso ese trabajo.
- Se ejecuto `node validate.js` y el frontend sigue OK.

Se creo pagina nueva, separada del index principal, para visualizar el pizarron sin tocar el trabajo paralelo:

`C:\Users\USUARIO\iporave-sistema\public\pizarron.html`

Funcion:

- Lee `https://iporave-api.iporaveparaguay.workers.dev/api/pizarron`.
- Muestra reportes como cards legibles.
- Tiene filtros por texto, estado y agente.
- Tiene resumen de total, activos/finalizados, alertas y errores.
- Auto-actualiza cada 30 segundos.
- Es responsive para celular.

Validaciones:

- `node validate.js`: OK.
- Validacion JS interna de `public/pizarron.html`: OK.

Pendiente:

- Publicar o abrir la pagina desde el servidor actual.
- Si se quiere integrarla al menu admin del sistema, hacerlo despues de sincronizar con Antigravity para no pisar sus cambios actuales en `public/index.html`.

## Actualizacion 2026-05-12 - Diagnostico localhost:8080

El usuario aviso que `http://localhost:8080/pizarron.html` no funciona.

Diagnostico:

- El archivo existe en:
  `C:\Users\USUARIO\iporave-sistema\public\pizarron.html`
- `node validate.js`: OK.
- `localhost:8080` no responde y queda en timeout.
- `netsh interface portproxy show all` mostro que Windows tiene reglas portproxy:

```text
0.0.0.0:8080       -> 172.26.76.194:8080
100.123.43.75:8080 -> 172.26.76.194:8080
```

- `172.26.76.194:8080` no responde.
- WinHTTP proxy: sin proxy.
- Proxy de Internet Settings: sin proxy.
- Variables HTTP_PROXY/HTTPS_PROXY: no configuradas.
- hosts: localhost normal.
- DNS localhost resuelve a `127.0.0.1` y `::1`.

Causa:

El puerto `8080` esta secuestrado por una regla `portproxy` vieja o incorrecta, no por el servidor de Iporave.

Solucion temporal aplicada:

Se creo:

`C:\Users\USUARIO\iporave-sistema\serve-public.js`

Se levanto el pizarron en puerto alternativo:

`http://localhost:8082/pizarron.html`

Verificacion:

- `Invoke-WebRequest http://localhost:8082/pizarron.html`: status 200.
- `netstat`: `0.0.0.0:8082 LISTENING`.

Para reparar 8080 definitivamente, ejecutar PowerShell como administrador:

```powershell
netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8080
netsh interface portproxy delete v4tov4 listenaddress=100.123.43.75 listenport=8080
```

Luego levantar servidor en 8080 o usar 8082.

## Actualizacion 2026-05-12 - Arranque persistente del pizarron visual

Problema encontrado:

- Los procesos `node serve-public.js 8082` iniciados desde Codex quedan vivos solo durante la ejecucion de la herramienta.
- Al terminar la llamada, el entorno mata el proceso.
- Por eso Codex podia verificar `STATUS=200`, pero luego el usuario veia `ERR_CONNECTION_REFUSED`.

Solucion creada:

`C:\Users\USUARIO\iporave-sistema\abrir-pizarron-iporave.bat`

Funcion:

- Abre una ventana persistente llamada `Servidor Pizarron Iporave`.
- Ejecuta:

```bat
node serve-public.js 8082
```

- Luego abre:

`http://localhost:8082/pizarron.html`

Regla:

El usuario no debe cerrar la ventana `Servidor Pizarron Iporave` mientras quiera usar el pizarron visual.

## Actualizacion 2026-05-12 - Reinicio agentes bloqueado por permisos

Se intentó reiniciar agentes y activar monitoreo por fases, pero hubo bloqueo de permisos del sandbox en:

`C:\Users\USUARIO\iporave-sistema\.agentes\PARADA_CRITICA.txt`

Hallazgo ACL:

- `CodexSandboxUsers`: solo `ReadAndExecute`
- No permiso de borrado para esta sesion

Resultado:

- No se pudo borrar `PARADA_CRITICA.txt`.
- `iniciar-todos.ps1` se detuvo correctamente por la parada critica.
- No se levantaron Supervisor / Telegram Bridge / Cerebro-Monitor.

Se preparó script de monitoreo por fases:

`C:\Users\USUARIO\iporave-sistema\.agentes\monitor-pizarron-codex.ps1`

Secuencia configurada:

- 5 min x 10 min
- 5 min x 10 min
- 10 min x 20 min
- 15 min x 2 veces
- luego cada 20 min continuo

Pendiente para ejecutar (desde sesion con permisos del usuario):

1. Borrar parada critica.
2. Ejecutar `iniciar-todos.ps1`.
3. Ejecutar `monitor-pizarron-codex.ps1`.
