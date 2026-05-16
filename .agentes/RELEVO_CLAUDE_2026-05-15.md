# RELEVO CLAUDE — 2026-05-15 (ACTUALIZADO POST-BLOQUE-1.5)

## 🆕 SESIÓN EXTENDIDA — Lo que se agregó después del primer relevo

### Bloque 1 — Estado Financiero MVP (commit `bfab4dd`)
- DL.savePago, DL.getPagos con tabla pagos
- Renglones 3D clickeables con avatar coloreado por rol
- Doble botón: 💵 Registrar Pago / ✅ Pagado
- Modal con autocálculo en vivo del saldo restante
- PAGES.pago_usuario página dedicada con tabs período, métricas, calendario, paginación
- Card "💼 Estado Financiero" en dashboard

### Bloque 1.5 — Polish (commit `ae073d6`)
- Búsqueda + filtros por rol + ordenamiento
- Cuentas "at risk" (saldo > 0 y 30+ días sin actividad)
- Métricas avanzadas: días promedio pagar, vs mes pasado, Top 3
- Animaciones fadeInUp, indicadores de tendencia
- Paginación 20 items
- Botón Volver con flecha animada

### Fixes QA Audit aplicados
- Race condition en confirmarRegistroPago (botón disable)
- División por cero en _actualizarSaldoLive
- track.html: MAPBOX_TOKEN validation + typeof checks
- catalog.html: showToast clearTimeout, WA placeholder check, cantidad > 0, swap min/max

### Worker comprobantes (deploy `0f94ee15`)
- `/api/comprobantes/upload` — sube archivo a R2 + registra en tabla
- `/api/comprobantes/list?pago_id=X` — lista comprobantes del pago
- `/api/comprobantes/delete?id=X` — borra
- SQL `pagos_comprobantes.sql` ya corrido en Supabase

### En curso (agentes en paralelo)
- Codex Bloque 2 — UI comprobantes en frontend
- Worker — endpoint Gemini 2.5 Pro + Cron Monitor 15 min
- Análisis de bugs del mapa (read-only)

### Pendientes nuevos identificados por el usuario
- Bugs del mapa: 3A "Solo Deliveries" muestra pedidos, 3B reset automático, 3C filtros de estado muestran delivery, 3D color por delivery, 3E botones de zona
- Boletas: 13A espaciado, 13B calendario
- Sidebar: 14A flechita colapsable
- Cierre jornada: 14B botón 3D centrado (✅ hecho)
- Toggle alertas: 14C diseño 3D + funcional (✅ hecho)
- Limpieza menú: 15A Balance vs Estadísticas (verificado: son diferentes)
- Multi-rol del mismo usuario (ítem 36 reformulado: NO multi-tenant, sino multi-cuenta del mismo dueño)
- Base de datos de clientes por zona (ítem 37 nuevo)
- Estado financiero escalable por permisos de plan (ítem 4N nuevo)

### Investigación pendiente
- Gemini 3.1 Pro vía Vertex AI (CONFIRMADO disponible — requires service account JSON)
- ChatGPT API key situation (usuario investiga)

---

# RELEVO ANTERIOR (ÚLTIMA OLEADA 2)

> Documento de contexto completo para retomar el trabajo si se cae la sesión.
> Última actualización: cierre oleada 2 (sistema de pagos + ítem 2J)

---

## 🟢 ESTADO ACTUAL DEL SISTEMA

### Deploys live en producción
| Componente | Versión | Estado |
|---|---|---|
| **Worker** (Cloudflare) | `ee13b168` | ✅ Live — Groq LLaMA + DeepSeek R1 + Anthropic fallback |
| **Frontend** (Vercel) | `101e94e` | ✅ Live — auditoría + botones 3D coherentes + fixes |
| **DB** (Supabase) | — | ✅ Tabla `pagos` creada con RLS |

### Auditoría última (commit `101e94e`)
Sistema verificado 95-100% funcional:
- 119/120 funciones existen y funcionan
- 29/29 PAGES implementadas
- 69/70 botones operativos
- `openConvThread` se reportó como roto pero **SÍ existe** en línea 9793 (falso positivo del auditor)
- 3 duplicaciones `'En Ruta'||'En Ruta'` corregidas a `'En Ruta'||'En ruta'` (defensivo)
- Botones 3D coherentes aplicados a analítica vendedor (4) + catálogo (1)

