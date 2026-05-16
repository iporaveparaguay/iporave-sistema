# RELEVO MAESTRO — Sesión 2026-05-16 (v6 — post oleada 8 agentes)

**Fecha:** 2026-05-16  
**Sistema:** `https://iporave-sistema.vercel.app`  
**Worker:** Cloudflare Workers  
**Último commit sistema:** `759d170` (mapa topbar compacto)  
**Último commit worker:** `dca0010` (SQL injection fix — pendiente deploy)

---

## 🎯 CONTEXTO RÁPIDO

App PWA vanilla JS, SPA de ~17.800 líneas en `public/index.html`. Multi-rol (superadmin, admin, vendedor, dropshipper, delivery, proveedor, cliente). Backend Cloudflare Workers en `iporave-worker/src/`. DB Supabase Postgres con RLS.

Esta sesión se dedicó principalmente a:
1. Fixes mobile mapa (dropdown estilo, botón Volver, topbar nowrap)
2. Fix delivery descripción textarea + botones en fila
3. Escáner mejorado (Codex: cámara trasera, qrbox rectangular, fallback manual)
4. Oleada de 8 agentes de auditoría

---

## ✅ COMMITS DE ESTA SESIÓN (sistema)

| Commit | Descripción |
|--------|-------------|
| `557ba10` | feat(Codex): DOMPurify + escáner mejorado (cámara trasera, qrbox, fallback manual) |
| `c5df8a4` | fix(mobile): mapa colapso panel filtros + altura + botones horizontales |
| `a193657` | fix(delivery): descripción textarea + botones horizontales en cards |
| `a0cd6bc` | fix(mapa): botones estilo en dropdown mobile + Volver top-left |
| `759d170` | fix(mobile): topbar mapa combos compactos + nowrap confiable |

**Worker pendiente deploy:** `dca0010` — SQL injection fix en `catalog-public.js` (ilike escape)

---

## 🚨 HALLAZGOS CRÍTICOS — BLOQUEANTES (aplicar PRIMERO)

### CRIT-1 | XSS live — `descripcion_html` sin DOMPurify
**Archivo:** `index.html` línea **11461**  
**Riesgo:** Cualquier admin puede inyectar JS arbitrario visible por TODOS los usuarios.  
**DOMPurify está importado pero NUNCA se llama.**

```js
// LÍNEA 11461 — ACTUAL (inseguro):
'<div class="desc-html" style="font-size:13px;line-height:1.7">'+p.descripcion_html+'</div>'

// FIX — opción más simple: sanitizar al cargar del catálogo (DL.getProductos)
// En la función que carga productos (~líneas 2602, 2630), agregar:
descripcion_html: typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(p.descripcion_html||'') : (p.descripcion_html||''),
```

También afecta líneas **11308** y **11323** (editor HTML interno — menor riesgo).

---

### CRIT-2 | Data leak — localStorage sin prefijo por usuario (mezcla superadmin/admin)
**Archivo:** `index.html` líneas **2271-2272** (`DL._lg()` / `DL._ls()`)  
**Causa:** Claves `ipv5_users`, `ipv5_orders`, `ipv5_pagosCache` se usan para TODOS los usuarios en el mismo origen. Cuando superadmin carga datos y luego se hace switch a admin, el admin ve los datos del superadmin.

```js
// LÍNEA 2271-2272 — ACTUAL:
_lg(k){ return JSON.parse(localStorage.getItem('ipv5_'+k)||'null'); }
_ls(k,v){ localStorage.setItem('ipv5_'+k, JSON.stringify(v)); }

// FIX — prefijar por user_id:
_lg(k){ const uid=typeof CU!=='undefined'&&CU?CU.id:'anon'; return JSON.parse(localStorage.getItem('ipv5_'+uid+'_'+k)||'null'); }
_ls(k,v){ const uid=typeof CU!=='undefined'&&CU?CU.id:'anon'; localStorage.setItem('ipv5_'+uid+'_'+k, JSON.stringify(v)); }
```

