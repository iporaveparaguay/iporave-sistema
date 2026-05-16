# MASTER PENDIENTES — Iporãve Connect
**Fecha:** 2026-05-16 — Consolidado de todas las sesiones y auditorías  
**Fuentes:** v3→v7 RELEVOs + 8 agentes (mi sesión) + 5 agentes (otra sesión Claude $20)

---

## 🔴 BLOQUE 1 — BUGS CRÍTICOS (bloquean funcionalidad core)

### De la sesión v7 (otro Claude) — confirmados con agentes

| ID | Bug | Archivo | Línea | Fix |
|----|-----|---------|-------|-----|
| C1 | `_notificaciones` usada en Realtime ANTES de ser declarada → TypeError crash | index.html | ~5346 | Mover declaración arriba o lazy init |
| C2 | `SVG.rotateCcw` usado en DL.saveOrder antes de que SVG esté definido | index.html | ~2000 | Mover `const SVG={}` antes de DL |
| C3 | `_shownMsgIds.add()` en canal Realtime antes de declaración | index.html | ~5159 | Mover declaración o lazy init |
| C4 | `_cleanAllAppStorage` definida DOS VECES (~4356 y ~4565) → logout inconsistente | index.html | 4356+4565 | Mergear en una sola función |
| C5 | `crearPedidoDesdeProducto` usa IDs DOM incorrectos (noProducto→nProd, etc.) | index.html | ~7400 | ✅ CORREGIDO en f7d536c |
| C6 | `openNuevoPedido()` llamada por atajo 'N' pero función no existe | index.html | ~atajo | Crear función o remover atajo |
| C7 | Realtime proveedor filtra por `vendedor_id` en vez de `proveedor_id` | index.html | ~initRealtime | ✅ CORREGIDO en f7d536c |
| C8 | `clientes_zonas` usa `o.zonaId` (no existe) en vez de `o.zona` | index.html | ~PAGES.clientes_zonas | ✅ CORREGIDO en f7d536c |
| C9 | `resetAll()` sin verificación de rol → admin podría borrar todo | index.html | ~resetAll | Verificar CU.rol==='superadmin' |
| C10 | `editUser()` no protege contra editar usuarios de otro admin o superadmin | index.html | ~editUser | Verificar created_by |
| C11 | `backup.js` sin auth real de rol — cualquier JWT válido ejecuta backup | iporave-worker | backup.js | Verificar rol superadmin |
| C12 | `/api/backup/list` sin autenticación de ningún tipo | iporave-worker | backup.js | Agregar verifyToken |

### De mis agentes (v6) — no todos corregidos en f7d536c

| ID | Bug | Archivo | Línea | Estado |
|----|-----|---------|-------|--------|
| C13 | XSS `descripcion_html` sin DOMPurify (ver detalle) | index.html | 11461 | ✅ CORREGIDO en 3fcc1b3 |
| C14 | localStorage sin prefijo por usuario → mezcla datos superadmin/admin | index.html | 2271-2272 | ✅ CORREGIDO en 3fcc1b3 |
| C15 | `_switchAccount()` no limpia cache → datos persisten | index.html | 4324 | ✅ CORREGIDO en 3fcc1b3 |
| C16 | `confirm()` async en iOS PWA → botón Confirmar delivery no funciona | index.html | 7337 | ✅ CORREGIDO en 3fcc1b3 |
| C17 | `#mapaBackBtn` visible problem (botón molestaba) | index.html | ~14881 | ✅ ELIMINADO en 9146489 |

---

## 🟠 BLOQUE 2 — BUGS ALTOS (flujos principales afectados)