### URLs
- App: https://iporave-sistema.vercel.app
- Worker: https://iporave-api.iporaveparaguay.workers.dev
- Repo frontend: https://github.com/iporaveparaguay/iporave-sistema

### Credenciales / Config
- Usuario: iporaveparaguay@gmail.com (business)
- API key Anthropic: configurada en Cloudflare (~$4.25 saldo)
- API key Groq: configurada en Cloudflare (free tier)
- Mapbox token: en Cloudflare env, expuesto vía `/api/config`

---

## ✅ IMPLEMENTADO EN ESTA SESIÓN

### Oleada 1 (commit `80620f2`)

**Grupo 1 — Bugs:**
- ✅ `'En ruta'` → `'En Ruta'` (37 cambios, R mayúscula)
- ✅ Eliminado `'En camino'` del filtro del mapa
- ✅ `nav('pedidos')` → `nav('orders')` línea 7773
- ✅ `PAGES.perfil` completa para cliente (3 cards: datos, dirección, preferencias)

**Grupo 2 — Delivery:**
- ✅ Delivery solo ve pedidos Despachado/En Ruta/Entregado
- ✅ Pedidos Entregado desaparecen del mapa del delivery
- ✅ Quitada redirección a WhatsApp al cambiar a En Ruta
- ✅ Push a vendedor + dropshipper + creador cuando cambia estado
- ✅ Realtime ampliado a mapa y delivery

**Grupo 3 — Mapa:**
- ✅ Botones 3D modernos `.mapBtn` con dots de color
- ✅ Filtros: Todos / Pendiente / Despachado / En Ruta / Entregado
- ✅ Toggle Solo Deliveries / Solo Pedidos
- ✅ Dropdown buscar delivery específico
- ✅ Función `_aplicarFiltrosMapa()` orquesta filtros

**track.html (página tracking cliente):**
- ✅ Rediseño premium nivel Rappi/Uber Eats
- ✅ Header logo Iporãve + gradient naranja
- ✅ Hero con emoji animado + badge animado por estado
- ✅ Card delivery con foto + Llamar + WhatsApp
- ✅ Mapa Mapbox dark con markers animados (sonar)
- ✅ Refresh 10s cuando En Ruta
- ✅ Token Mapbox via `/api/config` (no hardcoded)

### Oleada 2 (commit `c16b5f4`)

**Grupo 4 — Sistema de pagos completo:**
- ✅ Tabla `pagos` en Supabase con RLS (script SQL corrido por usuario)
- ✅ `DL.savePago(p)` y `DL.getPagos(filtros)` en DataLayer (líneas ~1659-1683)
- ✅ `PAGES.pagos` (líneas ~11181-11304):
  - Admin/super: lista usuarios con avatar, ganado, pagado, saldo (rojo/verde) + botones "Registrar Pago" + "Ver Historial"
  - Otros roles: card "Te deben", historial de pagos recibidos
- ✅ Modal "Registrar Pago": monto, método (Efectivo/Transferencia/Logística externa/Otro), referencia, nota, fecha
- ✅ Cálculo ganado por rol:
  - Vendedor: `ganVend(o)` sobre Entregados del mes
  - Dropshipper: `comision × qty`
  - Proveedor: `costo × qty`
  - Delivery: sueldo fijo × días + premios cupos
- ✅ Realtime: notif push cuando se registra pago
- ✅ Nav: `💵 Pagos` (admin/super) / `💰 Mis Pagos` (otros)

**Ítem 2J:**
- ✅ Quitado auto-redirect Google Maps cuando delivery cambia a En Ruta

---

## 📋 PENDIENTE — LISTA COMPLETA

### 🔴 Grupo 1 — Bugs (mayormente cerrado)
- ⏸️ **Ítem 5**: `_activarPush()` función no existe (definir antes)
- ⏸️ **Ítem 6**: `_clienteCalificarUltimo()` ídem
- ⏸️ **Ítem 8**: `recaudacion` vs `recaudacion_dlv` en nav delivery

### 🚴 Grupo 2 — Delivery (mayormente cerrado)
- ⏸️ **Ítem 2F** *(futuro)*: Admin puede poner foto del delivery en el pin

