# RELEVO MAESTRO — Sesión 2026-05-16 (v4 — checkpoint ~80% tokens usado)

## 🔑 DATOS DE CONTEXTO INMEDIATO

**Sistema frontend:** `https://iporave-sistema.vercel.app`  
**Último commit sistema:** `91e25da` (ya pusheado a Vercel)  
**Worker backend:** Cloudflare Workers — último deploy `7c0b14c` (hay un commit local `dca0010` SIN deployar aún — ver PENDIENTES)  
**Archivo principal:** `C:\Users\USUARIO\iporave-sistema\public\index.html` (~17.578 líneas)  
**Modelo activo:** Claude Sonnet 4.6 (modo ahorro de tokens)  
**Fecha sesión:** 2026-05-16  
**Usuario:** iporaveparaguay@gmail.com

---

## 🛠️ STACK TÉCNICO COMPLETO

| Capa | Tecnología | Notas |
|------|-----------|-------|
| Frontend | SPA vanilla JS/HTML, ~17.578 líneas en 1 archivo | `index.html`, sin framework |
| Backend | Cloudflare Workers, ~50 endpoints | `iporave-worker/src/api/*.js` |
| DB | Supabase PostgreSQL con RLS | Auth via `signInWithPassword`, auth_id UUID |
| Storage | Cloudflare R2 | Fotos, videos de productos |
| Hosting | Vercel (auto-deploy desde GitHub main) | |
| IA cascada | Groq → Gemini Flash → Gemini Flash Lite → DeepSeek R1 → Anthropic Haiku | |
| Mapa | Mapbox GL JS | Filtros auto-cargan al entrar |
| Escáner | html5-qrcode v2.3.8 (CDN unpkg) | Ya configurado con formatos EAN/UPC |
| Push | VAPID + aes128gcm | Worker commit `9154f46d` |

**Patrones críticos:**
- `DL.*` = DataLayer (Supabase). Ej: `DL.getCatalogo()`, `DL.saveProducto(p)`
- `CU` = objeto usuario actual (global). `CU.rol`, `CU.id`, `CU.auth_id` (UUID)
- `openA(title, body, footer, size)` = modal único. title usa `innerHTML` (soporta SVG). NO usar textContent.
- `closeA()` = cierra modal
- `PAGES.X = function(q)` = páginas de la SPA
- `SVG.X` = iconos SVG (objeto global con 50+ íconos)
- `escHtml(str)` = escape HTML. `escAttr(str)` = escape para atributos HTML
- `gv('id')` = `document.getElementById('id').value`
- `$('id')` = `document.getElementById('id')`
- `getVisibleOrders()` = filtra pedidos por rol automáticamente
- `pushNotif(msg, type)` = notificación toast. type: 'i' info, 'e' error, 's' success
- `isAdminLike(rol)` = true si rol es admin o superadmin
- `node validate.js` en `/iporave-sistema` antes de CADA commit (verifica sintaxis y que no haya `</script>` sin escapar)
- CRÍTICO: dentro de strings JS en HTML, nunca escribir `</script>` — siempre `'<scr'+'ipt>'`

---

## ✅ LO QUE SE HIZO EN ESTA SESIÓN (commits `9fb1108` → `91e25da`)

### Commit `9fb1108` — 8 fixes urgentes pre-entrega + Configuración Delivery
- Fix: SVG en títulos de `openA()` — cambio de `textContent` a `innerHTML` (línea ~2053)
- Fix: Padding izquierdo en filtros "Desde/Hasta" del panel de pagos
- Fix: Botón "Pagado" — enviaba `CU.id` (integer) en `pagado_por`, corregido a `CU.auth_id` (UUID)
- Fix: Botones del mapa en mobile (overflow hidden los cortaba)
- NEW: `PAGES.configuracion_delivery` — página completa con 4 métodos de pago configurable:
  - `cupo` (crédito cliente), `porPedido` (por delivery), `fija` (sueldo fijo), `externa` (Fixy/etc)
  - Guarda en columnas `pago_metodo`, `pago_config`, `pago_notas` (migración ya aplicada en Supabase)
  - Modal por delivery, campos dinámicos por método

