# MASTER PENDIENTES v2 — Iporãve Connect
**Fecha:** 2026-05-16 — Consolidado FINAL de todas las sesiones y auditorías  
**Fuentes:** v3→v7 RELEVOs + 10 agentes oleadas 1/2/3 (sesión actual) + 5 agentes (otra sesión Claude $20)  
**Total bugs identificados:** ~80 items (críticos + altos + medios + bajos)

---

## 🔴 BLOQUE 1 — BUGS CRÍTICOS (bloquean funcionalidad core)

| ID | Bug | Archivo | Línea aprox. | Estado |
|----|-----|---------|--------------|--------|
| C1 | `_notificaciones` usada en Realtime ANTES de ser declarada → TypeError crash | index.html | 2101 vs 5370 | PENDIENTE |
| C2 | `const SVG` declarado en línea 4809 pero usado en línea 2520 → TDZ ReferenceError crash | index.html | 2520 vs 4809 | PENDIENTE |
| C3 | `_shownMsgIds.add()` en Realtime antes de declaración | index.html | 4649 vs 5183 | PENDIENTE |
| C4 | `_cleanAllAppStorage` definida DOS VECES (líneas 4380 y 4589) → logout inconsistente | index.html | 4380+4589 | PENDIENTE |
| C5 | `crearPedidoDesdeProducto` usa IDs DOM incorrectos | index.html | — | ✅ CORREGIDO f7d536c |
| C6 | `openNuevoPedido()` llamada por atajo 'N' pero función no existe | index.html | atajo teclado | PENDIENTE |
| C7 | Realtime proveedor filtra por `vendedor_id` en vez de `proveedor_id` | index.html | initRealtime | ✅ CORREGIDO f7d536c |
| C8 | `clientes_zonas` usa `o.zonaId` (no existe) en vez de `o.zona` | index.html | PAGES.clientes_zonas | ✅ CORREGIDO f7d536c |
| C9 | `resetAll()` sin verificación de rol → cualquier admin puede borrar todo | index.html | 12944 | PENDIENTE |
| C10 | `editUser()` no protege contra editar usuarios de otro admin o superadmin | index.html | 10095+10226 | PENDIENTE |
| C11 | `backup.js` sin auth real de rol — cualquier JWT válido ejecuta backup | iporave-worker | backup.js | PENDIENTE |
| C12 | `/api/backup/list` sin autenticación de ningún tipo | iporave-worker | backup.js | PENDIENTE |
| C13 | XSS `descripcion_html` sin DOMPurify | index.html | 11461 | ✅ CORREGIDO 3fcc1b3 |
| C14 | localStorage sin prefijo por usuario → mezcla datos entre cuentas | index.html | 2271-2272 | ✅ CORREGIDO 3fcc1b3 |
| C15 | `_switchAccount()` no limpia cache → datos persisten al cambiar cuenta | index.html | 4324 | ✅ CORREGIDO 3fcc1b3 |
| C16 | `confirm()` async en iOS PWA → botón Confirmar delivery no funciona | index.html | 7337 | ✅ CORREGIDO 3fcc1b3 |
| C17 | `#mapaBackBtn` visible problem | index.html | 14881 | ✅ ELIMINADO 9146489 |

---

## 🟠 BLOQUE 2 — BUGS ALTOS (flujos principales afectados)

