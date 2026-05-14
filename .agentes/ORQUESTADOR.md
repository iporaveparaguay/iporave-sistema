# ORQUESTADOR.md — Iporãve Connect
**Fecha de última actualización:** 2026-05-14 (limpieza pre-lanzamiento)
**Escrito por:** Claude Code (sesión agotando tokens)
**Para:** Cualquier IA que tome el mando

> **🧹 LIMPIEZA 2026-05-14 09:30:** Tareas colgadas en `[~]` reseteadas. Orquestador-Features
> en MODO SEGURO (no toca index.html). Aider-wrapper deshabilitado. Supervisor con lock
> anti-duplicado. Codex-Solucionador removido. Ver RELEVO_CLAUDE_2026-05-14_SESION2.md.

---

## TU ROL

Sos el comandante temporal de Iporãve Connect. Tu trabajo:
1. Leer este archivo completo antes de hacer cualquier cosa
2. Consultar el pizarrón para ver qué se hizo: GET https://iporave-api.iporaveparaguay.workers.dev/api/pizarron
3. Dar tareas a Aider según el nivel de complejidad
4. Reportar al pizarrón cuando una tarea termina
5. Nunca tocar archivos críticos de seguridad sin permiso del usuario

---

## ESTRUCTURA DEL PROYECTO

```
C:\Users\USUARIO\
├── iporave-sistema\        → Frontend (Vercel, deploy automático en push a main)
│   ├── public\
│   │   ├── index.html      → App principal (9000+ líneas)
│   │   ├── catalog.html    → Tienda pública (zona Antigravity)
│   │   └── [otras páginas públicas]
│   ├── validate.js         → OBLIGATORIO correr antes de commit
│   └── .agentes\           → Archivos de contexto y relevo
│
└── iporave-worker\         → Backend Cloudflare Worker (rama: master)
    └── src\
        ├── index.js        → Router principal
        ├── utils.js        → CRÍTICO: json(data,status) SIEMPRE 2 args
        └── api\            → Todos los endpoints
```

---

## URLs CLAVE

- Frontend: https://iporave-sistema.vercel.app
- API/Worker: https://iporave-api.iporaveparaguay.workers.dev
- Pizarrón: https://iporave-api.iporaveparaguay.workers.dev/api/pizarron

---

## REGLAS CRÍTICAS — NUNCA VIOLAR

1. **NO tocar:** `src/utils.js`, `src/api/login.js`, `verifyToken()`, `SAFE_SELF_FIELDS`, RLS Supabase
2. **json() siempre 2 argumentos:** `json(data, status)` — nunca 3
3. **validate.js antes de cada commit frontend:** `node validate.js` en iporave-sistema/
4. **No deployar sin permiso del usuario:** wrangler deploy solo cuando el usuario lo autorice
5. **No commitear sin validate.js OK**
6. **`</script>` dentro de strings JS en HTML es peligroso** — siempre partir: `'<scr'+'ipt>'`

---

## SISTEMA MULTI-AGENTE — QUIÉN HACE QUÉ

### Niveles de modelos (de más barato a más caro)

| Nivel | Modelo | Uso | Costo |
|-------|--------|-----|-------|
| **GRATIS** | Groq llama-3.3-70b | Tareas simples, archivos pequeños | $0 |
| **GRATIS** | Cerebras llama3.1-8b | Respuestas rápidas | $0 |
| **GRATIS LOCAL** | Ollama qwen2.5-coder:7b | Código privado/sensible | $0 |
| **GRATIS LOCAL** | Ollama llama3.2:3b | Supervisión, checklists | $0 |
| **BARATO** | Gemini 1.5 Flash | CSS/HTML grande, 1M tokens | $0.075-0.15/1M |
| **BARATO** | Gemini 2.5 Flash | Orquestación rápida | $0.30-0.60/1M |
| **BALANCE** | Qwen 2.5 Coder | JS complejo, Worker API | $0.20-0.40/1M |
| **PRO** | Gemini 1.5 Pro | Análisis global, arquitectura | $3.50-7.00/1M |
| **EMERGENCIA** | Codestral | Cuando Gemini/Qwen se traban | $1.00-2.00/1M |
| **EMERGENCIA** | GPT-4o | Seguridad, JWT, RLS únicamente | $5.00-15.00/1M |