---

### CRIT-3 | `_switchAccount()` no limpia cache entre cuentas
**Archivo:** `index.html` línea **4324**  
**Causa:** `location.reload()` limpia RAM pero NO el localStorage. Datos de cuenta anterior persisten.

```js
// LÍNEA 4324 — ACTUAL:
setTimeout(function(){ location.reload(); }, 400);

// FIX — agregar antes del setTimeout:
try{ _cleanAllAppStorage(); }catch(_){}
setTimeout(function(){ location.reload(); }, 400);
```

---

### CRIT-4 | `confirm()` async en iOS PWA — botón Confirmar delivery no funciona
**Archivo:** `index.html` línea **7337**  
**Causa:** En iOS Safari standalone (PWA instalada), `confirm()` dentro de `async function` es silenciado — devuelve `false` sin mostrar nada. El delivery toca Confirmar y no pasa nada.

```js
// LÍNEA 7337 — ACTUAL:
if(!confirm('¿Confirmar cambio...')){return;}

// FIX — reemplazar con inline button en showAlert:
showAlert('dlvAlert','w',
  '¿Confirmar "'+estado+'" para #'+id+'? '+
  '<button class="btn btn-success" style="margin-left:8px;min-height:44px;touch-action:manipulation" onclick="_ejecutarConfirmDlv('+id+')">✓ Sí, confirmar</button>'
);
return; // no continuar — _ejecutarConfirmDlv hace el guardado
```
Crear función `async function _ejecutarConfirmDlv(id)` con el código de guardado desde línea 7338.

---

### CRIT-5 | `#mapaBackBtn` invisible — `display:none` inline nunca se quita
**Archivo:** `index.html` línea **~14803**  
**Causa:** El botón se renderiza con `style="display:none"` y el CSS `!important` no lo puede sobreescribir porque el `inline style` tiene mayor especificidad cuando `!important` está en stylesheet externo (CSS en `<style>` tag tiene misma especificidad pero el inline estilo gana).

```js
// FIX — en PAGES.mapa, después de renderizar:
const backBtn = document.getElementById('mapaBackBtn');
if(backBtn) backBtn.style.display = window.innerWidth < 640 ? 'flex' : 'none';
```

---

### CRIT-6 | Botones GPS y estilos mapa superpuestos (mismo right:12px, bottom similar)
**Archivo:** `index.html` CSS líneas ~294, ~299  
**Fix CSS (dentro del bloque `@media(max-width:639px)`):**
```css
.mapa-estilo-toggle{ bottom:56px!important; right:12px; }
.mapa-locate-btn   { bottom:10px; right:12px; }
```

---

### CRIT-7 | Topbar 7 botones fijos + N dinámicos → 3 filas en mobile
**Archivo:** `index.html` líneas **1805-1815**  
**Causa:** `#refreshBtn`, `#tutorialToggleBtn`, `#themeToggleBtn`, `#codexNotifBell` siempre visibles.  
**Fix:** Agrupar en kebab "⋮" en mobile:
```css
@media(max-width:639px){
  #refreshBtn,#tutorialToggleBtn,#themeToggleBtn,#codexNotifBell{display:none!important;}
  #topbarKebab{display:flex!important;}
}
```
Crear `#topbarKebab` con dropdown de esas 4 acciones.

---

### CRIT-8 | Modal botón sticky — `.mfoot` no es sticky real en mobile
**Archivo:** `index.html` CSS línea **1032**  
**Causa:** `.mbox` tiene `overflow-y:auto` → el sticky del `.mfoot` no funciona (su padre scrollea en lugar del viewport).  
**Fix CSS (en `@media(max-width:640px)`):**
```css
.mbox{overflow:hidden!important;}
.mbody{overflow-y:auto!important;flex:1 1 auto!important;-webkit-overflow-scrolling:touch!important;}
.mfoot{flex-shrink:0!important;position:relative!important;}
.mhead{flex-shrink:0!important;}
```