### Commit `711a245` — macaquito + layout nuevo producto + labels filtros
- Asistente IA rediseñado como robot/macaquito animado con círculos SVG
- Layout "Nuevo producto": título centrado arriba del cuadro negro, labels debajo de inputs
- Labels de filtros de fecha con borde izquierdo naranja (estilo tarjeta)
- `_requireUserAuth()`: unlock por sessionStorage `iporave_userauth_unlock` válido 15 min

### Commit `261a224` — doble click cliente + mobile grids
- Doble click en pedido para cliente ya no abre modal doble
- Grids mobile más compactos

### Commit `e583e57` — tutorial toggle button en topbar
- Botón toggle tutorial al lado del refresh en topbar
- `localStorage.iporave_tutorial_enabled`

### Commit `5604804` — data leak proveedor + mobile masivo
- Fix: proveedor ya NO ve todos los proveedores en liquidación (usa `getVisibleOrders()` que aísla por rol)
- Mobile: `.btn-sm` touch targets 44px, `.topbar-icon-btn` 40px

### Commit `65e3fe7` — EMPRESA actualizada
- `EMPRESA` (línea ~1789): `{nombre:'Distribuidora Iporãve', ruc:'80167603-7', timbrado:'18662937', ...}`

### Commit `d9ebe94` — unlock 15 min
- `_requireUserAuth()` en gestión de usuarios: TTL 5min → 15min en sessionStorage

### Commit `499495c` — boleta IVA rediseño
- `_boletaHTML()`: formato oficial FACTURA ELECTRÓNICA SET Paraguay
- Encabezado doble: datos empresa izq + datos timbre der
- Tabla 8 columnas con EXENTAS / 5% / 10%
- Liquidación IVA por línea
- @media print incluido

### Commit `7b48cee` — emojis → SVG
- `SVG.lock` nuevo (candado moderno)
- `SVG.carRoute` nuevo (auto en carretera, reemplaza 🚴 "En Ruta")
- `SVG.scooter` rediseñado como camión delivery
- Pin delivery en mapa: V3 motoqueiro con casco
- Meta Ads: `SVG.megaphone`

### Commit `89c48e0` — visual improvements
- Empty state `renderTable()`: caja isométrica SVG (reemplaza 📦)
- `.btnPagado`: pill verde neón gradient
- `.toggleBtn`: pill teal neón cuando ON

### Commit `07652a6` — fix masivo multi-agente
- Fix: `_liqDrop()` usa `o.comision*o.qty` en lugar de ganancia bruta
- Fix: `getVisibleOrders()` para cliente: usa `clienteId` O nombre case-insensitive
- Mobile: touch targets `.btn-sm` 44px, `.topbar-icon-btn` 40px
- Nav proveedor: eliminado "Nuevo pedido" (proveedor no crea pedidos)
- `bE()` + `_estadoEmoji` + `_EI_CL`: "En Ruta" → `SVG.carRoute`
- `editPresentacion`: `escHtml(p.nombre)` y `escAttr(pr.nombre)` (fix XSS)
- `saveEditProducto`: muestra alert si nombre vacío

### Commit `91e25da` — escáner de códigos de barras REESCRITO
- `_scannerFormats()`: helper que devuelve array con EAN-13, EAN-8, UPC-A/E, CODE-128/39/93, ITF, DATA_MATRIX
- `_scanBeep()`: beep de confirmación via Web Audio API (sin librerías)
- `abrirScannerCatalogo()`: qrbox rectangular `{width:280,height:120}`, fps:15, formatos explícitos, trim comparison, link "Crear producto con este código" (→ `_scanCrearConCodigo`)
- `_scanCrearConCodigo(codigo)`: cierra scanner y abre form nuevo producto con código pre-llenado
- `_scanParaNuevoProducto()`: qrbox rectangular, fps:15, formatos explícitos, lookup Open Food Facts API, re-abre form con nombre+código pre-llenados
- **Bug root cause**: `qrbox:250` (cuadrado) + sin `formatsToSupport` → barcodes 1D casi no se detectaban