| ID | Bug | Archivo | Línea | Estado |
|----|-----|---------|-------|--------|
| A1 | Pedidos del cliente filtran por nombre (no ID) → 2 clientes mismos nombre ven pedidos del otro | index.html | ~filtro clientes | PENDIENTE |
| A2 | `_fotoBase64` no se resetea entre pedidos → foto anterior puede confirmar otro pedido | index.html | ~confirmDlv | PENDIENTE |
| A3 | `_gpsToggleFromPill` usa `confirm()` → iOS PWA pausa GPS accidentalmente | index.html | ~pill GPS | PENDIENTE |
| A4 | Foto entrega guardada como base64 en Supabase (sin R2) → puede superar límite | index.html | ~confirmDlv | PENDIENTE |
| A5 | Estado "Reprogramado" no detiene GPS loop → consume batería delivery | index.html | ~_gpsLoopTick | PENDIENTE |
| A6 | `loadServerConfig` falla → `mapboxgl.accessToken` vacío → crash no capturado al abrir mapa | index.html | ~loadServerConfig | PENDIENTE |
| A7 | Marcadores coordenadas null/0 → TypeError rompe TODOS los marcadores si uno falla | index.html | ~mapa marcadores | PENDIENTE |
| A8 | `_liqDrop` calcula ganancia con `ganVend()` (lógica vendedor) → montos incorrectos | index.html | ~_liqDrop | PENDIENTE |
| A9 | Comisión ×qty en `_liqDrop` pero NO en `analitica_drop` → inconsistencia financiera | index.html | ~analitica_drop | PENDIENTE |
| A10 | `o.precio * o.qty` sin `||0` en balance, tabla pedidos y CSV → NaN con pedidos legacy | index.html | múltiple | PENDIENTE |
| A11 | `saveNewZona()` muestra "Zona creada" ANTES de confirmar Supabase | index.html | ~saveNewZona | PENDIENTE |
| A12 | `doDelUser()` sin verificar pedidos activos → delivery eliminado deja pedidos huérfanos | index.html | ~doDelUser | PENDIENTE |
| A13 | `PAGES.usuarios` no filtra por `created_by` → admin ve y puede editar usuarios de otros admins | index.html | ~PAGES.usuarios | PENDIENTE |
| A14 | `waSend()` con `window.open('_blank')` → saca al usuario de la app en iOS | index.html | 3186 | PENDIENTE |
| A15 | `_scannerNPLock` nunca se resetea en error de OpenFoodFacts → scanner inutilizable | index.html | ~10573 | PENDIENTE |
| A16 | `getPagos({})` sin filtro de rol → admin ve todos los pagos del sistema | index.html | 2807 | PENDIENTE |
| A17 | `corsHeaders()` sin request → fija CORS al primer origen → roto para otros dominios | iporave-worker | utils.js | PENDIENTE |
| A18 | `catalogo-publico.js` expone `proveedor_nombre` y `codigo_barras` sin autenticación | iporave-worker | catalogo-publico.js | PENDIENTE |
| A19 | `gps-pill` height:30px → bajo 44px mínimo Apple HIG (botón crítico delivery) | index.html CSS | ~pill | PENDIENTE |
| A20 | `mhead`/`mfoot` sticky iOS Safari roto → header/footer modal se desplazan con scroll | index.html CSS | ~modal | PENDIENTE (ver CRIT-8) |
| A21 | `ejecutarCierre()` sobreescribe silenciosamente cierre del día → sin advertencia | index.html | ~8969 | PENDIENTE |
| A22 | `pagado_por` usa `CU.auth_id` (UUID) vs `pagado_a` integer → posible error tipo Supabase | index.html | 15625 | VERIFICAR |
| A23 | RLS policies Supabase posiblemente `using(true)` → cualquier auth ve todo | Supabase | consola | VERIFICAR MANUAL |

---

## 🟡 BLOQUE 3 — BUGS MEDIOS (afectan UX significativamente)

| ID | Bug | Línea/Archivo | Estado |
|----|-----|--------------|--------|
| M1 | WhatsApp sin validación formato 595XXXXXXXXX | index.html ~11990 + save-user.js | PENDIENTE |
| M2 | `created_by` null bypasea filtro en `getOrders()` fallback | index.html 2405 | PENDIENTE |
| M3 | `_gpsSendPos` silencia errores de red → delivery no sabe si GPS falla | index.html ~14573 | PENDIENTE |
| M4 | `.page-mapa` class nunca se asigna al DOM → CSS selector no aplica | index.html 1105 | PENDIENTE |
| M5 | Panel filtros mapa se oculta bajo topbar sticky | index.html 551 | PENDIENTE |
| M6 | `--mapa-offset:160px` corta mapa en iPhones con notch | index.html ~1094 | PARCIAL (175px en f7d536c) |
| M7 | `saveNewOrder` sin validación de dirección ni stock | index.html ~7647 | PENDIENTE |
| M8 | `_TRACK_ESTADO_ICON` sin badge urgencia +24h en tarjetas delivery | index.html ~6592 | PENDIENTE |
| M9 | `.btn` mobile `min-height:38px` < 44px requerido | index.html 1501 | PENDIENTE |
| M10 | Botones popup mapa con `min-height:36px` | index.html 14136 | PENDIENTE |
| M11 | 16 instancias de `confirm()` nativo restantes (líneas 11278, 12843, 15614, etc.) | index.html | PENDIENTE |
| M12 | Sidebar footer sin `safe-area-inset-bottom` → botones bajo barra gestos iPhone | index.html 335 | PENDIENTE |
| M13 | `textarea resize:vertical` incómodo en mobile táctil | index.html 88 | PENDIENTE |
| M14 | Mensajes GPS error no diferencian iOS/Android | index.html ~_gpsLoopTick | PENDIENTE |
| M15 | Botón "Llamar" (tel:) faltante en tarjetas delivery | index.html ~6619 | PENDIENTE |
| M16 | Sin botón "Llamar" en el agente tiene el código exacto | index.html ~6619 | PENDIENTE |
| M17 | GPS mensajes sin ruta específica iOS (Ajustes→Privacidad→Localización) | index.html ~_gpsLoopTick | PENDIENTE |
| M18 | `track.html` número WA soporte ficticio 595981234567 | track.html | ✅ CORREGIDO f7d536c |
| M19 | Viewport meta sin `interactive-widget=resizes-visual` | index.html línea 5 | PENDIENTE |

