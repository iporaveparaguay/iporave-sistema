# RELEVO MAESTRO — Sesión 2026-05-16 (v2 — actualizado al cierre)

## 🎯 Estado al cierre de sesión

**Sistema (frontend):** `https://iporave-sistema.vercel.app` — último commit `ced72d5`
**Worker (backend):** Cloudflare Workers — último commit `601f36b`
**Repo sistema:** `https://github.com/iporaveparaguay/iporave-sistema` (rama `main`)
**Repo worker:** `https://github.com/iporaveparaguay/iporave-worker` (rama `master`)

---

## 📋 PENDIENTE CRÍTICO PARA EL USUARIO (acción manual)

### 1. Aplicar migración SQL en Supabase
Abrir Supabase SQL Editor y ejecutar:
- `sql/migration_facturas_b2b.sql` — crea tabla `facturas_b2b` con todas las columnas, índices y RLS.
- (Si están pendientes desde sesiones previas también: `sql/audit_logs.sql`, `sql/notificaciones.sql`.)

Hasta aplicar esto la página **Facturas B2B** seguirá mostrando error "columnas no existen". Después de aplicar la migración, todo carga normal.

### 2. Configurar secret MAPBOX_TOKEN en worker (mejor práctica)
Actualmente está en `wrangler.toml` `[vars]` (texto plano). Mover a secret:
```
wrangler secret put MAPBOX_TOKEN
```
Ya hay endpoint `/api/geocode` proxy server-side; el token deja de exponerse al cliente.

### 3. Verificar deploy del fix del asistente IA
Commit `66f9faf` fue el fix definitivo (era CSS especificidad, no JS). Después del deploy de Vercel, hacer `Ctrl+Shift+R` para recargar la app y el botón 🤖 debería abrir el chat normalmente.

---

## 🟢 LO QUE SE HIZO EN ESTA SESIÓN (orden cronológico, último → primero)

### Tutorial Onboard expandido (49 coachmarks)
- Cada página del menú principal ahora tiene 3-6 coachmarks secuenciales explicando todos los botones importantes.
- Páginas cubiertas: dashboard, orders, mapa, pagos (admin+usuario), usuarios, zonas, catálogo, liquidación (admin+mi), config, mensajes, clientes_zonas.
- Lenguaje formal B2B, persistente hasta click/Omitir/ESC, no se repite (solo primera visita por usuario).
- `Onboard.enqueue()`, `Onboard._closeCurrent()` en `nav()` corta cola al cambiar de página.
- `window.Onboard.reset()` desde consola limpia todas las keys vistas (debug).

### Bug crítico asistente IA (resuelto)
- **Causa real:** `#aiPanel{display:none !important}` global ganaba en especificidad a `.open{display:flex}` sin !important. Todos los fixes JS previos (setPointerCapture, toggleAI(force), pointerup directo) eran correctos.
- **Fix:** `.open{display:flex !important}` + reglas defensivas para `body:has(#appScreen.show)`.

### Lote masivo de seguridad y UX (oleadas 1-3)
**Seguridad worker:**
- IDOR notificaciones: SELECT previo + verificación ownership antes de UPDATE/DELETE.
- CORS: allowlist (`iporave-sistema.vercel.app`, `iporaveparaguay.com`, localhost). Vary:Origin.
- `pagado_a` agregado a `registrarPagoAUsuario` (semántica consistente).
- Mass assignment: denylist amplía con `auth_id`, `created_at`, `created_by`.
- R2 rollback: `console.error` con contexto en lugar de catch silencioso.
- `crearNotificacion`: valida `if(!userIdInt && !userIdUuid)` para evitar notifs huérfanas.

**Privacy worker:**
- Tracking GPS público: `_aproximarCoord` redondea a 1 decimal (~11km vs ~1.1km).
- Si `estado==='Entregado'`, NO expone GPS del delivery.
- Endpoint `/api/geocode` con Mapbox server-side (token nunca al cliente). Auth + rate limit 30/min.