| ID | Bug | Archivo | Línea | Estado |
|----|-----|---------|-------|--------|
| A1 | Pedidos del cliente filtran por nombre (no ID) → 2 clientes con mismo nombre ven pedidos del otro | index.html | 5208, 6176, 2894 | PENDIENTE |
| A2 | `_fotoBase64` no se resetea entre pedidos → foto anterior puede confirmar otro pedido | index.html | 7339 | PENDIENTE |
| A3 | `_gpsToggleFromPill` y `_toggleTurno` usan `confirm()` → iOS pausa GPS accidentalmente | index.html | 14720-14724, 14828 | PENDIENTE |
| A4 | Foto entrega guardada como base64 en Supabase sin R2 → puede superar límite columna | index.html | confirmDlv | PENDIENTE |
| A5 | Estado "Reprogramado" no detiene GPS loop → consume batería delivery | index.html | 7449 | PENDIENTE |
| A6 | `loadServerConfig` falla → `mapboxgl.accessToken` vacío → crash no capturado al abrir mapa | index.html | loadServerConfig | PENDIENTE |
| A7 | Marcadores con coordenadas null/0 → TypeError rompe TODOS los marcadores si uno falla | index.html | mapa marcadores | PENDIENTE |
| A8 | `_liqDrop` calcula ganancia con `ganVend()` (lógica vendedor precio-costo-flete) → montos incorrectos para dropshipper | index.html | 8223 | PENDIENTE |
| A9 | Comisión ×qty en `_liqDrop` pero NO en `analitica_drop` → inconsistencia financiera | index.html | 9658-9659 | PENDIENTE |
| A10 | `o.precio * o.qty` sin `||0` en 19+ líneas → NaN con pedidos legacy sin precio | index.html | múltiples | PENDIENTE |
| A11 | `saveNewZona()` muestra "Zona creada" ANTES de confirmar Supabase | index.html | 10394 | PENDIENTE |
| A12 | `doDelUser()` sin verificar pedidos activos → delivery eliminado deja pedidos huérfanos | index.html | doDelUser | PENDIENTE |
| A13 | `PAGES.usuarios` no filtra por `created_by` → admin ve y puede editar usuarios de otros admins | index.html | PAGES.usuarios | PENDIENTE |
| A14 | `waSend()` con `window.open('_blank')` → saca al usuario de la app en iOS | index.html | 3230 | PENDIENTE |
| A15 | `_scannerNPLock` nunca se resetea en error → scanner inutilizable después de falla red | index.html | 10667 | PENDIENTE |
| A16 | `getPagos({})` sin filtro de rol → admin ve todos los pagos del sistema | index.html | 2807 | PENDIENTE |
| A17 | `corsHeaders()` sin request → fija CORS al primer origen → roto para otros dominios | iporave-worker | utils.js | PENDIENTE |
| A18 | `catalogo-publico.js` expone `proveedor_nombre` y `codigo_barras` sin autenticación | iporave-worker | catalogo-publico.js 56-58 | PENDIENTE |
| A19 | `.gps-pill` `height:30px` < 44px mínimo Apple HIG | index.html CSS | línea 171 | PENDIENTE |
| A20 | `mhead`/`mfoot` sticky iOS Safari roto → header/footer modal se desplazan con scroll | index.html CSS | modal | PENDIENTE |
| A21 | `ejecutarCierre()` sin verificación de rol — accesible navegando directo a `#cierre` | index.html | 9067 | PENDIENTE |
| A22 | `pagado_por` usa `CU.auth_id` (UUID) vs `pagado_a` integer → posible error tipo Supabase | index.html | 15625 | VERIFICAR |
| A23 | RLS policies Supabase posiblemente `using(true)` → cualquier auth ve todo | Supabase | consola | VERIFICAR MANUAL |
| **A24** | **`window._asistHistorial` (chat IA PAGES.asistente) nunca se limpia al logout → segundo usuario ve historial del primero** | **index.html** | **16427** | **PENDIENTE** |
| **A25** | **`ejecutarCierre()` usa `confirm()` nativo → iOS PWA ejecuta cierre sin confirmación real** | **index.html** | **9067** | **PENDIENTE** |
| **A26** | **Sin verificación de cierre duplicado del día → usuario puede cerrar jornada múltiples veces** | **index.html** | **9047-9083** | **PENDIENTE** |

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
| M11 | 16+ instancias de `confirm()` nativo (líneas 9067, 10428, 12841, 12843, 15614, etc.) | index.html | PENDIENTE |
| M12 | Sidebar footer sin `safe-area-inset-bottom` → botones bajo barra gestos iPhone | index.html 335 | PENDIENTE |
| M13 | `textarea resize:vertical` incómodo en mobile táctil | index.html 88 | PENDIENTE |
| M14 | Mensajes GPS error no diferencian iOS/Android ni dan ruta exacta Ajustes | index.html ~_gpsLoopTick | PENDIENTE |
| M15 | Botón "Llamar" (tel:) faltante en tarjetas delivery | index.html ~6619 | PENDIENTE |
| M16 | GPS mensajes sin ruta específica iOS (Ajustes→Privacidad→Localización) | index.html ~_gpsLoopTick | PENDIENTE |
| M17 | `track.html` número WA soporte ficticio | track.html | ✅ CORREGIDO f7d536c |
| M18 | Viewport meta sin `interactive-widget=resizes-visual` | index.html línea 5 | PENDIENTE |
| **M19** | **Filtro fecha boletas inconsistente con timestamps Supabase (ISO vs YYYY-MM-DD)** | **index.html** | **8616** | **PENDIENTE** |
| **M20** | **Flete de zona siempre gravado a tasa del producto en boleta SET (fiscalmente incorrecto para 5%)** | **index.html** | **8783-8784** | **PENDIENTE** |
| **M21** | **`analitica_admin`: `_getZonaO(b).precio` sin `\|\|0` → NaN en toda la analítica si zona sin precio** | **index.html** | **9859** | **PENDIENTE** |
| **M22** | **Cascada modelos IA (Groq→Gemini→DeepSeek→Anthropic) no implementada en frontend — solo 1 llamada sin fallback** | **index.html** | **16499** | **PENDIENTE** |
| **M23** | **`escHtml()` en respuestas del asistente IA → markdown/HTML se muestra como texto plano** | **index.html** | **16444, 3970** | **PENDIENTE** |
| **M24** | **ID de zona generado con `Math.max()+1` localmente → colisión en multi-sesión con upsert silencioso** | **index.html** | **10388-10399** | **PENDIENTE** |
| **M25** | **`saveNewZona` sin validación de nombre duplicado → se pueden crear 2 zonas "Villa Elisa"** | **index.html** | **10388** | **PENDIENTE** |
| **M26** | **`/api/comprobantes/delete` no tiene llamada en frontend → usuario no puede borrar comprobante subido por error** | **index.html** | **~PAGES.pagos** | **PENDIENTE** |
| **M27** | **`_resetTema()` en PAGES.config usa `confirm()` nativo → puede resetear tema sin confirmación en iOS** | **index.html** | **12841** | **PENDIENTE** |
| **M28** | **`delZona()` usa `confirm()` nativo → mismo riesgo iOS PWA** | **index.html** | **10428** | **PENDIENTE** |
| **M29** | **Segunda función `exportCSV` (línea 13379) sin BOM y sin escape de comillas → CSV malformado con nombres que tengan comillas** | **index.html** | **13379** | **PENDIENTE** |