---

## 📱 BLOQUE 4 — MOBILE UX PENDIENTE

| ID | Issue | Prioridad |
|----|-------|-----------|
| MOB1 | Topbar kebab ⋯ → dropdown con 4 botones secundarios | ✅ CORREGIDO 3fcc1b3 |
| MOB2 | `.btn-sm` inline `padding:5px 11px` → área táctil ~26px | ALTO |
| MOB3 | 7 botones export en tbActions pedidos → dropdown kebab "Exportar ⋮" | ALTO |
| MOB4 | Banner sticky verde "✓ Crear producto" en `openNuevoProducto()` | ALTO |
| MOB5 | Botones GPS y estilos mapa superpuestos (bottom:10-14px right:12px) | ALTO |
| MOB6 | "Mostrar filtros" mapa (`pointer-events:none`) no tapeable | ALTO |
| MOB7 | Combos zona/vendedor mapa: 2 filas en topbar mobile | ✅ CORREGIDO f7d536c |
| MOB8 | Sidebar z-index 200 < pines Mapbox → hamburguesa tapada | ✅ CORREGIDO f7d536c |
| MOB9 | Auditoría completa app mobile por secciones (delivery, mapa, formularios, catálogo) | PENDIENTE |
| MOB10 | Configurar delivery: modal guardar config pago | ✅ CORREGIDO 9146489 |

---

## 🎨 BLOQUE 5 — EMOJIS REMANENTES (~167 instancias)

### Objetos críticos (3 a migrar de una vez):

| Objeto | Línea | Emojis a reemplazar |
|--------|-------|---------------------|
| `_TRACK_ESTADO_ICON` | ~13354 | ⏳→clock, 📦→pkg, 🛵→scooter, ✅→checkCircle, ❌→xCircle, ↩️→rotateCcw |
| `stateDefs` | ~5674-5680 | mismos 6 |
| `stepIcons` | ~7025 | ⏳→clock, 📦→pkg, 🚴→scooter, ✅→checkCircle |

### Por emoji (total instancias):
- 📦 → SVG.pkg (46 instancias)
- ✅ → SVG.checkCircle (35)
- ⚠️ → SVG.alertTriangle (19)
- 📍 → SVG.mapPin (20)
- ⏳ → SVG.clock (17)
- 🛵 → SVG.scooter (16)
- 💰 → SVG.dollar (14)
- 💬 → SVG.chat (11)
- ❌ → SVG.xCircle (12)
- 🚚 → SVG.truck (6)
- 📅 → SVG.calendar (5)
- 📋 → SVG.clipboard (5)
- 👤 → SVG.user (6)
- 👥 → SVG.users (5)
- 🔔 → SVG.bell (3)
- Otros (🔄, 📊, ⭐, 🏆, 🎯, 🔗, 🔒, 🚫, etc.) (~50 instancias)

---

## 🔒 BLOQUE 6 — SEGURIDAD PENDIENTE