### Criterio de escalada
- 1 intento fallido → reintentar con mejor prompt
- 2 intentos fallidos → escalar a Codestral
- Error de seguridad/auth → directo a GPT-4o

---

## CÓMO DAR TAREAS A AIDER

### Con Groq (gratis, archivos pequeños <128k tokens):
```powershell
$env:GROQ_API_KEY="[ver api-keys.json]"
aider --model groq/llama-3.3-70b-versatile --yes --no-git --no-auto-commits `
  --message "TU TAREA" `
  "C:\Users\USUARIO\iporave-worker\src\api\archivo.js"
```

### Con Vertex AI / Gemini (archivos grandes como index.html):
```powershell
# Requiere gcloud instalado y autenticado con ivanelgato4000@gmail.com
aider --model vertex_ai/gemini-1.5-flash-002 --yes --no-git --no-auto-commits `
  --message "TU TAREA" `
  "C:\Users\USUARIO\iporave-sistema\public\index.html"
```

### Con Vertex AI / Qwen 2.5 Coder:
```powershell
aider --model vertex_ai/qwen2.5-coder-32b-instruct --yes --no-git --no-auto-commits `
  --message "TU TAREA" `
  "C:\ruta\al\archivo.js"
```

---

## CÓMO REPORTAR AL PIZARRÓN

```powershell
$body = @{
  agente = 'NombreAgente'
  tarea = 'nombre-tarea'
  archivos = 'archivo.js'
  estado = 'Finalizado'
  resumen = 'Qué se hizo exactamente'
} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri 'https://iporave-api.iporaveparaguay.workers.dev/api/pizarron' -Method Post -ContentType 'application/json' -Body $body
```

---

## PROTOCOLO DE CADA TAREA

1. Leer el archivo a modificar
2. Planear el cambio mínimo necesario
3. Editar con Aider (elegir modelo según tamaño del archivo)
4. Si es frontend: `node validate.js` en iporave-sistema/
5. Si es Worker: `node --check src/api/archivo.js` en iporave-worker/
6. Commit con mensaje descriptivo
7. Si es frontend: `git push origin main` (Vercel deploya solo)
8. Si es Worker: esperar permiso del usuario para `npx wrangler deploy`
9. Reportar al pizarrón

---

## ESTADO DEL PROYECTO AL 2026-05-11 (actualizado en sesión)

### Vertex AI — CONFIGURADO ✅
- gcloud instalado y autenticado con ivanelgato4000@gmail.com
- Proyecto: `rugged-shell-430212-f6`
- Archivo JSON: `C:\Users\USUARIO\OneDrive\Desktop\rugged-shell-430212-f6-d4358e47cfbe.json`
- Variables de entorno guardadas con `setx` (permanentes)
- Modelo funcionando: `vertex_ai/gemini-2.5-flash` ✅
- API Vertex AI habilitada en Google Cloud Console ✅
- Costo real: $0.11 por tarea grande (index.html completo)

### Cómo usar Aider con Gemini 2.5 Flash (ya configurado):
```powershell
aider --model vertex_ai/gemini-2.5-flash --yes --no-git --no-auto-commits --message "TU TAREA" "ruta\al\archivo"
```
No necesitás poner variables de entorno — ya están guardadas con setx.

### Modelos disponibles en Vertex AI (sin descarga, por API):
- `vertex_ai/gemini-2.5-flash` ✅ PROBADO — barato, 1M tokens, ideal para index.html
- `vertex_ai/gemini-2.5-pro` — más potente, más caro
- `vertex_ai/gemini-2.5-flash-lite` — más barato aún
- NO usar: gemini-1.5-flash-002 (retirado), gemini-1.5-pro (verificar)