### 💰 Grupo 4 — Pagos (cerrado, listo para probar)

### 🎨 Grupo 5 — Visual / Tema (TODO pendiente)
- ⏸️ **Ítem 17**: Dark/Light mode toggle visible (estilo Shopify, blanco suave)
- ⏸️ **Ítem 18**: Color picker / eyedropper — absorber color del logo
- ⏸️ **Ítem 19** *(futuro)*: Editor de tema completo estilo Shopify (en español)

### 🏢 Grupo 6 — Perfil / Empresa
- ⏸️ **Ítem 20**: Campos extras perfil (descripción tienda, redes, horarios)
- ⏸️ **Ítem 21**: Configuración empresa mejorada (logo, colores, RUC, timbrado)

### 🤖 Grupo 7 — IA / Asistente (TODO pendiente, GRANDE)
- ⏸️ **Ítem 7A**: Asistente con acceso de acción (function calling vía Groq)
  - "Poné el pedido #123 en ruta" → ejecuta
  - "Cuál es mi pedido más urgente" → consulta
  - REQUIERE: cambios en worker (claude.js) para tool_calls + cambios en frontend
- ⏸️ **Ítem 7B**: Burbuja arrastrable — YA EXISTE confirmado
- ⏸️ **Ítem 7C**: Notificación push cuando asistente termina acción
- ⏸️ **Ítem 7D** *(futuro)*: Voz desde burbuja (WebRTC/Groq Whisper)
- ⏸️ **Ítem 7E** *(app nativa)*: Chat head fuera de la app — no posible con PWA
- ⏸️ **Ítem 7F**: Historial chat en sección "Mensajes" (guardar 1 semana? definir)
- ⏸️ **Ítem 7G**: Posición original burbuja al iniciar sesión
- ⏸️ **Ítem 7H** *(diferido +2 días)*: Asistente por WhatsApp
- ⏸️ **Ítem 7I**: Cada admin/super con SU número WhatsApp del asistente

### 📦 Grupo 8 — Catálogo público
- ⏸️ **Ítem 26**: WhatsApp vendedor en `catalog.html` es placeholder `595981000000`
- ⏸️ **Ítem 27**: Fotos reales de productos (hoy fallback 📦)

### 🔔 Grupo 9 — Notificaciones
- ⏸️ **Ítem 30**: Push nativo al cliente además de WhatsApp

### 🔒 Grupo 10 — Producción / Seguridad
- ⏸️ **Ítem 31**: Eliminar `DEVICE_CHECK_BYPASS_EMAILS` antes de prod real
- ⏸️ **Ítem 32**: Exportar CSV para dropshipper

### 💳 Grupo 11 — Suscripciones (CONTEXTO, no implementar aún)
- ⏸️ **Ítem 33**: Proveedor con suscripción paga:
  - ✅ Sí: sus herramientas, catálogo propio, crear pedidos propios
  - ❌ No: crear usuarios (delivery, vendedor, dropshipper)
  - ❌ No: gestionar usuarios de otros roles
- ⏸️ **Ítem 34**: Tienda pública también pago
- ⏸️ **Ítem 35**: Menús restringidos por plan
  - UX: todos los menús visibles, al hacer click en bloqueado → notif "Desbloqueá con plan X"

### 🎨 Grupo 12 — Coherencia visual
- ⏸️ **Ítem 12**: Aplicar diseño 3D de botones del mapa a TODOS los filtros del sistema

### Ideas futuras
- Catálogo con checkbox para mostrar/ocultar precio proveedor/vendedor/mayorista
- Link de tienda personal por usuario (cada vendedor tiene su URL)

---

## 🔑 CONTEXTO TÉCNICO

### Arquitectura
- SPA `public/index.html` (~11.030 líneas, ~640KB)
- Worker Cloudflare `iporave-worker/`, módulos en `src/api/`
- Supabase Auth + RLS
- Vercel frontend, Cloudflare backend