| ID | Issue | Archivo | Estado |
|----|-------|---------|--------|
| SEC1 | XSS `descripcion_html` sin DOMPurify | index.html 11461 | ✅ CORREGIDO 3fcc1b3 |
| SEC2 | `openA()` recibe HTML crudo — riesgo sistémico por concatenación | index.html 2173 | PENDIENTE (diseño) |
| SEC3 | `backup.js` sin auth de rol — cualquier JWT ejecuta backup | iporave-worker | PENDIENTE |
| SEC4 | `/api/backup/list` sin auth | iporave-worker | PENDIENTE |
| SEC5 | `corsHeaders()` fija CORS al primer origen sin leer request | iporave-worker utils.js | PENDIENTE |
| SEC6 | `catalogo-publico.js` expone columnas sensibles sin auth | iporave-worker | PENDIENTE |
| SEC7 | CSP tiene `'unsafe-inline'` — nonces pendientes | index.html | PENDIENTE |
| SEC8 | Webhook WhatsApp sin firma HMAC | iporave-worker | PENDIENTE |
| SEC9 | 2FA para acciones críticas (eliminar usuario, resetAll, cierre jornada) | index.html | PENDIENTE |
| SEC10 | RLS Supabase verificar que no sea `using(true)` | Supabase consola | VERIFICAR MANUAL |
| SEC11 | SQL injection ilike en catalog-public.js | iporave-worker | ✅ CORREGIDO dca0010/deployado |

---

## 🛠️ BLOQUE 7 — HELPERS UX (definidos, nunca aplicados)

| Helper | Función | Aplicar en |
|--------|---------|-----------|
| `_withLoading(btn, fn)` | Deshabilita botón y muestra spinner durante operación async | saveOrder, saveUser, saveProducto, savePago |
| `_confirmDoubleClick` | Requiere doble clic en acciones destructivas | Eliminar usuario, eliminar producto, eliminar zona |
| `_copyWithCheck` | Copia al clipboard con feedback visual ✓ | Botones copiar teléfono/ID/dirección/link |
| `_flashSuccess` | Flash verde breve tras guardado exitoso | Todos los guardados exitosos |

---

## 📋 BLOQUE 8 — COACHMARKS / TUTORIALES PENDIENTES

| Coachmark | Página | Estado |
|-----------|--------|--------|
| Recaudación Delivery | PAGES.delivery | PENDIENTE |
| Boletas IVA | PAGES.boletas | PENDIENTE |
| Cierre Jornada | PAGES.cierre | PENDIENTE |
| Escáner de código de barra | PAGES.catalogo | PENDIENTE |
| Mapa en tiempo real | PAGES.mapa | PENDIENTE |

---

## 🔄 BLOQUE 9 — REACTIVAR SEMANA 2026-05-23

| Item | Archivo | Qué hacer |
|------|---------|-----------|
| `_perfilCompleto()` desactivado | index.html ~11973 | Eliminar línea `return{ok:true,missing:[]};` — la lógica original sigue abajo |

---

## 🚀 BLOQUE 10 — FEATURES FUTURAS (no empezar sin aprobación)

### Tienda Pública (PLAN_TIENDA_PUBLICA.md)
- Landing + catálogo `iporaveparaguay.com`
- Carrito persistente, checkout multi-paso
- Login opcional post-compra
- Confirmación por WhatsApp
- Sub-tienda por vendedor/dropshipper `/v/{slug}`
- Ficha producto SEO `/p/{slug}`
- Integración con pipeline de pedidos existente
- Nuevo worker endpoint `/api/tienda/checkout`
- Auto-registro cliente post-compra

### Sistema de Suscripciones SaaS (PLAN_SUSCRIPCIONES.md)
- Tiers: Free (Gs 0) / Pro (Gs 99.000/mes) / Business / Enterprise
- Locks de features con modal "Desbloqueá con Plan X"
- Tabla `subscripciones` en Supabase
- Webhook de pago (PagoPA/BancoRed/transferencia)
- Panel de cobros del superadmin

### Multi-rol / Cuentas vinculadas (PLAN_MULTI_ROL.md)
- Tabla `user_groups` + `user_group_members`
- Panel "Mi Negocio" con balance consolidado de todas las cuentas del mismo dueño
- Switcher ya implementado (account switcher liviano) — falta el aggregado

### Mapbox V6 Premium
- Reemplazar Mapbox GL JS actual por V6
- Look tipo Tesla, dark mode
- 150+ pines fluidos
- Marcadores 3D

### WhatsApp Asistente por Cliente
- Bot WA propio por cliente con su número
- Integración con Twilio o Meta Business API
- Flujo de consultas, seguimiento de pedido