---

## 🔴 HALLAZGOS ALTOS

### ALTO-1 | Botón "✓ Crear producto" en modal post-scan difícil de alcanzar
**Fix:** Agregar banner sticky verde al TOP del body de `openNuevoProducto()` (línea ~11025):
```js
// Insertar ANTES del bloque // MULTIMEDIA:
'<div style="position:sticky;top:-22px;z-index:9;margin:-22px -22px 16px -22px;padding:10px 16px;background:linear-gradient(135deg,#16a34a,#15803d);display:flex;align-items:center;justify-content:space-between;gap:10px;box-shadow:0 2px 8px rgba(22,163,74,.35)">'+
  '<span style="color:#fff;font-size:12px;font-weight:600;line-height:1.3">Completá los datos<br><span style="font-size:10px;font-weight:400;opacity:.85">Nombre y precio son obligatorios</span></span>'+
  '<button type="button" onclick="saveNuevoProducto()" style="background:#fff;color:#15803d;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap;min-height:42px;touch-action:manipulation">✓ Crear producto</button>'+
'</div>'+
```
(El `top:-22px` compensa el `padding:22px` del `.mbody`.)

---

### ALTO-2 | `waSend()` saca al usuario de la app en iOS
**Archivo:** `index.html` línea **3186**  
**Fix — usar `<a>` sintético:**
```js
function waSend(phone,msg){
  if(!phone)return;
  const clean=phone.toString().replace(/\D/g,'');
  const num=clean.startsWith('595')?clean:'595'+clean.replace(/^0/,'');
  const url='https://wa.me/'+num+'?text='+encodeURIComponent(msg);
  const a=document.createElement('a');
  a.href=url;a.target='_blank';a.rel='noopener noreferrer';
  a.style.display='none';document.body.appendChild(a);a.click();
  setTimeout(()=>a.remove(),200);
}
```

---

### ALTO-3 | "Mostrar filtros" mapa no tapeable (`pointer-events:none`)
**Archivo:** `index.html` CSS línea **~1429**  
El `.filtros-toggle` es muy pequeño (28px). Fix: agrandarlo en mobile.
```css
@media(max-width:768px){
  #mapaContadores.collapsed .filtros-toggle{width:100%;height:42px;border-radius:8px;font-size:13px;font-weight:600;}
  #mapaContadores:not(.collapsed) .filtros-toggle{width:28px;height:28px;border-radius:50%;}
}
```

---

### ALTO-4 | Sin botón "Llamar" en tarjetas delivery
**Archivo:** `index.html` línea **~6619-6623** en `_renderDlvCard`  
Agregar junto a los otros botones de acción:
```js
+(o.cliente_tel?'<a href="tel:'+escAttr(o.cliente_tel)+'" class="btn btn-secondary" style="min-height:44px;touch-action:manipulation">'+SVG.phone+'</a>':'')
```

---

### ALTO-5 | `getPagos({})` sin filtro de rol → admin ve todos los pagos
**Archivo:** `index.html` líneas **2807-2814** (`DL.getPagos`)  
El admin puede acceder a pagos del superadmin. Agregar filtro:
```js
if(CU && CU.rol==='admin'){
  const misUsuarios=(_usersCache||[]).filter(u=>u.created_by===CU.id).map(u=>u.id);
  if(misUsuarios.length) q=q.in('pagado_a',misUsuarios);
  else return [];
}
```

---

### ALTO-6 | `.btn-sm` con `padding:5px 11px` inline → área táctil ~26px
**Archivo:** `index.html` líneas **10924, 10928**  
Eliminar el `style="padding:5px 11px"` inline de los botones Meta Ads y Mi link en catálogo, o agregar `style="min-height:44px"`.

