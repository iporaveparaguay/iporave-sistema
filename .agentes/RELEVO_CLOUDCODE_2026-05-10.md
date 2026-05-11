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

- Seguridad primero ante todo. El sistema ya tuvo un incidente/hackeo al inicio y hay parches de seguridad en curso; cualquier decision debe priorizar no abrir nuevas fugas ni regresiones.
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

4. Mejora visual/mobile: boton flotante del asistente IA
   - Archivo: `public/index.html`
   - Commit: `76d7382 feat: make AI assistant button draggable`
   - Cambio:
     - el boton del robot/asistente ahora se puede arrastrar en pantalla;
     - la posicion se guarda en `localStorage`;
     - el panel del chat se abre cerca del boton sin salirse de la pantalla;
     - al redimensionar la pantalla, la posicion se reajusta dentro del viewport.
   - Validacion: `node validate.js` OK.

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
- Politica especial para OpenRouter:
  - tratarlo como proveedor externo no confiable para secretos, tokens, datos de clientes, credenciales, dumps de base de datos y archivos sensibles;
  - usarlo preferentemente para tareas de baja sensibilidad: revision visual, redaccion, prompts, analisis de diffs ya limpiados, ideas de UX, tareas aisladas sin secretos;
  - no enviar `.env`, claves Supabase, claves Cloudflare, tokens VAPID, datos reales de clientes ni conversaciones completas con informacion privada;
  - crear API keys con limite de credito bajo y nombre por agente/tarea;
  - revisar en OpenRouter que logging/uso de inputs este desactivado y filtrar proveedores que puedan entrenar con datos;
  - si se usa OpenRouter para codigo, pasar solo fragmentos minimos y sanitizados.
- Politica para Ollama:
  - preferir Ollama para supervision local, lectura de contexto, analisis de bugs y tareas con datos mas sensibles, porque corre localmente;
  - instalar modelos livianos para no bloquear la maquina;
  - usarlo como respaldo cuando se terminen tokens cloud, aunque sea mas lento.
- Seguridad:
  - hay preocupacion previa sobre seguridad y migracion/ajuste de Supabase/RLS;
  - el sistema ya fue hackeado en una etapa inicial y existen parches/pendientes de seguridad;
  - no tocar auth, RLS, tokens, login, permisos ni exposicion de datos sin plan especifico, diff pequeno, revision dedicada y permiso explicito;
  - si hay duda entre velocidad y seguridad, frenar y pedir confirmacion.

## URLs oficiales para agentes/modelos de respaldo

- OpenRouter API keys: `https://openrouter.ai/settings/keys`
- OpenRouter documentacion API keys: `https://openrouter.ai/docs/api-keys`
- OpenRouter privacidad/logging: `https://openrouter.ai/docs/features/privacy-and-logging`
- OpenRouter data collection: `https://openrouter.ai/docs/guides/privacy/data-collection/`
- Ollama descarga/documentacion: `https://docs.ollama.com/`
- Ollama quickstart: `https://docs.ollama.com/quickstart`
- Ollama API local: `https://docs.ollama.com/api`

Prioridad recomendada:

1. Ollama local para revisar contexto sensible y actuar como supervisor barato.
2. OpenRouter `:free` o bajo costo para tareas no sensibles y con API keys limitadas.
3. Modelos pagos solo cuando una tarea lo justifique y con limite de gasto.

## Estado Ollama local

- Ollama confirmado instalado por el usuario en:
  - `C:\Users\USUARIO\AppData\Local\Programs\Ollama\ollama.exe`
- Version reportada:
  - `0.23.2`
- Modelos confirmados:
  - `llama3.2:latest` (`a80c4f17acd5`, 2.0 GB)
  - `llama3.2:3b` descargado correctamente
- Descarga en curso al momento del relevo:
  - `qwen2.5-coder:7b` (aprox. 4.7 GB, iba 5% / 219 MB)

Uso recomendado:

- `llama3.2:3b`: supervisor local liviano, resumen, checklist, revision de contexto no critico.
- `qwen2.5-coder:7b`: apoyo local para codigo cuando termine la descarga.
- Por seguridad, Ollama tiene prioridad sobre OpenRouter para revisar fragmentos con contexto del proyecto.

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

## Cierre de tanda nocturna

- El usuario confirmo "eso era y guarda" despues de la mejora del boton flotante del asistente.
- Ultimo estado funcional relevante:
  - boton IA arrastrable implementado y validado;
  - cambios guardados en git;
  - reporte enviado a Node-RED;
  - no hay deploy frontend realizado desde Codex en esta tanda.
- Mantener siguiente criterio:
  - si no hay una tarea nueva explicita, continuar solo con monitoreo pasivo;
  - no abrir otra oleada de cambios hasta que el usuario o Cloud Code indiquen proximo objetivo.