### Ollama local — modelos disponibles:
- `qwen2.5-coder:7b` ✅
- `llama3.2:latest` ✅
- `llama3.2:3b` ✅
- `phi3:mini` ✅
- `qwen2.5-coder:32b` — descargando (~20GB)

### Node-RED — fix aplicado 2026-05-11:
- settings.js: agregado `fs: require('fs')` en functionGlobalContext
- flows.json: nodo sheets-writer ya no usa require() directo

---

## ESTADO DEL PROYECTO AL 2026-05-11

### Completado ✅
- Panel por rol completo (superadmin, vendedor, proveedor, dropshipper, delivery, cliente)
- Búsqueda global de pedidos
- Push notifications VAPID
- Facturas B2B
- Analítica por rol
- Dashboard superadmin con métricas
- Panel delivery operativo
- Exportar pedidos CSV/Excel/PDF con filtros
- Botón IA arrastrable
- Catálogo público (catalog.html) con filtros, carrito, dark mode
- Páginas públicas: tracking, 404, faq, contacto, terminos, nosotros
- Panel vendedor: "Pedidos de hoy" + "Copiar tel."
- Footer con link a nosotros en todas las páginas
- Error handling robusto en todos los endpoints Worker
- Node-RED + pizarrón operativo
- Google Sheets escribiendo desde Node-RED

### Pendiente 🔴 — COLA DE TAREAS PARA EL ORQUESTADOR

Formato: cada tarea tiene archivo, instruccion, y zona. El orquestador las ejecuta en orden.
Estados: [ ] pendiente | [~] en progreso | [x] completada | [!] bloqueada (necesita revision humana)
Cuando una tarea se completa, marcarla [x]. Cuando se empieza, marcarla [~].

#### ZONA FRONTEND — index.html CSS — Gemini/Codex
REGLA CRÍTICA para TODAS las tareas de esta zona:
- SOLO agregar/modificar reglas CSS dentro del bloque <style> ya existente
- NUNCA escribir </script> ni tocar bloques <script>
- NUNCA modificar HTML ni JavaScript
- Si el modelo propone cambios fuera del bloque style → rechazar, reintentar con instruccion mas acotada

- [x] **visual-inputs** — ya existia en .fg input con border-radius, outline:none, transition, focus color. OK.
- [x] **visual-modals** — backdrop-filter:blur(4px) agregado a .moverlay. Background suavizado a .65. OK.
- [x] **visual-topbar** — box-shadow:0 1px 8px rgba(0,0,0,.3) agregado a .topbar. OK.
- [x] **visual-sidebar** — transition:width .25s ease agregado a .sidebar. OK.
- [x] **visual-empty-states** — .empty-state,.no-data,.lista-vacia{text-align:center;...} agregado. OK.
- [x] **visual-loading** — @keyframes spin + .spinner agregados. OK.
- [x] **visual-tabs** — ya existia via .ptab con border-bottom:2px solid transparent y .ptab.active. OK.
- [x] **visual-cards-hover** — transition:box-shadow .2s ease y .lcard2:hover agregados. OK.
- [x] **visual-btn-primary** — box-shadow:0 4px 14px rgba(245,166,35,.35) agregado a .btn-primary. OK.
- [x] **visual-scrollbar** — ya existia en L53. OK.
- [x] **visual-campanita-scroll** — En el bloque style de index.html agregar: #codexNotifBell.scroll-faded{opacity:0.3;} y en el bloque script existente (al final, antes del cierre) agregar listener: window.addEventListener('scroll',function(){var b=document.getElementById('codexNotifBell');if(!b)return;b.classList.toggle('scroll-faded',window.scrollY>80);},{passive:true}); NUNCA escribir sin escapar las etiquetas script.
- [x] **visual-order-menu-right** — .lcard2 .order-menu-wrap{margin-left:auto;flex-shrink:0;} aplicado. OK.
- [x] **visual-mobile-btn-spacing** — .act-btns spacing y .order-menu-btn min-size aplicados en mobile. OK.