---

## 🆕 BUGS NUEVOS DESCUBIERTOS EN AUDITORÍA 16 (2026-05-16 Opus 4.7 MAX)

### Bugs arreglados esta sesión:
| ID | Bug | Archivo | Estado |
|----|-----|---------|--------|
| NB1 | `delete-user.js` usaba columnas `from_id`/`to_id` cuando la tabla `mensajes` usa `de_id`/`para_id` → mensajes quedaban huérfanos al eliminar usuario | iporave-worker delete-user.js 116/118 | ✅ ARREGLADO |
| NB2 | `doLogout` no limpiaba `_mapaUpdateTimer`, `_gpsLoopTimer`, `_gpsBannerTimer`, `_ordersLayerInterval`, `_trackRefreshTimer` → fetchs fantasma 401 + drenaje batería | index.html doLogout | ✅ ARREGLADO |
| NB5 | `config.js` ejecutaba cleanup de demos en CADA GET de superadmin (8+ queries) → ahora una sola vez por boot del worker | iporave-worker config.js | ✅ ARREGLADO |
| NB6 | `notif-entrega.js` solo notificaba al primer admin (`.limit(1).single()`) → ahora a todos los admins + superadmin | iporave-worker notif-entrega.js | ✅ ARREGLADO |
| NB7 | `tracking.js` guardaba lat/lng como strings (variables `lat`/`lng` del body) en vez de los parseados `latN`/`lngN` | iporave-worker tracking.js 44 | ✅ ARREGLADO |
| NB9 | `sendAI()` sin flag `_aiBusy` → doble-Enter/click producía race condition con `_aiHistory.push()` duplicado y respuestas cruzadas | index.html 3865 | ✅ ARREGLADO |