---

### ALTO-7 | `tbActions` pedidos admin: 7 botones desbordan topbar
**Archivo:** `index.html` líneas **6629-6636**  
Colapsar botones de exportación en dropdown kebab "Exportar ⋮".

---

### ALTO-8 | `_scannerNPLock` nunca se resetea en error de OpenFoodFacts
**Archivo:** `index.html` línea **~10573** en `_scannerNuevoProductoLeido`  
El lock queda en `true` si la API falla → scanner inutilizable sin reabrir modal.  
**Fix:** agregar `finally { _scannerNPLock = false; }` en el try-catch de `_scannerNuevoProductoLeido`.

---

## 🟡 HALLAZGOS MEDIOS

### MED-1 | WhatsApp sin validación formato 595XXXXXXXXX
En `save-user.js` (Worker) y formulario perfil `index.html` línea ~11990. No valida formato antes de guardar.

### MED-2 | `delete-user.js` no verifica pedidos activos
`iporave-worker/src/api/delete-user.js`. Eliminar usuario con pedidos en Pendiente/En Ruta deja pedidos con `vendedor_id=null`.

### MED-3 | `created_by` null bypassea filtro en `getOrders()` fallback
**Línea 2405:** `!o.created_by` hace que pedidos sin `created_by` sean visibles para cualquier admin.  
**Fix:** eliminar `!o.created_by ||` de la condición.

### MED-4 | `ejecutarCierre()` sobreescribe silenciosamente cierre del día
**Línea ~8969.** No verifica si ya existe cierre para hoy antes de hacer upsert.

### MED-5 | `pagado_por` usa `CU.auth_id` (UUID) vs `pagado_a` integer
**Línea 15625.** Inconsistencia de tipos. Verificar esquema tabla `pagos` en Supabase.

### MED-6 | `--mapa-offset:160px` corta mapa en iPhones con notch
Aumentar a `185px` + `env(safe-area-inset-bottom)`.

### MED-7 | GPS silencia errores de red (solo `console.warn`)
**Línea ~14573.** El delivery no sabe si su posición falla. Agregar `pushNotif` al primer y cada 3 fallos.

### MED-8 | `.page-mapa` CSS class nunca se asigna al DOM
**Línea 1105-1108.** El selector `.page-mapa .search-combo` nunca aplica. Fix: agregar clase a `#appScreen` al entrar/salir del mapa.

### MED-9 | Panel filtros mapa se oculta bajo topbar sticky
**Línea 551.** `.mapBar` tiene `top:0` sin contar los ~55px del topbar.  
Fix: `top:calc(55px + env(safe-area-inset-top, 0px))`.

### MED-10 | Viewport meta sin `interactive-widget`
**Línea 5.** Agregar `interactive-widget=resizes-visual` para comportamiento consistente del teclado virtual en Android/iOS.

### MED-11 | `saveNewOrder` sin validación de dirección ni stock
El pedido puede crearse sin dirección y sin verificar stock disponible.

### MED-12 | Sin badge urgencia +24h en tarjetas delivery
La función `_mapaUrgencia` existe pero no se usa en `_renderDlvCard`.

### MED-13 | `.btn` mobile `min-height:38px` (< 44px requerido)
**Líneas 1501-1504.** Cambiar a `min-height:44px`.

### MED-14 | Botones popup mapa con `min-height:36px`
**Líneas 14136-14138.** Cambiar a `min-height:44px`.

### MED-15 | RLS policies Supabase posiblemente permisivas
El SQL inicial tiene `using(true)` — verificar en consola Supabase que se hayan reemplazado por políticas reales.

### MED-16 | 16 instancias de `confirm()` nativo
Deberían reemplazarse por modal `openA`. Críticos: líneas 7337, 11278, 12843, 15614.

### MED-17 | Sidebar footer sin `safe-area-inset-bottom`
**Línea 335 `.sfooter`.** Botones "Mi Perfil" y "Cerrar sesión" ocultos bajo barra de gestos iPhone.