#### ZONA CATALOGO — catalog.html — Gemini/Antigravity
- [x] **catalog-filtros-visual** — Los botones de filtro de categoria: cuando estan activos (.active) agregar background:var(--primary) y color:white. Solo CSS.
- [x] **catalog-precio** — El precio del producto: font-size:20px, font-weight:700, color:var(--primary). Solo CSS.
- [x] **catalog-empty** — Si no hay productos en el filtro, mostrar mensaje centrado "No hay productos en esta categoria". Solo CSS/HTML del estado vacio.
- [x] **catalog-footer** — Agregar footer simple con copyright y link a terminos al final de catalog.html. Solo HTML/CSS.
- [x] **catalog-mobile-nav** — En mobile, el navbar fijo arriba no debe tapar el contenido: agregar padding-top al body igual a la altura del nav. Solo CSS media query.
- [x] **catalog-mobile-ux** — CERRADA 2026-05-14: la app es usable en mobile. Si hay algo concreto que falle, abrir tarea nueva con repro.
- [x] **catalog-card-img** — CERRADA 2026-05-14: imágenes de catálogo se ven OK. Si hay desproporción concreta, abrir tarea nueva con captura.

#### ZONA WORKER — archivos pequeños — Qwen7B/Groq
- [x] **worker-calificaciones** — En calificaciones.js: todos los catch deben retornar json(data,status) con 2 argumentos. No cambiar logica.
- [x] **worker-catalog-public** — En catalog-public.js: agregar try/catch global, retornar json({error:'Error interno'},500) si falla. No cambiar logica.
- [x] **worker-notif-entrega** — En notif-entrega.js: verificar que todos los return usen json(data,status) con exactamente 2 argumentos.
- [x] **worker-geocode** — En geocode.js: agregar validacion de parametros al inicio — si falta lat o lng, retornar json({error:'Parametros requeridos: lat, lng'},400).
- [x] **worker-order-status-logs** — En order-status.js: agregar campo updated_at con timestamp en cada actualizacion de estado. No cambiar logica principal.
- [x] **worker-audit-validaciones** — Revisar TODOS los archivos en src/api/: cualquier endpoint que reciba body JSON debe validar campos obligatorios al inicio y retornar json({error:'Campo X requerido'},400) si faltan. No cambiar logica existente, solo agregar validaciones faltantes al inicio de cada handler.
- [x] **worker-headers-seguridad** — En src/index.js, verificar que corsHeaders() incluya: X-Content-Type-Options:nosniff, X-Frame-Options:DENY, Referrer-Policy:strict-origin-when-cross-origin. Agregarlos si faltan. No tocar verifyToken ni login.js.

#### ZONA PAGINAS PUBLICAS — otras paginas — Gemini
- [x] **paginas-meta-tags** — En todas las paginas publicas (tracking.html, faq.html, contacto.html): verificar que tengan meta description y og:title correctos.
- [x] **paginas-favicon** — Verificar que todas las paginas publicas tengan link rel=icon apuntando al favicon correcto.
- [x] **paginas-track-mobile** — En public/track.html: revisar en 375px que el formulario de tracking sea usable: input de numero de pedido con width:100%, boton buscar min-height:44px, resultado del pedido con padding suficiente, texto legible (font-size>=14px). Solo CSS/HTML minimo.
- [x] **paginas-nosotros-mobile** — En public/nosotros.html: revisar que el contenido no desborde en 375px, texto con max-width y padding lateral, imagenes responsive. Solo CSS.
- [x] **paginas-faq-mobile** — En public/faq.html: verificar que las preguntas/respuestas sean legibles en mobile, acordeon funcional con touch, padding lateral adecuado. Solo CSS si se puede.

---

#### ZONA FEATURES — index.html funcionalidades JS — Gemini 1M ctx