### Bugs nuevos PENDIENTES (requieren más diseño/tiempo):
| ID | Bug | Archivo | Severidad |
|----|-----|---------|-----------|
| NB3 | Listeners SW + scroll bell duplicados en multi-login (no se hace `removeEventListener` al logout) | index.html ~5509 / 4698 | ALTO |
| NB4 | XSS en email de notificación de nuevo dispositivo (user.nombre/userAgent sin escapar en template) | iporave-worker login.js 201-218 | ALTO |
| NB8 | `/api/dispositivos-pendientes` no filtra por `created_by` → admin A ve solicitudes de usuarios de admin B (cross-tenant leak) | iporave-worker dispositivos-pendientes.js 30-35 | MEDIO |
| NB10 | `sw.js` stale-while-revalidate sirve index.html viejo en primera carga post-deploy → 2 recargas para ver fix | public/sw.js 111-122 | MEDIO |
| NB11 | `/api/orders/notify` no valida que `order_id` pertenezca al caller → vendedor A puede spammear delivery de vendedor B | iporave-worker orders.js 36-77 | MEDIO |
| NB12 | `get-users.js` slice silencioso a 100 → admin con >100 usuarios pierde algunos del listado sin aviso | iporave-worker get-users.js 51-62 | BAJO |

---

## 🆕 AUDITORÍA 17 — Opus 4.7 MAX 2026-05-17 (cierre sesión)

### Bugs CERRADOS en auditoría 17:
| ID | Bug | Archivo | Estado |
|----|-----|---------|--------|
| NB3 | Listeners SW + scroll bell se duplicaban en multi-login | index.html (doLogout + _notifSessionInit) | ✅ ARREGLADO |
| NB4 | XSS en email de notificación de dispositivo nuevo | iporave-worker login.js + utils.js (escapeHtmlMail) | ✅ ARREGLADO |
| NB8 | /api/dispositivos-pendientes cross-tenant leak | iporave-worker dispositivos-pendientes.js | ✅ ARREGLADO |
| NB10 | sw.js stale-while-revalidate HTML viejo post-deploy | public/sw.js (NetworkFirst con timeout 3s) | ✅ ARREGLADO |
| NB11 | /api/orders/notify no validaba ownership de order_id | iporave-worker orders.js | ✅ ARREGLADO |
| NB12 | get-users.js slice silencioso a 100 | iporave-worker get-users.js (subido a 500 + truncated flag) | ✅ ARREGLADO |
| AUD-XSS-2 | XSS en modal calificación (paraNombre raw) | index.html 12354/12356 | ✅ ARREGLADO |
| AUD-XSS-3 | XSS en modal eliminar producto (p.nombre raw) | index.html 11380 | ✅ ARREGLADO |

### Bugs NUEVOS encontrados auditoría 17 (PENDIENTES):
| ID | Bug | Archivo | Severidad |
|----|-----|---------|-----------|
| **AUD-1** | **MAPBOX_TOKEN público hardcodeado en wrangler.toml — debe ir a secret** | iporave-worker wrangler.toml línea 13 | **CRÍTICO** |
| **AUD-4** | **admin-tools.js cleanup-test borra pedidos por substring "test/prueba/demo" sin tenant scope ni OTP → riesgo data-loss masivo** | iporave-worker admin-tools.js línea 72 | **CRÍTICO** |
| **AUD-5** | **`verifyToken` cache key usa solo 32 chars del JWT → colisión + sesión zombie 5min tras bloquear usuario** | iporave-worker utils.js 59-95 | **ALTO** |
| **AUD-6** | **`calificaciones.js` permite duplicados cuando no hay pedido_id (admin/superadmin) → inflar rating** | iporave-worker calificaciones.js 101-111 | **ALTO** |
| **AUD-7** | **`comprobantes-share.js` admin de otro tenant puede enviar comprobantes por WA del destinatario** | iporave-worker comprobantes-share.js línea 28 | **ALTO** |