---

## 🟢 EMOJIS REMANENTES (~167 instancias)

### Objetos críticos a migrar primero:

**1. `_TRACK_ESTADO_ICON` (línea ~13354) — tracking público, lo ven los clientes:**
```js
// ACTUAL:
'Pendiente':'⏳','Despachado':'📦','En Ruta':'🛵','Entregado':'✅','Cancelado':'❌','Devuelto':'↩️'
// FIX:
'Pendiente':SVG.clock,'Despachado':SVG.pkg,'En Ruta':SVG.scooter,'Entregado':SVG.checkCircle,'Cancelado':SVG.xCircle,'Devuelto':SVG.rotateCcw
```

**2. `stateDefs` (líneas ~5674-5680) — dashboard superadmin:**
```js
// Reemplazar '⏳' → SVG.clock, '📦' → SVG.pkg, '🚴' → SVG.scooter, '✅' → SVG.checkCircle, '❌' → SVG.xCircle, '↩️' → SVG.rotateCcw
```

**3. `stepIcons` (línea ~7025) — stepper formulario pedido:**
```js
// Reemplazar: ⏳ → SVG.clock, 📦 → SVG.pkg, 🚴 → SVG.scooter, ✅ → SVG.checkCircle
```

### Top 10 más urgentes por visibilidad:

| Línea | Emoji | Contexto |
|-------|-------|---------|
| ~13354 | ⏳📦🛵✅❌↩️ | `_TRACK_ESTADO_ICON` — tracking clientes |
| ~7025 | ⏳📦🚴✅ | `stepIcons` stepper pedidos |
| ~5674-5680 | ⏳📦🚴✅❌↩️ | `stateDefs` dashboard superadmin |
| ~6560-6565 | 🛵 | Empty state delivery |
| ~9195-9197 | ✅⏳❌ | Stats dropshipper |
| ~15342-15349 | ✅ | Botón "Pagado" liquidación |
| ~6603 | ✅🔄 | btnLabel delivery en ruta |
| ~2453 | 📦🛵 | Push notification title |
| ~13385-13393 | 📦 | Tracking público cliente |
| ~6530 | 🔴 | Badge "PRIORIDAD" urgente |

### Conteo por emoji:
📦 (46) · ✅ (35) · 📍 (20) · 🛵 (16) · ⏳ (17) · 💰 (14) · ❌ (12) · 💬 (11) · ⚠️ (19) · 👤 (6) · 🚚 (6) · 📅 (5) · 📋 (5) · Otros (50+)

---

## 📋 TAREAS ORDENADAS POR PRIORIDAD

### BLOQUE A — Seguridad (deploy INMEDIATO)
- [ ] CRIT-1: DOMPurify activar en línea 11461 (+ 2602, 2630)
- [ ] CRIT-2+3: Fix localStorage por user_id + `_cleanAllAppStorage` en `_switchAccount`
- [ ] ALTO-5: `getPagos` filtro por rol
- [ ] MED-3: `getOrders` eliminar `!o.created_by`
- [ ] Deploy worker `dca0010` (`npx wrangler deploy` en `iporave-worker/`)

### BLOQUE B — Mobile crítico (UX bloqueante)
- [ ] CRIT-4: `confirm()` async iOS → inline button `showAlert` (línea 7337)
- [ ] CRIT-5: `#mapaBackBtn` siempre visible en mobile
- [ ] CRIT-6: Botones GPS y estilos mapa superpuestos
- [ ] CRIT-7: Topbar kebab "⋮" en mobile (ocultar 4 botones fijos)
- [ ] CRIT-8: CSS `.mbox overflow:hidden` para sticky real del `.mfoot`
- [ ] ALTO-1: Banner sticky verde en `openNuevoProducto()`
- [ ] ALTO-3: `.filtros-toggle` 100% de ancho cuando colapsado
- [ ] ALTO-4: Botón "Llamar" en tarjetas delivery
- [ ] ALTO-6: Eliminar `style="padding:5px 11px"` inline de btn-sm catálogo
- [ ] ALTO-7: Botones exportar pedidos → dropdown kebab
- [ ] MED-13: `.btn` min-height:44px en mobile