---

## 🔴 PENDIENTES CRÍTICOS (hacer en la próxima sesión, en orden de prioridad)

### PRIORIDAD 1 — Deploy worker (aún no deployado)
**Archivo:** `C:\Users\USUARIO\iporave-worker\src\api\catalog-public.js`  
**Commit local:** `dca0010` (commit exists locally but NOT pushed to Cloudflare)  
**Qué hace:** Fix SQL injection en búsqueda por nombre — escapa wildcards `%`, `_`, `\` en el parámetro `buscar` del endpoint público del catálogo  
**Cómo deployar:** En directorio `iporave-worker`, ejecutar `npx wrangler deploy`  
**IMPORTANTE:** El usuario debe confirmar antes de deployar. Mostrar resumen y preguntar.

### PRIORIDAD 2 — Fix emojis remanentes (sweep masivo pendiente)
El usuario dijo: "hay muchísimos emojis todavía que no se han cambiado"  
**Ya identificados en sesión anterior:** 32 emojis con 257+ ocurrencias en index.html  
Los más críticos:
- `📦` → `SVG.pkg` o box isométrico SVG (62 ocurrencias)
- `✅` → `SVG.checkCircle` (37 ocurrencias)  
- `⚠️` → `SVG.alertTriangle` (18 ocurrencias)
- `🔔` → `SVG.bell` (ya existe en SVG)
- `💬` → `SVG.chat` (chat asistente — usuario lo mencionó en esta sesión, el emoji del chat está obsoleto)
- `📊` → `SVG.chart`
- `👤` → `SVG.user`
- `🗺` → `SVG.map`
- `🛒` → `SVG.shoppingCart`

**Cómo hacerlo bien:** Usar agentes Explore para encontrar cada emoji, luego Edit con replace_all si el SVG equivalente ya existe en el objeto `SVG`. Los SVG están definidos alrededor de la línea 650-900 del archivo.

**Para enviar a un agente:** Decirle exactamente qué emoji reemplazar → con qué SVG.X → en qué contextos (badges, botones, headers, cards). Darle los números de línea aproximados para que sea eficiente.

### PRIORIDAD 3 — Fix botón "Editar presentación" en modal edición producto
**Función:** `editProducto(id)` (línea ~10916)  
**Problema:** En el modal de edición de producto, el botón "Editar presentación" probablemente no aparece o no funciona bien.  
**Lo que debería hacer:** Abrir sub-modal con form de edición de presentaciones de ese producto.  
**Funciones relacionadas:** `editPresentacion(prodId, idx)`, `savePresentacion(prodId, idx)`, `addPresentacion(prodId)`, `deletePresentacion(prodId, idx)`

### PRIORIDAD 4 — Fixes delivery (de auditoría completada, no aplicados)
Hallazgos del agente de delivery que NO fueron aplicados:
1. **Badge urgencia >24h**: Pedidos sin movimiento por más de 24h deberían mostrar badge visual en las tarjetas del delivery
2. **GPS throttle de batería**: El GPS loop debería empezar en 30s si no hay pedido activo, bajar a 5s con pedido activo
3. **Dashboard "Recaudado HOY"**: El delivery ve total acumulado en vez de solo hoy — confuso
4. **Auto-refresh lista delivery**: La lista de pedidos no se actualiza automáticamente (debería cada 60s)
5. **Estado "Bloqueado"**: Si un delivery tiene estado "bloqueado", debe mostrarse claramente en su panel (no solo en admin)
6. **Eliminar confirm() duplicado**: En iOS, el confirm() del sistema + el confirm() de la app pueden generar doble diálogo al cambiar estado

### PRIORIDAD 5 — Fixes vendedor (de auditoría, no aplicados)
1. **XSS en tablas analítica**: Las celdas de las tablas de analytics del vendedor usan innerHTML sin escapar
2. **Ocultar asterisco costo proveedor**: El campo `*Costo proveedor` se muestra a roles que no deberían verlo
3. **Validación teléfono**: El campo de teléfono de cliente no valida formato paraguayo (+595)
4. **Mobile cards**: En mobile, las tarjetas de pedidos del vendedor cortan el monto y la fecha

### PRIORIDAD 6 — Fixes dropshipper (de auditoría, no aplicados)
1. **FIX 4 (XSS)**: En "top productos", si el nombre tiene caracteres especiales, se puede inyectar HTML
2. **FIX 5 (paginador)**: El paginador de la lista de dropshipper puede romperse si hay >100 pedidos
3. **FIX 6 (ocultar select)**: El select de dropshipper en el form de pedido debería ocultarse si hay solo 1 opción

### PRIORIDAD 7 — Fixes catálogo (de auditoría, no aplicados)
1. **FIX 1 CRÍTICO — XSS descripcion_html**: En la función que renderiza la descripción del producto (visor público y admin), el campo `descripcion_html` se inserta directo con innerHTML sin sanitizar. RIESGO: si alguien carga una descripción con JS malicioso, se ejecuta.
   - **Cómo fix**: Usar DOMPurify o sanitizar antes de insertar: `div.innerHTML = DOMPurify.sanitize(prod.descripcion_html)`
   - DOMPurify CDN: `https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.6/purify.min.js`
   - Buscar en index.html: `descripcion_html` con innerHTML
2. **FIX 3+4 (picker XSS)**: El color picker del catálogo tiene XSS potential
3. **FIX 5 (presentaciones validation)**: No valida precio ni nombre mínimo al guardar presentación

### PRIORIDAD 8 — Fixes admin/subadmin (de auditoría, no aplicados)
1. **FIX 2 — Email regex**: La validación de email en "Crear usuario" acepta emails inválidos. Regex actual demasiado permisivo.
2. **FIX 3 — WhatsApp 595**: No valida que el teléfono WhatsApp tenga formato paraguayo +595XXXXXXXXX
3. **FIX 4-6 — Zona validations + modal**: Crear/editar zona no valida que el nombre no esté vacío. `delZona()` usa `confirm()` del browser — en iOS puede dar doble diálogo. Cambiar a modal customizado.
4. **FIX 7 — Bloquear delete usuario con pedidos**: Si un usuario tiene pedidos abiertos, borrar su cuenta rompe la FK. Debe verificar antes de borrar.
5. **FIX 9 — Panel datos empresa en Config**: Los datos de EMPRESA (RUC, timbrado, etc.) deberían ser editables desde la Config del admin, no hardcodeados en el código.
6. **FIX 10 — Columna acciones**: En la tabla de usuarios, la columna "Acciones" a veces queda fuera del viewport en mobile.

### PRIORIDAD 9 — PWA fixes
1. **Push subscribe broken**: El auto-subscribe al abrir la app usa `localStorage.getItem('token')` pero el sistema usa `sessionStorage.getItem('iporave_token')`. No se auto-suscribe. Buscar en index.html donde se llama `subscribePush()` o similar.
2. **VAPID key comparison**: Verificar que la clave VAPID en el service worker coincide con la del worker
3. **pendingQueue dedup**: Si el usuario offline crea el mismo pedido dos veces y luego vuelve online, se duplica

### PRIORIDAD 10 — track.html GPS privacy
**Archivo:** `C:\Users\USUARIO\iporave-sistema\public\track.html`  
**Problema:** Las coordenadas GPS exactas del delivery se muestran a cualquiera con el share_token. Privacy issue.  
**Fix identificado:**
- Redondear coords a 1 decimal (±5km de precisión) en la URL pública
- Si `estado === 'Entregado'`, ocultar el mapa completamente (no tiene sentido mostrar la ubicación después de entrega)

---

## 🟡 PENDIENTES MENORES / POST-DEADLINE

- **Emoji chat asistente obsoleto**: El icono del chat (💬 flotante) todavía usa emoji viejo. Cambiar a `SVG.chat` o similar. No es urgente.
- **Categorías editables**: Ahora las categorías de producto son hardcodeadas. Hacer editables desde Admin Config.
- **Test GPS tracking en vivo**: Hacer prueba real: delivery actualiza GPS → admin ve en mapa → cliente ve en track.html
- **Webhook WhatsApp firma HMAC**: El endpoint de Green API no valida firma HMAC → cualquiera puede mandar mensajes falsos
- **CSP nonces**: Eliminar `'unsafe-inline'` del Content Security Policy usando nonces generados por el worker
- **2FA para acciones críticas**: Confirmación extra para borrar usuario, borrar producto, cambiar rol
- **Tienda Pública con carrito**: Ver `PLAN_TIENDA_PUBLICA.md` en la carpeta del proyecto
- **Configuración técnica avanzada por usuario**: Preferencias por sesión (chat config, etc.)

---

## 📋 AUDITORÍAS COMPLETADAS (resultados disponibles pero NO aplicados)

Estos agentes terminaron en la sesión, produciendo listas de fixes concretos que quedaron pendientes de aplicar:

| Agente | Estado | Fixes principales listos |
|--------|--------|--------------------------|
| Delivery audit | ✅ completo | 8 fixes (badge urgencia, GPS throttle, dashboard HOY, auto-refresh 60s) |
| Vendedor audit | ✅ completo | XSS analytics, ocultar costo proveedor, validación teléfono |
| Dropshipper audit | ✅ completo | FIX 4 XSS, FIX 5 paginador, FIX 6 ocultar select |
| Catálogo audit | ✅ completo | FIX 1 CRÍTICO descripcion_html XSS, FIX 3+4+5 |
| Admin/subadmin audit | ✅ completo | FIX 2 email, FIX 3 WhatsApp, FIX 4-6 zona, FIX 7 delete check, FIX 9 empresa panel |
| PWA audit | ✅ completo | Push subscribe, VAPID, pendingQueue |
| GPS/track audit | ✅ completo | Privacy coords, ocultar mapa post-entrega |
| Worker security | ✅ completo | OTP brute force, Maps API key, Green API HMAC |

**Para aplicar estos fixes:** Necesitás leer el output de cada agente (o leer el archivo index.html en el área relevante) y hacer los edits. Usar agentes de escritura de código para aplicar lote por lote. Siempre `node validate.js` antes de commit.

---

## ⚠️ REGLAS OPERATIVAS (NUNCA olvidar)

1. **`node validate.js` SIEMPRE antes de `git commit`** — en `iporave-sistema/`
2. **`</script>` DENTRO de strings JS** → siempre dividir: `'<scr'+'ipt>'`
3. **`openA()` usa innerHTML en el título** — no textContent (para que SVG funcione)
4. **Deploy worker** → requiere confirmación explícita del usuario + `npx wrangler deploy` en `iporave-worker/`
5. **No commit sin `node validate.js` pasado** — si falla, arreglar primero
6. **Respuestas cortas** — modo ahorro de tokens activo
7. **Español siempre** — en código comentarios es opcional, pero en respuestas al usuario siempre español
8. **No modificar auth/roles/secrets sin explicación previa**
9. **Mostrar resumen antes de deploy** y esperar confirmación
10. **Formulario nuevo producto**: campos son `npNom` (nombre), `npCat` (categoría), `npCodigo` (código barras), `npStock`, `npPrecioComp` — NO `npNombre` ni `npCategoria`

---

## 🔧 PATRONES DE CÓDIGO IMPORTANTES PARA CADA ROL

### Cómo funciona la navegación por rol:
```js
// En el objeto PAGES, cada entrada es una función:
PAGES.pedidos = function() { ... }
PAGES.catalogo = function(q='') { ... }
PAGES.configuracion_delivery = function() { ... }