**Seguridad sistema:**
- Supabase `createClient` con `sessionStorage` (no localStorage).
- `_cleanAllAppStorage()` en logout: borra ipv*, iporave*, AI_BTN*, onboard_v1_*, supabase.auth*, _mapaFiltros, mapa_auto.
- Token expiry tracking + `_ensureFreshToken()` enganchado en `_fetchWithTimeout` para URLs del worker.
- VAPID_PUBLIC_KEY centralizada.
- XSS sweep: 11 interpolaciones envueltas con `escHtml()`.
- `window.error` y `window.unhandledrejection` handlers globales.
- Frontend migrado a `/api/geocode` (3 llamadas) — token Mapbox ya no se expone.
- DL.saveOrder con `_fetchWithTimeout` (10s) en 4 fire-and-forget. AbortError manejado.

**UX masivo:**
- Toast: pill semi-transparente, centro inferior, blur 12px, opacity 0.85, dura 3s, slide-up, glow tintado por tipo. NO tapa más los botones.
- Badge campana: 16x16, font 9px, anillo 2px del color del topbar, >99→"99+". `overflow:visible` solo en el bell.
- Buscadores: cursiva, capitalize, opacity 0.65, sin emojis. CSS global `::placeholder`.
- Theme: emojis ☀️/🌙 reemplazados por SVG profesionales Linear/Apple. **3er modo light-soft** (descanso visual) con paleta crema. Ciclo dark→light→light-soft.
- Mapa hover gris en light/light-soft (no azul). Controles Mapbox estilizados.
- `.sidebarCollapseBtn` más fino (18px width, hover 22px) para no chocar paneles internos.
- Catálogo recuadro precio: ensanchado, lápiz quitado, X con title aclaratorio, "veo de op" expandido a "Vendedor: N · Dropshipper: N · Proveedor: N".

**Performance mapa:**
- MutationObservers `_caResetObs`, `_navObs` ahora globales con disconnect previo + en doLogout.
- `_aplicarFiltrosMapa` con debounce leading+trailing 100ms.
- `_fetchTrackData` con AbortController condicional (solo si pestaña visible).
- Popups Mapbox `getPopup()?.remove()` antes de `m.remove()` en 3 puntos.
- Blur de `.notif` 20→12px + will-change.
- Timer auto-update del mapa 60s→**300s (5min)**. Toggle "Auto-actualizar" con persistencia.
- `_mapaSkipCameraMove` flag: updates automáticos NO mueven cámara/zoom. Carga inicial sí encuadra.

**Filtros mapa (refactor central):**
- `_aplicarFiltrosMapa()` limpia ambos conjuntos al inicio. Calcula `mostrarPedidos` y `mostrarDeliveries` independientes.
- Los 4 casos (Despachado+Todos, Despachado+SoloDeliveries, etc.) ahora consistentes.
- Delivery rol no ve Entregado: filtro aplicado sobre `_mapaBase` antes del filtro de estado.

**Modales:**
- ESC cierra el modal más reciente, aiPanel, notif, dropdowns.
- Click en backdrop `.moverlay` cierra; `.mbox` preserva clicks.
- Scroll-lock body via MutationObserver.
- `role="dialog" aria-modal aria-labelledby` en mA/mB/mC.
- Focus-trap con wrap Tab/Shift+Tab.
- `aria-live="polite"` en `#notifArea`.

**A11y:**
- CSS global `.btn:disabled`, `:focus-visible` con ring ámbar.
- 7+ aria-labels en botones emoji (✕ minimizar maximizar mic WA).
- Spans con role="button" + tabindex="0".
- `rel="noopener noreferrer"` en 11 `target="_blank"`.
- Skip-link al inicio del body. Min-height 44px mobile.

**Forms:**
- `#pfWa`, `#pfTel2`, `#nTel` → type=tel inputmode=tel autocomplete=tel.
- Precios/montos: step=1 inputmode=numeric. Banco: pattern numérico.
- Buscadores: type=search spellcheck=false.
- `focus-visible` global con ring ámbar.

**Combobox delivery:**
- `<select>` reemplazado por input texto + lupa SVG + clear X + filtrado en vivo + nav teclado.
- Valida si delivery seleccionado sigue activo (auto-limpia si no).

**Tablas:**
- thead sticky, hover ámbar sutil con transition.
- `.empty-state` reutilizable, `.tbl-wrap` mobile, densidad reducida ≤640px.
- Bug duplicado `'En Ruta' || 'En Ruta'` limpiado en 3 instancias.

**Nav:**
- `PT.facturas_b2b` agregado.
- `_ensureFacturasB2BNavCfg` ahora incluye admin/superadmin.
- buildDate 2026-05-16.
- `closeSidebar` con delay 80ms para transición visual.

