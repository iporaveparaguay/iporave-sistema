# Instrucciones para Antigravity

## Regla principal

Siempre guardar el relevo de lo trabajado en:

`C:\Users\USUARIO\iporave-sistema\.agentes\RELEVO_CODEX_2026-05-12.md`

Si haces cambios, agrega una seccion nueva al final con:

- fecha y hora,
- archivos tocados,
- que cambiaste,
- que validaste,
- que queda pendiente,
- si los agentes deben seguir dormidos o pueden reiniciarse.

## Estado actual

Node-RED se abre con:

```powershell
cd C:\Users\USUARIO
npx.cmd node-red -u C:\Users\USUARIO\.node-red
```

URL local:

`http://localhost:1880/`

El pizarron JSON esta en:

`https://iporave-api.iporaveparaguay.workers.dev/api/pizarron`

## Seguridad operativa

No borrar este archivo salvo confirmacion del usuario:

`C:\Users\USUARIO\iporave-sistema\.agentes\PARADA_CRITICA.txt`

No activar `IPORAVE_AUTO_COMMIT=1` sin confirmacion del usuario.

No hacer `git push` automatico durante estabilizacion.

Despues de tocar `public/index.html`, correr:

```powershell
cd C:\Users\USUARIO\iporave-sistema
node validate.js
```