- [!] **feature-auto-registro-ui** — BLOQUEADO hasta post-lanzamiento. No tocar hoy.: formulario con nombre, email, telefono, password, rol (cliente/vendedor/dropshipper). Al enviar, POST a /api/auth/registro. Mostrar mensaje de "pendiente aprobacion" al terminar. Solo mostrar esta pantalla si el usuario no esta logueado.

- [!] **feature-whatsapp-config** — BLOQUEADO hasta post-lanzamiento. No tocar hoy. (visible para admin, vendedor, dropshipper), agregar subseccion "Configuracion WhatsApp Business" con campos: Token de API, Phone Number ID, Business Account ID. Boton "Guardar" que hace PUT a /api/config/whatsapp. Boton "Probar conexion" que hace POST a /api/config/whatsapp/test y muestra resultado. Mostrar estado actual: conectado (verde) o no configurado (amarillo).

- [!] **feature-asistente-ia** — BLOQUEADO hasta post-lanzamiento. No tocar hoy. por un chat funcional que llama a /api/ai/chat con el mensaje del usuario. El endpoint devuelve la respuesta. UI: burbuja flotante, al hacer click abre panel lateral con historial de mensajes, input y boton enviar. Usar el mismo estilo visual del sistema.

- [!] **feature-analytics-admin** — BLOQUEADO hasta post-lanzamiento. No tocar hoy., agregar seccion "Analitica avanzada" con: grafica de ventas por semana (ultimas 4 semanas), top 5 vendedores por volumen, mapa de calor de horas con mas pedidos (24 franjas), tasa de entrega exitosa. Datos desde /api/analytics/admin. Usar Chart.js que ya esta incluido.

- [!] **feature-boletas-pdf** — BLOQUEADO hasta post-lanzamiento. No tocar hoy. en el detalle de cada pedido. Al hacer click, llama a /api/boletas/{pedido_id} que devuelve HTML, luego usa window.print() con estilos de impresion para generar PDF desde el navegador. Mostrar numero de pedido, productos, total, fecha, datos del cliente.

- [!] **feature-pwa** — BLOQUEADO hasta post-lanzamiento. No tocar hoy.: crear boton "Instalar app" que aparece solo cuando el navegador soporta instalacion (evento beforeinstallprompt). Al hacer click, llama a prompt.prompt(). El boton debe estar en el topbar, solo visible si la app no esta instalada. No tocar el manifest.json existente si ya existe.

- [!] **feature-gps-tracking** — BLOQUEADO hasta post-lanzamiento. No tocar hoy., agregar seccion "Mi ubicacion" con boton "Iniciar tracking". Al activar, llama a navigator.geolocation.watchPosition() y envia lat/lng a /api/delivery/ubicacion cada 30 segundos. Mostrar estado "Tracking activo" con punto verde parpadeante. Boton "Detener" para parar. En el panel del cliente, en el detalle del pedido activo, mostrar mapa Leaflet con la ubicacion del delivery en tiempo real (GET /api/pedidos/{id}/ubicacion-delivery).

- [!] **feature-rol-empresa** — BLOQUEADO hasta post-lanzamiento. No tocar hoy.: en el panel de superadmin, seccion "Empresas" que lista cuentas con rol empresa. Cada empresa puede ver sus propios pedidos y vendedores asignados. UI similar al panel dropshipper pero con nombre de empresa en el topbar. Endpoint GET /api/empresa/dashboard para sus metricas.

---

#### ZONA WORKER — nuevos endpoints — Groq/Gemini

- [x] **worker-auto-registro** — Crear src/api/auto-registro.js: endpoint POST /api/auth/registro que recibe {nombre, email, telefono, password, rol_solicitado}, crea usuario en Supabase Auth, inserta en tabla usuarios con estado='pendiente', notifica al superadmin via tabla notificaciones. Retornar json({ok:true, mensaje:'Registro recibido, pendiente aprobacion'},201).