### Acciones manuales pendientes para usuario:
1. `wrangler secret put MAPBOX_TOKEN` y rotar token en cuenta Mapbox
2. Refactor de `admin-tools.js` cleanup para requerir OTP + filtrar por created_by
3. Revisar lógica de cache de tokens en utils.js (hash completo + invalidación al bloquear)

---

## 🟢 BLOQUE 3B — BUGS BAJOS (impacto menor / estético / técnico)

| ID | Bug | Archivo | Línea | Notas |
|----|-----|---------|-------|-------|
| **L1** | **`waBoleta()` puede mostrar "Flete zona —:" si pedido no tiene zona** | **index.html** | **9038** | **fallback b.zona.nombre** |
| **L2** | **`_boletaHTML_legacy_unused` (~175 líneas) declarada pero nunca llamada — código muerto** | **index.html** | **8816** | **eliminar** |
| **L3** | **`/api/comprobantes/delete` endpoint del worker no tiene UI correspondiente** | **index.html** | **~pagos** | **feature incompleta** |
| **L4** | **URL descarga comprobante: `WORKER_URL + downloadUrl` puede duplicar dominio si URL ya es absoluta** | **index.html** | **15814** | **verificar qué devuelve worker** |
| **L5** | **`manifest.json` línea 17: `"purpose": "any maskable"` debe ser 2 entradas separadas** | **manifest.json** | **17** | **spec W3C** |
| **L6** | **`sw.js` `CACHE_VERSION = 'v11'` hardcodeado — requiere actualización manual en cada deploy** | **sw.js** | **9** | **usuarios quedan en cache vieja** |
| **L7** | **`PAGES.config`: bloque "Alta visibilidad" con `CU.rol==='delivery'` es código muerto (delivery nunca llega a config)** | **index.html** | **12736-12744** | **eliminar** |

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
| `_TRACK_ESTADO_ICON` | 13455 | ⏳→SVG.clock, 📦→SVG.pkg, 🛵→SVG.scooter, ✅→SVG.checkCircle, ❌→SVG.xCircle, ↩️→SVG.rotateCcw |
| `stateDefs` | 5748-5755 | mismos 6 SVG |
| `stepIcons` | 7104 | ⏳→SVG.clock, 📦→SVG.pkg, 🚴→SVG.scooter, ✅→SVG.checkCircle |
| `_renderDlvCard` | 6677-6697 | 8 emojis (📦🛵✅❌⏳⚠️💬📍) |

### SVG faltantes que hay que agregar al objeto (línea 4809):
- `SVG.download` — para botones de descarga
- `SVG.smartphone` — para indicadores mobile
- `SVG.scooter` — verificar si existe (no `SVG.carRoute` que NO existe)

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
- Otros (🔄📊⭐🏆🎯🔗🔒🚫etc.) (~50 instancias)

**NOTA:** WA messages y push notification titles deben MANTENER emojis (son texto, no UI).

---

## 🔒 BLOQUE 6 — SEGURIDAD PENDIENTE