// La navegación respeta el rol via:
const nav = NAV_ROLES[CU.rol] || [];
// NAV_ROLES está definido con arrays de {id, label, icon} por rol
```

### Cómo funciona el modal único:
```js
openA('Título con SVG.x aquí', '<div>body HTML</div>', '<button>footer</button>', 'lg');
// size puede ser: '' (default), 'lg', 'xl', 'sm'
closeA(); // cierra
```

### Cómo funciona el escáner AHORA (después del fix de esta sesión):
```js
// Catalog scanner: abrirScannerCatalogo()
// - Abre modal con scanner
// - Escanea → busca en _catalogoCache por codigo_barras (trim)
// - Si no encuentra → muestra link "Crear producto con este código" → llama _scanCrearConCodigo(codigo)
// - _scanCrearConCodigo: cierra scanner, setTimeout → openNuevoProducto(), luego llena npCodigo

// New product scanner: _scanParaNuevoProducto()  
// - Abre modal con scanner
// - Escanea → intenta lookup Open Food Facts (world.openfoodfacts.org/api/v0/product/{code}.json)
// - Cierra modal → setTimeout → openNuevoProducto() → llena npCodigo y npNom con datos encontrados
```

### Cómo funciona la seguridad de sesión (unlock 15 min):
```js
// En funciones críticas de gestión de usuarios:
if(!_requireUserAuth()) return;
// _requireUserAuth() verifica sessionStorage.getItem('iporave_userauth_unlock')
// Si no hay, abre modal para pedir contraseña
// Si se ingresa bien, guarda en sessionStorage con TTL 15 min
```

---

## 📊 CONTEXTO DE NEGOCIO

- **Empresa:** Distribuidora Iporãve, RUC 80167603-7, Timbrado: 18662937
- **Roles del sistema:** `superadmin` > `admin` > `subadmin` > `vendedor` > `dropshipper` > `proveedor` > `delivery` > `cliente`
- **Supabase:** tablas principales: `usuarios`, `pedidos`, `catalogo`, `catalog_shares`, `pagos`, `pagos_comprobantes`, `zonas`, `push_subscriptions`, `jornadas`, `facturas_b2b`
- **Columnas delivery:** `pago_metodo` (TEXT, default 'cupo'), `pago_config` (JSONB), `pago_notas` (TEXT) — ya migradas
- **Columna eliminación lógica:** `deleted_at` en `push_subscriptions` — ya migrada
- **Auth:** Supabase nativo `signInWithPassword`. `auth_id` (UUID) es el campo de enlace entre `auth.users` y `public.usuarios`

---

## 🆕 COSAS QUE EL USUARIO MENCIONÓ EN ESTA SESIÓN (recordar)

1. **Emoji del asistente/chat**: el ícono flotante del chat IA usa un emoji viejo — cambiar a SVG moderno (no urgente)
2. **El escáner no andaba**: ya fixeado en commit `91e25da` — si el usuario reporta que sigue raro, verificar que `Html5QrcodeSupportedFormats` esté disponible como global (depende del CDN cargado)
3. **Cuando mandes agentes a hacer botones/emojis**: el usuario pidió EXPLÍCITAMENTE dar a los agentes toda la info necesaria (qué emoji, qué SVG, en qué función, en qué línea aproximada) — no mandar agentes vagos

---

## 🚀 PROMPT INICIAL PARA PRÓXIMA SESIÓN

> Hola Claude. Soy iporaveparaguay@gmail.com. Continuación del 16-may-2026 (Sonnet 4.6).
> Leer `.agentes/RELEVO_MAESTRO_2026-05-16_v4.md` para contexto completo.
> Último commit sistema: `91e25da`. Worker pendiente de deploy: `dca0010`.
> Prioridades: (1) Deploy worker catalog-public.js, (2) Sweep emojis remanentes con agentes detallados, (3) Fix XSS descripcion_html catálogo (CRÍTICO seguridad), (4) Fixes delivery dashboard y GPS throttle.
> Modo ahorro de tokens activo.

---

**Fin del RELEVO v4. Última actualización: 2026-05-16, ~80% tokens usados.**