- [x] **worker-whatsapp-config** — Crear src/api/whatsapp-config.js: GET /api/config/whatsapp devuelve config actual del usuario autenticado (sin mostrar el token completo, solo los ultimos 4 chars). PUT /api/config/whatsapp guarda {token, phone_number_id, business_account_id} encriptado en tabla config_integraciones. POST /api/config/whatsapp/test envia mensaje de prueba "Conexion exitosa con Iporave" al numero configurado usando la API de WhatsApp. Retornar resultado.

- [x] **worker-ai-chat** — Crear src/api/ai-chat.js: endpoint POST /api/ai/chat que recibe {mensaje, historial:[]} y llama a Cloudflare AI (env.AI.run('@cf/meta/llama-3.1-8b-instruct', {messages})) con contexto del sistema Iporave. Si falla, usar fetch a api.groq.com con model llama-3.3-70b-versatile y GROQ_API_KEY del env. Retornar json({respuesta: texto}, 200).

- [x] **worker-boletas** — Crear src/api/boletas.js: endpoint GET /api/boletas/{pedido_id} que obtiene el pedido con sus items, cliente y vendedor, genera HTML de boleta con estilos de impresion (tabla de productos, totales, logo Iporave, fecha, numero de pedido), retorna como text/html. Solo accesible para el dueno del pedido o admin.

- [x] **worker-delivery-ubicacion** — Crear src/api/delivery-ubicacion.js: POST /api/delivery/ubicacion recibe {lat, lng} del delivery autenticado, guarda en tabla delivery_ubicaciones con timestamp. GET /api/pedidos/{id}/ubicacion-delivery devuelve la ultima ubicacion del delivery asignado a ese pedido (solo si el cliente es dueno del pedido). Retornar json({lat, lng, updated_at}).

- [x] **worker-analytics-admin** — Crear src/api/analytics-admin.js: endpoint GET /api/analytics/admin (solo superadmin) que consulta: ventas por semana ultimas 4 semanas, top 5 vendedores por total de pedidos, distribucion de pedidos por hora del dia, tasa de entrega exitosa (entregados/total). Retornar todo en un solo JSON.

---

### Comandos remotos — leer desde pizarron
El orquestador lee el pizarron cada ciclo. Si encuentra una entrada con agente="COMANDO" y estado="Pendiente", la ejecuta como tarea inmediata y marca como "Ejecutado".
Ejemplo para enviar desde celular:
POST https://iporave-api.iporaveparaguay.workers.dev/api/pizarron
{"agente":"COMANDO","tarea":"tarea-urgente","archivos":"archivo.html","estado":"Pendiente","resumen":"instruccion exacta para aider"}

---

#### ZONA AUDITORÍA CONTINUA — rotar cada 10 min — agente libre que encuentre [ ]

REGLA: Cuando un agente termina su tarea y no hay [ ] en su zona, toma la primera [ ] de aquí.
Cada auditoría es READ-ONLY: NO modifica código, solo reporta al pizarrón con estado=ALERTA si encuentra algo.