| ID | Issue | Archivo | Estado |
|----|-------|---------|--------|
| SEC1 | XSS `descripcion_html` sin DOMPurify | index.html 11461 | ✅ CORREGIDO 3fcc1b3 |
| SEC2 | `openA()` recibe HTML crudo — riesgo sistémico por concatenación dinámica | index.html 2173 | PENDIENTE (diseño) |
| SEC3 | `backup.js` sin auth de rol — cualquier JWT ejecuta backup | iporave-worker backup.js | PENDIENTE |
| SEC4 | `/api/backup/list` sin auth | iporave-worker backup.js | PENDIENTE |
| SEC5 | `corsHeaders()` fija CORS al primer origen sin leer request | iporave-worker utils.js | PENDIENTE |
| SEC6 | `catalogo-publico.js` expone `proveedor_nombre` + `codigo_barras` sin auth | iporave-worker | PENDIENTE |
| SEC7 | CSP tiene `'unsafe-inline'` — nonces pendientes | index.html | PENDIENTE |
| SEC8 | Webhook WhatsApp sin firma HMAC | iporave-worker | PENDIENTE |
| SEC9 | 2FA para acciones críticas (eliminar usuario, resetAll, cierre jornada) | index.html | PENDIENTE |
| SEC10 | RLS Supabase verificar que no sea `using(true)` | Supabase consola | VERIFICAR MANUAL |
| SEC11 | SQL injection ilike en catalog-public.js | iporave-worker | ✅ CORREGIDO dca0010 |
| **SEC12** | **`/api/monitor` (monitor.js) sin autenticación → expone estado infra (Supabase, R2, Groq) a cualquiera** | **iporave-worker monitor.js** | **PENDIENTE** |
| **SEC13** | **`/api/config` expone `mapboxToken` a usuarios anónimos sin auth + sin rate limit** | **iporave-worker config.js** | **PENDIENTE** |
| **SEC14** | **`/api/file` sin rate limit → scraping masivo de fotos de cédula posible** | **iporave-worker file.js** | **PENDIENTE** |
| **SEC15** | **`delete-user.js` no verifica pedidos activos antes de eliminar usuario** | **iporave-worker delete-user.js** | **PENDIENTE** |

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
| `_perfilCompleto()` desactivado | index.html 11988 | Eliminar línea `return{ok:true,missing:[]};` — la lógica original sigue abajo |

---

## 🚀 BLOQUE 10 — FEATURES FUTURAS (no empezar sin aprobación)

### Tienda Pública (PLAN_TIENDA_PUBLICA.md)
- Landing + catálogo `iporaveparaguay.com`
- Carrito persistente, checkout multi-paso
- Login opcional post-compra, Confirmación por WhatsApp
- Sub-tienda por vendedor/dropshipper `/v/{slug}`, Ficha producto SEO `/p/{slug}`
- Integración con pipeline de pedidos existente
- Nuevo worker endpoint `/api/tienda/checkout`

### Sistema de Suscripciones SaaS (PLAN_SUSCRIPCIONES.md)
- Tiers: Free (Gs 0) / Pro (Gs 99.000/mes) / Business / Enterprise
- Tabla `subscripciones` en Supabase + Webhook de pago

### Multi-rol / Cuentas vinculadas (PLAN_MULTI_ROL.md)
- Tabla `user_groups` + `user_group_members`
- Panel "Mi Negocio" balance consolidado

### Mapbox V6 Premium — después de GPS/filtros/tracking público/dashboard
### WhatsApp Asistente por Cliente — Twilio/Meta Business API
### PWA Offline Avanzado — extender cola a saveProducto/saveUser/savePago
### Push Notifications Completas — extender a vendedor/dropshipper/proveedor/cliente
### Document AI Processor — OCR facturas/cédulas
### API Keys Propias por Cliente — WA, Shopify, dashboard integraciones
### Rol Empresa (Sub-admin mejorado) — permisos granulares, multi-sucursal

---

## 📊 BLOQUE 11 — ITEMS ARRASTRADOS DE SESIONES ANTERIORES

| Item | Descripción | Desde |
|------|-------------|-------|
| Categorías editables | Admin pueda crear/editar/eliminar categorías del catálogo | v3 |
| Clientes recurrentes vendedor | Panel de clientes frecuentes para rol vendedor | v3 |
| Facturación B2B módulo | Módulo completo entre roles | v3 |
| Estado financiero escalable | Panel de pagos con permisos por plan suscripción | v15 |
| Gemini 2.5 Pro vía Vertex AI | Requiere service account JSON de Google Cloud | v15 |
| Mapa bugs reportados | Solo deliveries, reset auto, filtros estado, color por delivery | v15 |
| Botón Editar presentación | En modal de edición de producto | actual |
| Test GPS tracking en vivo | Verificar GPS real con delivery real | actual |
| Asistente voz/conversación | Botón micrófono en chat IA, STT→TTS | actual |
| Gemini Flash Imagen | Análisis imágenes productos | v14+ |
| Multi-rol nuclear (DB refactor) | Un usuario con múltiples roles reales en DB | v3 |
| Boletas: espaciado y calendario | Espaciado fecha + integración calendario | v15 |
| Sidebar: flechita colapsable | Collapse animado | v15 |