### Convenciones críticas
- **NUNCA escribir `</script>` literal** en strings JS — dividir como `'</'+'script>'`
- **`validate.js` debe pasar** antes de cualquier commit a `index.html`
- Estados en `'En Ruta'` (R mayúscula). Sistema acepta ambas formas defensivamente
- Globales: `CU`, `_ordersCache`, `_usersCache`, `_sessionToken`, `_supa`, `_supaConnected`, `WORKER_URL`
- Helpers: `$()`, `fmt()`, `pushNotif()`, `nav()`, `getCfg()`, `getUser()`, `ganVend()`

### Zonas index.html
- Líneas 1-2668: Claude Code (auth, DL, Supabase, realtime, push) — INTOCABLE
- Líneas 2669+: Codex (UI páginas, formularios)
- Archivos nuevos en `public/`: Antigravity (catalog.html, track.html)
- `iporave-worker/`: Claude Code exclusivo

### Roles
1. superadmin — acceso total + DeepSeek R1
2. admin — gestión usuarios y pedidos
3. vendedor — pedidos, clientes, catálogo
4. proveedor — suministros, pagos, catálogo
5. dropshipper — pedidos, balance, liquidación
6. delivery — entregas, cupo, recaudación
7. cliente — pedidos, boletas, mi perfil

### Modelos IA
- Todos los roles: `llama-3.3-70b-versatile` (Groq, ~14.400 req/día)
- Superadmin: `deepseek-r1-distill-llama-70b` (Groq, ~1.000 req/día)
- Fallback: `claude-haiku-4-5-20251001` (Anthropic)

### Reglas de seguridad
- `verifyToken()` en utils.js — INTOCABLE
- `save-user.js` `SAFE_SELF_FIELDS` — INTOCABLE
- RLS solo vía dashboard Supabase manual
- `DEVICE_CHECK_BYPASS_EMAILS` eliminar antes de prod

### Flujo de pedidos (actualizado tras oleada 1-2)
1. Vendedor/admin crea pedido → `Pendiente`
2. Admin despacha → `Despachado` → WhatsApp auto al cliente
3. Admin asigna delivery → delivery ve el pedido en su panel
4. Delivery cambia a `En Ruta` → WhatsApp auto al cliente con link tracking + push a relacionados
5. Delivery aprieta "Navegar" cuando quiere (NO automático) → Google Maps
6. Delivery sube foto + método cobro → `Entregado`
7. Admin/vendedor califica delivery
8. Pedido desaparece del mapa del delivery

---

## 🛠️ COMANDOS ÚTILES

```bash
# Validar antes de commit
cd ~/iporave-sistema && node validate.js

# Deploy worker
cd ~/iporave-worker && npx wrangler deploy

# Deploy frontend (Vercel auto-deploya con push)
cd ~/iporave-sistema && git push

# Configurar secret en worker
cd ~/iporave-worker && npx wrangler secret put NOMBRE_VARIABLE
```

---

## 💬 FILOSOFÍA DE TRABAJO ACTUAL

- **Ritmo**: Un tema a la vez, presentar → esperar → avanzar
- **Confirmación**: Esperar "sí/ok/procede" antes de acción importante
- **Idioma**: Siempre español
- **Commit**: Solo con aprobación explícita o modo automático
- **Modo automático**: Activable con "permiso total" / "metele"
- **Agentes**: Delegar a Codex/Antigravity. Claude monitorea
- **Cuando un agente se traba esperando confirmación**: Relanzarlo con autorización explícita en el prompt

---

## 📝 ÚLTIMA INTERACCIÓN

Usuario pidió guardar relevo después de oleada 2 (sistema de pagos + ítem 2J) por riesgo de caída de Anthropic (cayó ayer). Sin tareas en curso, todo deployado, todos los agentes terminaron limpios.

**Próximo paso natural al retomar:**
1. Probar lo desplegado en navegador
2. Decidir cuál grupo atacar siguiente
   - Probable: Grupo 7 asistente agentic (function calling)
   - O Grupo 5 visual/tema (dark-light mode)
   - O Grupo 12 coherencia visual (3D buttons en todo el sistema)

---

## 🔥 SI SE CAE LA SESIÓN — RECUPERACIÓN

1. Leer este archivo completo
2. Verificar estado actual con: `cd ~/iporave-sistema && git log --oneline -5`
3. Si último commit es `c16b5f4` o posterior → el sistema está al día
4. Preguntar al usuario qué grupo retomar
5. NO empezar a implementar sin que el usuario confirme
