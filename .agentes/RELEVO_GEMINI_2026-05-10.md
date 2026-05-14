# Relevo para Gemini — Comandante temporal Iporãve Connect
**Fecha:** 2026-05-10 | **Reemplaza a:** Claude Code + Codex

---

## Tu rol

Sos el comandante temporal del proyecto Iporãve Connect. Tu trabajo es:
1. Leer este archivo completo antes de hacer cualquier cosa
2. Dar tareas a Aider (agente de código que corre en la PC del usuario)
3. Dar tareas a sub-agentes si tenés acceso al Agent SDK
4. Reportar al pizarrón público cada vez que una tarea termina
5. Nunca tocar archivos críticos de seguridad sin permiso explícito del usuario

---

## Estructura del proyecto

```
C:\Users\USUARIO\
├── iporave-sistema\        ← Frontend (Vercel, deploy automático en push a main)
│   └── public\
│       ├── index.html      ← App principal (5000+ líneas, zona Codex: 2669-4888)
│       ├── catalog.html    ← Tienda pública (zona Antigravity)
│       ├── tracking.html   ← Rastreo público de pedidos
│       ├── 404.html        ← Página de error
│       ├── faq.html        ← Preguntas frecuentes
│       ├── contacto.html   ← Contacto
│       ├── terminos.html   ← Términos y condiciones
│       └── manifest.json   ← PWA manifest
│
└── iporave-worker\         ← Backend Cloudflare Worker (deploy con wrangler)
    └── src\
        ├── index.js        ← Router principal
        ├── utils.js        ← CRÍTICO: json(data,status) solo 2 args, incluye CORS
        └── api\            ← Todos los endpoints
```

---

## URLs del sistema

- **Frontend:** https://iporave-sistema.vercel.app
- **Worker/API:** https://iporave-api.iporaveparaguay.workers.dev
- **Pizarrón público:** https://iporave-api.iporaveparaguay.workers.dev/api/pizarron

---

## Cómo reportar al pizarrón

```bash
curl -X POST https://iporave-api.iporaveparaguay.workers.dev/api/pizarron \
  -H "Content-Type: application/json" \
  -d '{"agente":"Gemini","tarea":"NOMBRE","archivos":"ARCHIVO","estado":"Finalizado","resumen":"QUE HICISTE"}'
```

---

## Cómo dar tareas a Aider

Aider corre en la PC del usuario. El usuario lo lanza con:
```powershell
aider --model groq/llama-3.3-70b-versatile --yes --no-git --no-auto-commits `
  --read "C:\Users\USUARIO\iporave-sistema\.agentes\CONTEXTO_SISTEMA.md" `
  --message "TU TAREA AQUI" `
  src/api/archivo.js
```

Vos le das el texto de la tarea y el archivo. El usuario copia y pega el comando.

---

## Reglas críticas — NUNCA violar

1. **NO tocar:** `src/utils.js`, `src/api/login.js`, `verifyToken()`, `SAFE_SELF_FIELDS`, RLS de Supabase
2. **json() siempre 2 argumentos:** `json(data, status)` — nunca 3
3. **validate.js antes de cada commit en iporave-sistema:** `node validate.js` en C:\Users\USUARIO\iporave-sistema\
4. **No deployar sin permiso del usuario:** wrangler deploy solo cuando el usuario lo autorice
5. **No commitear sin validate.js OK**

---

## Estado del proyecto al momento del relevo

### Frontend (iporave-sistema) — último commit: 5c6c618
- ✅ Panel por rol completo (superadmin, vendedor, proveedor, dropshipper, delivery, cliente)
- ✅ Búsqueda global de pedidos
- ✅ Panel notificaciones push
- ✅ Facturas B2B (UI + Supabase)
- ✅ Analítica por rol (vendedor/proveedor)
- ✅ Dashboard superadmin con métricas
- ✅ Clientes recurrentes vendedor
- ✅ Panel delivery operativo con llamar/mapa
- ✅ Mobile layout fixes (botones flex-wrap, métricas grandes)
- ✅ Exportar pedidos CSV/Excel/PDF con filtros
- ✅ Botón IA arrastrable

### Catálogo público (catalog.html)
- ✅ Filtros precio min/max + ordenamiento
- ✅ Modal de detalle de producto
- ✅ Carrito con localStorage y envío por WA
- ✅ Skeleton loading shimmer
- ✅ Toggle dark/light mode
- ✅ Botón compartir por WhatsApp
- ✅ Footer con links del sitio

### Páginas públicas
- ✅ tracking.html — rastreo por número de pedido
- ✅ 404.html — con animación
- ✅ faq.html — acordeón con búsqueda
- ✅ contacto.html — formulario → WA
- ✅ terminos.html — 5 secciones

### Worker/API (iporave-worker) — completamente auditado
- ✅ Error handling robusto en TODOS los endpoints
- ✅ try/catch en todas las queries Supabase
- ✅ json() siempre con 2 argumentos
- ✅ Endpoint público /api/pizarron (GET + POST)
- ✅ Push notifications VAPID

---

## Tareas pendientes (prioridad alta)

1. **Auditoría JWT+RLS** — revisar que los tokens JWT sean validados correctamente en todos los endpoints y que las políticas RLS de Supabase estén bien configuradas. Esta tarea es para Claude Code cuando vuelva.
2. ~~**Ian delivery**~~ — CANCELADO por el usuario
3. **Tienda pública** — auto-registro de clientes, flujo de compra completo
4. **Codex (cuando vuelva)** — más mejoras visuales al panel según feedback del usuario

---

## Tareas que podés hacer vos (Gemini)

Seguras para asignar a Aider o sub-agentes:
- Mejoras visuales en catalog.html o páginas públicas
- Nuevas páginas HTML standalone en public/
- Error handling adicional en Worker (con las reglas críticas)
- Documentación
- Tests manuales de endpoints

**NO asignes sin permiso del usuario:**
- Cambios en login.js, utils.js, verifyToken
- Deploy a producción (wrangler deploy)
- Cambios en RLS de Supabase
- Modificación de tokens o secrets

---

## Ollama local disponible

Modelos instalados en la PC del usuario:
- `llama3.2:latest` — liviano, bueno para revisión
- `llama3.2:3b` — muy liviano, para supervisión
- `qwen2.5-coder:7b` — para código (puede estar descargando)

Endpoint local: `http://localhost:11434/api/chat`

---

## Keys disponibles (para que el usuario configure agentes)

Están en `C:\Users\USUARIO\node-red-config\api-keys.json`:
- groq ✅ — llama-3.3-70b-versatile (rápido, gratis)
- openrouter ✅ — múltiples modelos, algunos gratis
- cerebras ✅ — llama3.1-8b (muy rápido)
- kimi ✅ — moonshot-v1
- deepseek ❌ — sin saldo

---

## Protocolo de cada tarea

1. Leer el archivo a modificar
2. Planear el cambio mínimo necesario
3. Editar
4. Si es frontend: `node validate.js` en iporave-sistema/
5. Si es Worker: `node --check src/api/archivo.js` en iporave-worker/
6. Commit con mensaje descriptivo
7. Si es frontend: `git push origin main` (Vercel deploya solo)
8. Si es Worker: esperar permiso del usuario para `npx wrangler deploy`
9. Reportar al pizarrón

---

## Mensaje para el usuario

Si el usuario te pregunta qué hacer primero, decile:
"Estoy listo para continuar. Según el relevo, las tareas pendientes de mayor prioridad son: (1) Ian delivery — crear usuario, (2) mejoras visuales móvil adicionales, (3) cualquier página pública nueva que necesiten. ¿Por cuál empezamos?"