### BLOQUE C — Funcionalidad
- [ ] ALTO-2: `waSend()` usar `<a>` sintético (no `window.open`)
- [ ] ALTO-8: `_scannerNPLock` finally reset
- [ ] MED-4: `ejecutarCierre()` verificar cierre existente del día
- [ ] MED-5: Verificar tipo `pagado_por` en tabla `pagos` Supabase
- [ ] MED-7: `_gpsSendPos` notificar fallos de red al usuario
- [ ] MED-11: `saveNewOrder` validación de dirección
- [ ] MED-12: Badge urgencia +24h en delivery cards

### BLOQUE D — CSS/UX mejoras
- [ ] MED-6: `--mapa-offset:185px` + safe-area
- [ ] MED-8: Asignar `.page-mapa` a `#appScreen` al entrar al mapa
- [ ] MED-9: `.mapBar top` considerar altura topbar
- [ ] MED-10: Viewport meta `interactive-widget=resizes-visual`
- [ ] MED-14: Botones popup mapa min-height:44px
- [ ] MED-16: `confirm()` × 16 → reemplazar por `openA` (priorizar líneas 11278, 12843, 15614)
- [ ] MED-17: `.sfooter` safe-area-inset-bottom

### BLOQUE E — Emojis sweep
- [ ] `_TRACK_ESTADO_ICON` (línea ~13354) — ⏳📦🛵✅❌↩️ → SVG
- [ ] `stateDefs` (líneas ~5674-5680) — mismo reemplazo
- [ ] `stepIcons` (línea ~7025) — mismo reemplazo
- [ ] 📦 restantes (46 ocurrencias) → SVG.pkg
- [ ] ✅ restantes (35) → SVG.checkCircle
- [ ] ⚠️ (19) → SVG.alertTriangle
- [ ] 📍 (20) → SVG.mapPin
- [ ] 🛵 (16) → SVG.scooter
- [ ] ⏳ (17) → SVG.clock
- [ ] 💰 (14) → SVG.dollar
- [ ] ❌ (12) → SVG.xCircle
- [ ] Resto (~50) por lotes

---

## 🔧 ARCHIVOS CLAVE

```
iporave-sistema/public/index.html       — SPA ~17.800 líneas
iporave-sistema/.agentes/               — RELEVOs e inventarios
iporave-worker/src/api/                 — ~50 endpoints
iporave-worker/src/api/catalog-public.js — commit dca0010 pendiente deploy
```

---

## 🛡️ REGLAS OPERATIVAS

- Modo ahorro de tokens: respuestas cortas, delegar a agentes
- NO commit/deploy sin permiso explícito del usuario
- Validar con `node validate.js` antes de cada commit
- Idioma español siempre (código técnico en inglés)
- Revisar lógica manualmente antes de deployar (validate.js solo sintaxis)

---

## 🚀 PROMPT INICIAL PARA PRÓXIMA SESIÓN

```
Hola Claude. Soy iporaveparaguay@gmail.com. Continuación sesión 2026-05-16.
Leer .agentes/RELEVO_MAESTRO_2026-05-16_v6.md para contexto completo.
Estado: oleada de 8 agentes completada, RELEVO v6 guardado.
Último commit sistema: 759d170. Worker pendiente deploy: dca0010.
PRIORIDAD: Bloque A (seguridad) luego Bloque B (mobile crítico).
Modo ahorro de tokens activo.
```

---

**Fin del RELEVO v6. Generado 2026-05-16 post oleada de 8 agentes.**