- [x] **audit-xss-index** — COMPLETADO 2026-05-14: todos los innerHTML con datos de usuario usan escHtml(). Sin vulnerabilidades XSS encontradas.
- [x] **audit-worker-auth** — Leer todos los archivos en iporave-worker/src/api/. Verificar que cada endpoint que no sea público llame a verifyToken() al inicio. Listar los que NO lo hacen. Reportar al pizarrón.
- [x] **audit-mobile-index** — COMPLETADO 2026-05-14: único problema encontrado era .tbl th font-size:9px → corregido a 11px (commit 395d6ca). #aiPanel.maximized width:680px cubierto por media query. Sin otros problemas.
- [x] **audit-rls-supabase** — Leer iporave-worker/src/api/save-user.js y order-status.js. Verificar que ningún UPDATE/INSERT omita filtros de usuario_id o rol. Reportar al pizarrón.
- [x] **audit-errores-js** — Leer public/index.html, buscar funciones async sin try/catch, fetch() sin .catch(), y console.log() que expongan datos sensibles (token, password, auth_id). Reportar líneas exactas al pizarrón.
- [x] **audit-catalog-seguridad** — COMPLETADO 2026-05-14: usa esc() en todos los datos, safeUrl() en URLs, fetch con try/catch. Sin vulnerabilidades encontradas.
- [x] **audit-worker-rate-limits** — Leer iporave-worker/src/index.js y los api/*.js. Verificar que los endpoints de login, registro y cambio de contraseña tengan rate limiting activo. Reportar cuáles no tienen.
- [x] **audit-performance-index** — COMPLETADO 2026-05-14: todos los setInterval tienen clearInterval previo. _gpsLoopTimer es correcto (llama _gpsLoopStop() antes). Dos document.click y dos window.scroll handlers son intencionales y no duplicados exactos. Sin problemas reales.

### NO DELEGAR (solo Claude Code o GPT-4o)
- JWT + RLS Security Audit
- Cambios en login.js, utils.js, verifyToken
- Integracion Mercado Pago real
- WhatsApp Business API
- Configuracion Supabase RLS

---

## CONFIGURACIÓN GOOGLE CLOUD / VERTEX AI (EN PROCESO)

**Estado al 2026-05-11:** gcloud CLI instalándose en la PC del usuario
**Cuenta:** ivanelgato4000@gmail.com
**Pendiente:**
1. Terminar instalación gcloud
2. `gcloud init` → autenticar con ivanelgato4000@gmail.com
3. Habilitar Vertex AI API en Google Cloud Console
4. Probar: `aider --model vertex_ai/gemini-1.5-flash-002 ...`

---

## API KEYS DISPONIBLES

Están en `C:\Users\USUARIO\node-red-config\api-keys.json`:
- groq ✅
- openrouter ✅
- cerebras ✅
- kimi ✅
- deepseek ❌ sin saldo

**NUNCA poner las keys en este archivo — están en api-keys.json**

---

## MODELOS OLLAMA LOCAL DISPONIBLES

Endpoint: `http://localhost:11434/api/chat`
- `qwen2.5-coder:7b` — para código (4.7 GB) — INSTALAR PRIMERO
- `llama3.2:latest` — general (2 GB)
- `llama3.2:3b` — supervisión liviana (2 GB)
- `phi3:mini` — muy liviano (2.1 GB)

**Nota:** Qwen 2.5 Coder local tiende a timeout en primera inferencia — darle 5 min.

---

## ZONAS DE AGENTES — NO PISAR

| Zona | Archivo | Agente dueño |
|------|---------|-------------|
| Líneas 2669-4888 | index.html | Codex |
| catalog.html | catálogo público | Antigravity |
| Worker API | src/api/*.js | Aider |
| Seguridad/Auth | login.js, utils.js | Solo Claude Code |

**Regla:** Una sola IA editando el mismo archivo grande a la vez.

---

## SISTEMA DE RELEVO

```
Claude Code se queda sin créditos
         ↓
1. Leer este archivo (ORQUESTADOR.md)
2. Ver pizarrón: qué está hecho, qué falta
3. Tomar mando con Gemini 2.5 Flash como orquestador
4. Usar Aider + Gemini 1.5 Flash para tareas de código grande
5. Usar Aider + Qwen 2.5 Coder para JS/Worker
6. Usar Groq/Cerebras para tareas simples y gratuitas
7. Reportar todo al pizarrón
         ↓
Claude Code vuelve → lee pizarrón → retoma mando
```

---

## NOTAS IMPORTANTES

- El sistema fue hackeado en etapa inicial — hay parches de seguridad activos
- iporave-worker está en rama `master` (no main)
- iporave-sistema está en rama `main`
- Vercel deploya automáticamente en push a main
- Worker requiere `npx wrangler deploy` con permiso explícito del usuario
- Node-RED corre localmente en http://localhost:1880
- Pizarrón local Node-RED: http://localhost:1880/reporte
- Siempre usar `Invoke-RestMethod` para reportar (curl.exe falla con JSON en PowerShell)