**Visual polish:**
- Variables `--ease-out`, `--ease-in-out`, `--ease-spring`.
- Glassmorphism `.moverlay` (blur 10 saturate 140) y `.mbox` (blur 20).
- `.ni` translateX hover. `.sc` translateY+accent glow hover.
- btn-danger/success/blue con translateY+shadow tinted en hover.

**GPS:**
- Banner consent `#gpsConsentBanner` con duración mm:ss + botón Pausar.
- Eventos `gpsActive`/`gpsInactive`.

---

## 📂 ARCHIVOS NUEVOS CREADOS EN ESTA SESIÓN

- `sql/migration_facturas_b2b.sql` (PENDIENTE aplicar manualmente)

---

## 🟡 PENDIENTES PARA LA PRÓXIMA SESIÓN

### Funcionalidad pendiente (mencionada por el usuario)
- **Botón colapsar menú vs línea amarilla**: hicimos el botón más fino — usuario debe verificar si ya no choca.
- **3 lotes seguridad worker** que faltaban: optimistic locking en order-status, WhatsApp delivery fail silencioso, calificaciones sin validar partes reales.
- Migrar el resto de `DL.*` que aún usan fetch directo a `_fetchWithTimeout` (la mayoría usa Supabase SDK directo, no aplicable).
- Banner GPS: agregar tiempo transcurrido en `#gpsText` del dashboard.

### Features pendientes documentadas en sesiones previas
- **Tienda pública** completa (`.agentes/PLAN_TIENDA_PUBLICA.md`).
- **Sistema de suscripciones** (`.agentes/PLAN_SUSCRIPCIONES.md`).
- **Multi-rol del mismo usuario** (`.agentes/PLAN_MULTI_ROL.md`).
- **WhatsApp asistente** propio por cliente.
- **Mapbox V6 premium** (después de GPS/filtros/tracking).
- **Document AI Processor** (necesita configuración manual en Google Cloud Console).

### Cosas chicas que el usuario quería pero no críticas
- "Veedor" / etiquetas redundantes en otros lugares del UI.
- Más coachmarks específicos para flujos como "agregar producto" o "asignar delivery".

---

## 🔑 CREDENCIALES Y CONFIG

- **Usuario:** iporaveparaguay@gmail.com (cuenta negocio/Shopify/admin)
- **Cuenta Claude Code:** iporave@gmail.com (esta sesión)
- **Saldo API:** $4.25 USD al 28-abr-2026 (avisar cuando queden ~$0.25)
- **Mapbox token:** está en `wrangler.toml` [vars] — mover a secret cuando se pueda

---

## 🛡️ REGLAS OPERATIVAS (recordatorio)

- **Esperar confirmación siempre** — preguntar antes de actuar (excepto en modo automático explícito).
- **No commit/deploy sin permiso** — salvo en modo autónomo otorgado.
- **Revisar manualmente antes de deploy** — `node validate.js` solo valida sintaxis.
- **Idioma español** — siempre, todas las respuestas.
- **Lenguaje formal B2B** — en tutoriales/UI texts.

---

## 📊 MÉTRICAS DE LA SESIÓN

- **Commits totales:** 15+ (sistema) + 5 (worker)
- **Auditorías ejecutadas:** ~13 (botones, modales, forms, tablas, nav, roles, a11y, animaciones, performance, seguridad, contratos API, flujos pedidos/pagos, ronda nueva).
- **Hallazgos identificados:** ~100+ (entre múltiples rondas).
- **Hallazgos fixeados:** ~80+ (la mayoría críticos y altos).
- **Líneas de código modificadas:** ~3000+ en `index.html` solamente.

---

## 🚀 PROMPT INICIAL PARA PRÓXIMA SESIÓN

> Hola Claude, soy iporaveparaguay@gmail.com. Estamos trabajando en el sistema Iporãve Connect. Leé el RELEVO `.agentes/RELEVO_MAESTRO_2026-05-16_v2.md` para todo el contexto. Antes de empezar, decime: (1) si ejecuté la migración SQL de `facturas_b2b`, (2) si el asistente IA ya abre, (3) qué pendientes querés atacar.

---

**Fin del RELEVO. Última actualización: 2026-05-16 cierre de sesión.**