### PWA Offline Avanzado
- Cola `pending` actual solo cubre `DL.saveOrder`
- Extender a: saveProducto, saveUser, savePago
- Sync automático cuando vuelve la conexión

### Push Notifications Completas
- Actualmente: admin y delivery
- Extender a: vendedor, dropshipper, proveedor, cliente
- Notificaciones de: pago recibido, pedido asignado, comisión liquidada

### Document AI Processor
- Configuración Google Cloud Document AI
- Procesamiento de facturas/comprobantes automático
- OCR de cédulas y documentos

### API Keys Propias por Cliente
- WA, Shopify, otros servicios
- Puente directo a Shopify por cliente
- Dashboard de integraciones

### Rol Empresa (Sub-admin mejorado)
- Sub-admin con permisos granulares
- Gestión de múltiples sucursales
- Dashboard consolidado

---

## 📊 BLOQUE 11 — ITEMS ARRASTRADOS DE SESIONES ANTERIORES

| Item | Descripción | Desde |
|------|-------------|-------|
| Categorías editables | Admin pueda crear/editar/eliminar categorías del catálogo | v3 |
| Clientes recurrentes vendedor | Panel de clientes frecuentes para rol vendedor | v3 |
| Facturación B2B módulo | Módulo completo entre roles (boletas ya en nav, módulo largo plazo) | v3 |
| Estado financiero escalable | Panel de pagos con permisos por plan de suscripción | v15 (2026-05-15) |
| Gemini 2.5 Pro vía Vertex AI | Requiere service account JSON de Google Cloud | v15 |
| Mapa bugs reportados | 3A solo deliveries muestra pedidos, 3B reset automático, 3C filtros estado, 3D color por delivery | v15 |
| Botón Editar presentación | En modal de edición de producto | todo-list actual |
| Test GPS tracking en vivo | Verificar GPS real con delivery real | todo-list actual |
| Asistente voz/conversación | Botón micrófono en chat IA, STT→TTS | todo-list actual |
| Gemini Flash Imagen | Análisis de imágenes de productos con Gemini | v14+ |
| Multi-rol nuclear (DB refactor) | Un usuario con múltiples roles reales en DB — muy largo plazo | v3 |
| Boletas: espaciado y calendario | 13A espaciado fecha, 13B integración calendario | v15 |
| Sidebar: flechita colapsable | 14A sidebar con collapse animado | v15 |

---

## ⚙️ BLOQUE 12 — ACCIONES MANUALES PENDIENTES (usuario debe hacer en consola)

| Acción | Dónde | Instrucción |
|--------|-------|-------------|
| Verificar RLS Supabase | consola.supabase.com → Policies | Que NO haya políticas `using(true)` en tablas pedidos/usuarios/pagos |
| `wrangler secret put MAPBOX_TOKEN` | PowerShell en iporave-worker/ | Mover token de wrangler.toml a secret |
| Crear tabla `auditoria` | Supabase SQL editor | Requerida por admin-tools cleanup |
| Configurar `env.CLEANUP_OTP` | Cloudflare dashboard → Workers → Settings | Secret para endpoint cleanup |
| Número WA soporte en track.html | Archivo track.html | ✅ CORREGIDO f7d536c — definir número real |
| Telegram bot configurar | Cloudflare dashboard | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |

---

## 📌 RESUMEN EJECUTIVO — QUÉ HACER PRIMERO

### Esta sesión (tokens nuevos):
1. **C1/C2/C3** — Orden de declaración JS (crash Realtime)
2. **C4** — `_cleanAllAppStorage` duplicada
3. **C6** — `openNuevoPedido()` función fantasma
4. **C9/C10** — `resetAll` + `editUser` sin verificación de rol
5. **C11/C12** — `backup.js` sin auth
6. **A14** — `waSend()` fix iOS
7. **MOB2/MOB3/MOB4/MOB5/MOB6** — Mobile UX altos

### Próxima semana:
1. Bloque A1/A2/A3 — flujos delivery
2. Emojis: objetos _TRACK_ESTADO_ICON + stateDefs + stepIcons
3. Helpers _withLoading aplicados masivamente
4. Reactivar `_perfilCompleto()` (semana 2026-05-23)

### Mediano plazo:
- Tienda pública MVP
- Sistema suscripciones diseño
- Multi-rol aggregado

---

**Fin del documento. Generado 2026-05-16 consolidando v3→v7 + 13 agentes de auditoría.**