---

## ⚙️ BLOQUE 12 — ACCIONES MANUALES PENDIENTES (usuario debe hacer en consola)

| Acción | Dónde | Instrucción |
|--------|-------|-------------|
| Verificar RLS Supabase | consola.supabase.com → Policies | Que NO haya políticas `using(true)` en tablas pedidos/usuarios/pagos |
| `wrangler secret put MAPBOX_TOKEN` | PowerShell en iporave-worker/ | Mover token de wrangler.toml a secret |
| Crear tabla `auditoria` | Supabase SQL editor | Requerida por admin-tools cleanup |
| Configurar `env.CLEANUP_OTP` | Cloudflare dashboard → Workers → Settings | Secret para endpoint cleanup |
| Número WA soporte en track.html | Archivo track.html | ✅ CORREGIDO f7d536c — definir número real en producción |
| Telegram bot configurar | Cloudflare dashboard | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |

---

## 📌 RESUMEN EJECUTIVO — ORDEN DE PRIORIDAD RECOMENDADO

### URGENTE esta sesión (riesgo de crash en producción):
1. **C2** — Mover `const SVG` antes de línea 2520 (TDZ crash real)
2. **C1** — Mover `_notificaciones` antes de línea 2101 (TypeError crash Realtime)
3. **C3** — Mover `_shownMsgIds` antes de línea 4649
4. **C4** — Mergear `_cleanAllAppStorage` duplicada (4380+4589)
5. **C11/C12 + SEC3/SEC4** — `backup.js` agregar verifyToken + rol superadmin
6. **SEC12** — `monitor.js` agregar auth (expone infra)

### Alta prioridad (seguridad + flujos principales):
7. **A24** — `window._asistHistorial` limpiar en logout
8. **A25/A26** — `ejecutarCierre()`: confirm() → openA() + verificar duplicado del día
9. **A21** — `ejecutarCierre()` sin verificación de rol
10. **A14** — `waSend()` fix iOS (`<a>` sintético)
11. **A3** — `_gpsToggleFromPill` + `_toggleTurno` confirm() → openA()
12. **A8** — `_liqDrop` usar comisión real en vez de ganVend()
13. **A18/SEC6** — Quitar `proveedor_nombre` + `codigo_barras` de catalogo-publico.js

### Media prioridad:
14. **M21** — `_getZonaO(b).precio||0` en analítica admin
15. **M23** — `escHtml()` en respuestas IA → renderizar markdown
16. **M19/M20** — Boletas: filtro fecha + IVA flete
17. **M24/M25** — Zonas: ID colisión + nombre duplicado
18. **A10** — 19 líneas `o.precio*o.qty` sin `||0`
19. **A9** — `analitica_drop` ×qty faltante
20. **A5** — "Reprogramado" en lista stop-states GPS
21. **M11** — Reemplazar confirm() nativos restantes (>16 instancias)
22. **SEC13/SEC14** — config.js + file.js rate limits

### Próxima semana:
- Bloque 5 EMOJIS: `_TRACK_ESTADO_ICON` + `stateDefs` + `stepIcons`
- Bloque 4 MOB2/MOB3/MOB4/MOB5/MOB6 Mobile UX
- Bloque 7 Helpers `_withLoading` masivo
- Reactivar `_perfilCompleto()` (2026-05-23)

---

## 📈 ESTADÍSTICAS DE AUDITORÍA

| Categoría | Total | Corregidos | Pendientes |
|-----------|-------|-----------|------------|
| Críticos (crash) | 17 | 5 | 12 |
| Altos (flujos) | 26 | 0 | 26 |
| Medios (UX) | 29 | 1 | 28 |
| Bajos | 7 | 0 | 7 |
| Seguridad | 15 | 2 | 13 |
| **TOTAL** | **94** | **8** | **86** |

---

**Fin del documento v2. Generado 2026-05-16.**  
**Fuentes: v3→v7 RELEVOs + Oleadas 1/2/3 (10 agentes) + sesión Claude $20 (5 agentes) = 15 agentes de auditoría.**
