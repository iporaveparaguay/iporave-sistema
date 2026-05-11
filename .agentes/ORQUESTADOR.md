# ORQUESTADOR.md — Iporãve Connect
**Fecha de última actualización:** 2026-05-11
**Escrito por:** Claude Code (sesión agotando tokens)
**Para:** Cualquier IA que tome el mando

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

### Pendiente 🔴 (prioridad alta)

#### 1. Mejoras visuales botones — desktop Y mobile (index.html)
**Problema:** Botones muy juntos, algunos apilados verticalmente, se ve poco profesional
**Archivo:** `public/index.html` — solo CSS primeras 475 líneas
**Usar:** Aider + Vertex AI Gemini 1.5 Flash (index.html es >128k tokens, Groq no alcanza)
**Cambios exactos:**
- `.btn` base: `box-shadow:0 1px 3px rgba(0,0,0,.13)`, padding `10px 20px`
- `.btn-sm`: padding `6px 13px`
- `.tbactions` desktop: gap `12px`
- `.act-btns` desktop: gap `8px`
- Mobile `@media`: `.tbl td.td-actions` → cambiar a grid 2 columnas en vez de block full-width
- Mobile `.act-btns`: gap `7px`, padding botones `6px 10px`
- Mobile `.tbactions .btn`: padding `8px 13px`, font-size `12px`
- **NO tocar JS. NO tocar utils.js ni login.js.**

#### 2. Tienda pública — catálogo + flujo de compra (catalog.html)
**Zona:** Antigravity
**Pendiente:** Auto-registro de clientes, flujo de compra completo, pago

#### 3. JWT + RLS Security Audit
**SOLO Claude Code o GPT-4o**
**No delegar a modelos baratos — es seguridad crítica**

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
