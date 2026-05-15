# RELEVO CLAUDE — 2026-05-15 (ACTUALIZADO POST-OLEADA 2)

> Documento de contexto completo para retomar el trabajo si se cae la sesión.
> Última actualización: cierre oleada 2 (sistema de pagos + ítem 2J)

---

## 🟢 ESTADO ACTUAL DEL SISTEMA

### Deploys live en producción
| Componente | Versión | Estado |
|---|---|---|
| **Worker** (Cloudflare) | `ee13b168` | ✅ Live — Groq LLaMA + DeepSeek R1 + Anthropic fallback |
| **Frontend** (Vercel) | `c16b5f4` | ✅ Live — todas las features de esta sesión |
| **DB** (Supabase) | — | ✅ Tabla `pagos` creada con RLS |

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
