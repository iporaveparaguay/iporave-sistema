# Relevo operativo para Cloud Code - 10 de mayo 2026

Este archivo resume lo hecho por Codex como suplente/coordinador temporal de la orquesta Iporave Connect mientras Cloud Code quedo sin tokens. La idea es que Cloud Code pueda retomar sin reconstruir contexto desde el chat.

## Estado general

- Proyecto principal: `C:\Users\USUARIO\iporave-sistema`
- Worker/API: `C:\Users\USUARIO\iporave-worker`
- Pizarron local Node-RED: `http://localhost:1880/reporte`
- Pizarron publico Worker: `https://iporave-api.iporaveparaguay.workers.dev/api/pizarron`
- Fecha operativa: 2026-05-10
- Rol asumido por Codex: coordinacion temporal, validacion, commits, deploy controlado y monitoreo.

## Reglas operativas vigentes

- No deployar produccion sin permiso explicito del usuario.
- Antes de cambios frontend en `public/index.html`, correr `node validate.js`.
- No tocar seguridad critica sin tarea precisa y confirmacion: `verifyToken`, `login.js`, `SAFE_SELF_FIELDS`, RLS.
- Mantener cambios pequenos, aislados y commiteados para rollback claro.
- Si varios agentes trabajan, evitar que dos editen el mismo archivo grande al mismo tiempo.
- Para Worker, si no hay tests definidos, usar `node --check` sobre archivos tocados.
- Reportar al pizarron cuando una tarea termina.

## Estado validado antes del relevo

### Frontend `iporave-sistema`

- `node validate.js`: OK.
- `git status --short`: limpio despues del ultimo commit.
- Ultimo commit realizado por Codex:
  - `9fc3eb7 feat: export pedidos por rango filtrado`

Cambios de ese commit:

- En `public/index.html`, vista de pedidos:
  - agregados filtros `Desde` y `Hasta`;
  - `CSV`, `Excel` y `PDF` exportan respetando los filtros visibles;
  - validacion `node validate.js` dio `Todo OK`.

Reporte local Node-RED:

- Primeros intentos con `curl.exe` fallaron por quoting JSON en PowerShell.
- Reporte exitoso con `Invoke-RestMethod`:
  - respuesta: `Reporte recibido - supervision en proceso`.
- No se avanzo a otra tarea que toque archivos porque no se recibio una respuesta literal `VALIDADO`.

### Worker `iporave-worker`

- Deploy controlado ejecutado con permiso del usuario.
- Comando usado:
  - `npx.cmd wrangler deploy`
- Resultado:
  - deploy OK;
  - Worker publicado en `https://iporave-api.iporaveparaguay.workers.dev`;
  - Version ID: `73e2e3e4-7b80-423a-a13a-27e5f50c152f`;
  - commit desplegado: `a5f5b44 worker: harden delivery notifications and whatsapp status`.
- Verificacion local con `curl` al endpoint publico fallo por conectividad del entorno, no por Wrangler.
- `git status --short` del Worker muestra solo:
  - `.aider.chat.history.md`
  - `.aider.input.history`
- Esos historiales de Aider no fueron commiteados.

## Tareas cerradas durante la suplencia

1. Deploy Worker post-fixes
   - Se desplego el commit `a5f5b44`.
   - No se modificaron archivos.

2. Mejora frontend: exportar pedidos por rango filtrado
   - Archivo: `public/index.html`
   - Commit: `9fc3eb7`
   - Validacion: `node validate.js` OK.
   - Reporte local: recibido por Node-RED, quedo en supervision.

3. Monitoreo recurrente
   - Stop flag libre en todos los chequeos.
   - `iporave-sistema` limpio.
   - `iporave-worker` sin cambios de codigo pendientes.

## Tareas sugeridas para la proxima oleada

Orden recomendado:

1. Esperar validacion del pizarron para `frontend-export-rango-filtrado`.
2. Lanzar tareas pequenas y sin solapamiento:
   - Antigravity: carrito basico en `public/catalog.html`.
   - Aider: robustez secundaria en Worker, sin tocar auth ni seguridad central.
   - Codex/frontend: siguiente mejora chica solo si no pisa el archivo de otro agente.
3. Mantener una sola persona editando `public/index.html` a la vez.

## Pendientes visuales detectados por el usuario

Estos no fueron ejecutados todavia; quedan como backlog visual/mobile:

- Mejorar layout mobile de botones en pedidos: actualmente quedan muy juntos y visualmente cargados.
- Profesionalizar cards/metrica de dashboards: las metricas existen pero se ven basicas.
- Revisar pantalla inicial/logo: en mobile, `Iporave Connect PI` y la bandera de Paraguay se superponen con el texto.
- Asegurar que toda mejora visual sea mobile-first porque la app se usa como PWA instalada desde la web.
- Mantener botones grandes y claros para roles operativos en celular, especialmente delivery.

## Pendientes estrategicos

- Disenar sistema de suplentes de agentes:
  - Cloud Code como comandante principal;
  - Codex como suplente/coordinador;
  - evaluar Antigravity u otro agente como tercer comandante;
  - preparar prompts de relevo para que un agente nuevo pueda tomar el mando con este archivo.
- Evaluar mas agentes gratuitos:
  - OpenRouter con modelos `:free` cuando corresponda;
  - Ollama local con modelos livianos para supervision/revision;
  - otros proveedores gratuitos solo despues de cerrar una tanda estable.
- Seguridad:
  - hay preocupacion previa sobre seguridad y migracion/ajuste de Supabase/RLS;
  - no tocar esto sin plan especifico y revision de Cloud Code o tarea muy precisa.

## Protocolo recomendado para seguir

1. Antes de nueva tarea:
   - `node .agentes/check-stop.js`
   - `git status --short` en ambos repos.
2. Si se toca frontend:
   - cambio pequeno;
   - `node validate.js`;
   - revisar diff;
   - commit;
   - reportar.
3. Si se toca Worker:
   - `node --check` de archivos modificados;
   - commit;
   - deploy solo con permiso explicito;
   - registrar Version ID de Wrangler.
4. Si un reporte al pizarron local falla con `curl.exe` por JSON:
   - usar `Invoke-RestMethod` con `ConvertTo-Json`.

Ejemplo:

```powershell
$body=@{
  agente='Codex'
  tarea='NOMBRE_TAREA'
  archivos='ARCHIVOS'
  estado='Finalizado'
  resumen='RESUMEN'
} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri 'http://localhost:1880/reporte' -Method Post -ContentType 'application/json' -Body $body
```

## Nota para Cloud Code

El usuario pidio que este archivo se vaya actualizando mientras Codex este parado o monitoreando, para que exista un relevo completo. Tambien pidio que se propongan mejoras cuando se detecten, pero sin ejecutarlas automaticamente si implican riesgo visual, seguridad o produccion.
