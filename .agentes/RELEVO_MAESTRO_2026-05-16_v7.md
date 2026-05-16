# RELEVO MAESTRO v7 — Iporãve Sistema
**Fecha:** 2026-05-16  
**Sesión:** Claude Sonnet 4.6 — ~80% contexto consumido  
**Próxima sesión en:** ~3 horas  
**Estado:** Commits aplicados, agentes corriendo en background  

---

## ESTADO ACTUAL DEL SISTEMA

### Commits de esta sesión (rama main)
| Hash | Descripción |
|------|-------------|
| `3fcc1b3` | fix(security+mobile): Bloque A+B — XSS escHtml, DOMPurify, localStorage por user, confirm iOS, kebab, export dropdown |
| `9146489` | fix(critical): DL.saveUser via worker API para admin, eliminar botón Volver mapa, desactivar restricciones perfil demo |

**Worker deployado:** versión `99b22fc6` (Cloudflare Workers) — incluye fix SQL injection catalog-public.js

---

## CAMBIOS APLICADOS EN ESTA SESIÓN (detalle técnico)

### 1. DL.saveUser — Fix error config delivery [CRÍTICO ✅]
**Archivo:** `public/index.html` línea ~2349  
**Problema:** `_guardarConfigDelivery(userId)` llamaba `DL.saveUser()` que hacía upsert directo a Supabase con anon key. RLS bloquea edición de otros usuarios. Resultado: "Error al guardar. Revisá la consola" al guardar configuración de pago de un delivery.  
**Fix:** Antes del path de contraseña, si hay `_sessionToken` Y no es edición propia → usar `/api/save-user` (worker) que sí tiene service key y maneja permisos correctamente.  
**Código agregado:**
```js
if(_sessionToken&&typeof CU!=='undefined'&&CU&&String(u.id)!==String(CU.id)&&!password){
  try{
    const _wr=await _fetchWithTimeout(WORKER_URL+'/api/save-user',{method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+_sessionToken},
      body:JSON.stringify(uLocal)});
    const _wj=await _wr.json();
    if(!_wr.ok){pushNotif('Error al guardar: '+(_wj.error||''),'e');return{ok:false,error:_wj.error};}
    return{ok:true};
  }catch(e){console.warn('saveUser API fallback:',e.message);}
}
```

### 2. Botón Volver del mapa — Eliminado [✅]
**Archivo:** `public/index.html` línea ~14881  
**Problema:** Botón "← Volver" en el mapa (top-left absoluto) molestaba en mobile, ocupaba espacio sobre los controles de navegación de Mapbox.  
**Fix:** Eliminada la línea que generaba el `<button id="mapaBackBtn">` y el JS que controlaba su visibilidad.

### 3. _perfilCompleto() — Restricciones desactivadas [✅]
**Archivo:** `public/index.html` línea ~11973  
**Problema:** Para demo del 2026-05-16, los usuarios nuevos que no tengan el perfil completo (foto cédula, banco, etc.) no podían navegar por el sistema.  
**Fix:** La función ahora retorna `{ok:true,missing:[]}` inmediatamente.  
**IMPORTANTE — REACTIVAR LA SEMANA DEL 2026-05-23:**
```js
function _perfilCompleto(u){
  return{ok:true,missing:[]};  // ← ELIMINAR esta línea y descomentar el resto
  // eslint-disable-next-line no-unreachable
  const rol=u?.rol||'';
  ...
```
Para reactivar: eliminar la línea `return{ok:true,missing:[]};` y el comentario eslint. La lógica original sigue ahí (no se borró).

### 4. XSS — escHtml() en analítica [✅ sesión anterior]
6 puntos en analitica_prov, analitica_drop, analitica_admin donde `p` (nombre producto/proveedor) se inyectaba en innerHTML sin escapar. Corregidos con `escHtml(p)`.

### 5. DOMPurify — descripcion_html [✅ sesión anterior]
Importado pero nunca llamado. Fix aplicado en load (~línea 2579) y en render (~línea 11461).

### 6. localStorage por usuario [✅ sesión anterior]
`DL._lg/_ls` ahora usa prefijo `ipv5_{uid}_{key}` en lugar de `ipv5_{key}`. Función `_cleanAllAppStorage()` creada para logout y switchAccount.

### 7. confirm() iOS PWA — confirmDlv [✅ sesión anterior]
Reemplazado `confirm()` (silenciado en iOS async) por botón DOM inline.

### 8. Topbar kebab mobile [✅ sesión anterior]
4 botones secundarios del topbar colapsados en dropdown ⋯ en mobile.

### 9. SQL injection worker catalog-public.js [✅ deployado]
Fix en worker, usando parámetros bind via Supabase SDK.

---

## AGENTES CORRIENDO EN BACKGROUND (al cierre de sesión)

Al cerrar esta sesión había 3 agentes en background. Sus resultados estarán disponibles pero no se capturaron en esta sesión.

### Agente A: Mobile mapa CSS + sidebar z-index
**Tarea:** Editar `public/index.html`
- Sidebar z-index: subir de 200 a 400 (para quedar sobre pines Mapbox)
- sideOverlay: subir de 199 a 399
- tbActions en mapa: cambiar de `flex-wrap:nowrap; overflow-x:auto` a `flex-wrap:wrap; overflow:visible`
- Fila 1: botones (order:1), Fila 2: combos (order:2, 50% cada uno)
- Dropdown combos: `position:fixed` para evitar clipping
- Variable CSS: `--mapa-offset:175px` (era 160px)

**CSS bloque a cambiar** (buscar "FIX mobile mapa" ~línea 1099):
```css
/* ANTES */
:root{--mapa-offset:160px;}
.page-mapa #tbActions,...{flex-wrap:nowrap!important; overflow-x:auto; ...}
.page-mapa .search-combo,...{min-width:70px!important; max-width:100px!important;}
/* DESPUÉS */
:root{--mapa-offset:175px;}
.page-mapa #tbActions,#tbActions:has(.mapa-secundarios){flex-wrap:wrap!important; overflow:visible!important; gap:4px!important; padding:4px 6px; align-items:center;}
.page-mapa #tbActions .map-btn,...,.mapa-secundarios{order:1; flex-shrink:0;}
#mapaZonaCombo,#mapaVendCombo{order:2!important; flex:1 1 calc(50% - 4px)!important; max-width:calc(50% - 4px)!important; min-width:0!important;}
#mapaZonaCombo .search-combo-list,#mapaVendCombo .search-combo-list{position:fixed!important; left:8px!important; right:8px!important; top:145px!important; width:auto!important; max-height:40vh!important; z-index:9999!important;}
```

**Sidebar z-index** (buscar en @media mobile sidebar ~línea 970-979):
```css
/* ANTES */
z-index:200;  /* sidebar */
z-index:199;  /* sideOverlay */
/* DESPUÉS */
z-index:400;
z-index:399;
```

### Agente B: track.html fixes
**Tarea:** Editar `public/track.html`
- `href="https://wa.me/595981234567"` → reemplazar número ficticio o eliminar href
- `precio(d.precio)` → `precio((d.precio||0)*(d.qty||1))` para mostrar total correcto
- Función `refresh()` → agregar contador máximo 10 reintentos antes de detener polling

### Agente C: Bugs críticos en index.html
**Tarea:** Editar `public/index.html`

**Bug 1 — zonaId vs zona** (buscar `zonaId` en PAGES.clientes_zonas y exportarClientesZonasCSV):
```js
// ANTES: o.zonaId || 'sin_zona'
// DESPUÉS: o.zona || 'sin_zona'
```
Todos los clientes aparecen "Sin zona asignada" porque el campo real del objeto pedido es `o.zona` (string), no `o.zonaId`.

**Bug 2 — crearPedidoDesdeProducto IDs incorrectos:**
```js
// ANTES: $('noProducto'), $('noProveedor'), $('noPrecio'), $('noCosto')
// DESPUÉS: $('nProd'), $('nProv'), $('nPrec'), $('nCost')
```
El autorrelleno desde catálogo → pedido está completamente roto por IDs de DOM incorrectos.

**Bug 3 — Realtime proveedor con vendedor_id:**
En `initRealtime`, filtro del proveedor usa `r.vendedor_id` en vez de `r.proveedor_id`. El proveedor nunca recibe notificaciones en tiempo real.

---

## BUGS PENDIENTES — ORDENADOS POR PRIORIDAD

### 🔴 CRÍTICOS (bloquean funcionalidad core)

| # | Bug | Archivo | Función | Estado |
|---|-----|---------|---------|--------|
| C1 | `_notificaciones` usada en Realtime ANTES de ser declarada (línea ~5346) — TypeError crash | index.html | pushNotif / initRealtime | PENDIENTE |
| C2 | `SVG.rotateCcw` usado en DL.saveOrder ANTES de que SVG esté definido (SVG ~línea 4785, DL ~línea 2000) | index.html | DL.saveOrder | PENDIENTE |
| C3 | `_shownMsgIds.add()` en canal Realtime antes de declaración en ~línea 5159 | index.html | _mostrarMensajeEntrante | PENDIENTE |
| C4 | `_cleanAllAppStorage` definida DOS VECES (~líneas 4356 y 4565) — segunda sobreescribe primera, logout inconsistente | index.html | doLogout / _switchAccount | PENDIENTE |
| C5 | crearPedidoDesdeProducto usa IDs DOM incorrectos (noProducto→nProd etc.) | index.html | crearPedidoDesdeProducto | EN AGENTE C |
| C6 | openNuevoPedido() llamada por atajo teclado 'N' pero no existe — función fantasma | index.html | atajo teclado | PENDIENTE |
| C7 | Realtime proveedor filtra por vendedor_id en vez de proveedor_id | index.html | initRealtime | EN AGENTE C |
| C8 | clientes_zonas usa o.zonaId (no existe) en vez de o.zona — todos aparecen sin zona | index.html | PAGES.clientes_zonas / exportarClientesZonasCSV | EN AGENTE C |
| C9 | resetAll() sin verificación de rol — admin podría borrar todo | index.html | resetAll | PENDIENTE |
| C10 | editUser() no protege contra editar usuarios de otro admin o superadmin | index.html | editUser | PENDIENTE |
| C11 | backup.js sin auth real de rol — cualquier JWT válido ejecuta backup | iporave-worker/src/api/backup.js | handleBackupRun | PENDIENTE |
| C12 | /api/backup/list sin autenticación de ningún tipo | iporave-worker/src/api/backup.js | handleBackupList | PENDIENTE |

### 🟠 ALTOS (flujos principales afectados)

| # | Bug | Archivo | Estado |
|---|-----|---------|--------|
| A1 | Pedidos del cliente filtran por nombre (no ID) — dos clientes mismos nombre ven pedidos del otro | index.html | PENDIENTE |
| A2 | _fotoBase64 no se resetea al abrir modal — foto de pedido anterior puede confirmar otro pedido | index.html | PENDIENTE |
| A3 | _gpsToggleFromPill usa confirm() — en iOS PWA pausa GPS accidentalmente | index.html | PENDIENTE |
| A4 | Foto entrega guardada como base64 en Supabase (sin R2) — puede superar límite y fallar silencio | index.html | PENDIENTE |
| A5 | Estado "Reprogramado" no detiene GPS loop — consume batería | index.html | PENDIENTE |
| A6 | loadServerConfig falla → mapboxgl.accessToken vacío → crash no capturado al abrir mapa | index.html | PENDIENTE |
| A7 | Marcadores coordenadas null/0 → TypeError rompe TODOS los marcadores si uno falla | index.html | PENDIENTE |
| A8 | track.html: loop polling infinito sin límite reintentos | track.html | EN AGENTE B |
| A9 | track.html: número WA soporte ficticio 595981234567 | track.html | EN AGENTE B |
| A10 | track.html: precio() muestra unitario sin multiplicar por qty | track.html | EN AGENTE B |
| A11 | _liqDrop calcula ganancia con ganVend() (lógica vendedor) — montos incorrectos | index.html | PENDIENTE |
| A12 | Comisión multiplicada por qty en _liqDrop pero no en analitica_drop — inconsistencia financiera | index.html | PENDIENTE |
| A13 | o.precio * o.qty sin ||0 en balance, tabla pedidos y CSV — NaN con pedidos legacy | index.html | PENDIENTE |
| A14 | saveNewZona() muestra "Zona creada" ANTES de confirmar Supabase | index.html | PENDIENTE |
| A15 | doDelUser() sin verificar pedidos activos — delivery eliminado deja pedidos huérfanos | index.html | PENDIENTE |
| A16 | PAGES.usuarios no filtra por created_by — admin ve y puede editar usuarios de otros admins | index.html | PENDIENTE |
| A17 | mhead/mfoot sticky iOS Safari roto — header/footer modal se desplazan con scroll | index.html CSS | EN AGENTE A |
| A18 | gps-pill height:30px — bajo el mínimo 44px Apple HIG (botón crítico delivery) | index.html CSS | PENDIENTE |
| A19 | corsHeaders() sin request fija CORS al primer origen — roto para otros dominios | iporave-worker/src/utils.js | PENDIENTE |
| A20 | catalogo-publico.js expone proveedor_nombre y codigo_barras sin autenticación | iporave-worker/src/api/catalogo-publico.js | PENDIENTE |

### 🟡 MEDIOS (10+ bugs — ver reporte completo de agentes de auditoría)
Ver sección "REPORTES DE AUDITORÍA" más abajo para lista completa.

---

## PROBLEMAS UX MOBILE REPORTADOS POR USUARIO (2026-05-16)

### 1. Buscador en mapa [EN AGENTE A]
- Combos zona/usuario en tbActions estaban cortados y no abrían dropdown
- Fix: tbActions pasa a `flex-wrap:wrap`, fila 1 botones, fila 2 combos 50%/50%
- Dropdown con `position:fixed` para evitar clipping por overflow del padre

### 2. Botón Volver en mapa [✅ ELIMINADO]
- Estaba arriba a la izquierda, molestaba y no tenía espacio

### 3. Menú hamburguesa: pines se superponen [EN AGENTE A]
- Sidebar z-index:200 < pines Mapbox
- Fix: sidebar a z-index:400, overlay a z-index:399

### 4. 3 puntos (⋯) cortados en mapa [EN AGENTE A]
- Causado por `overflow-x:auto` + `position:absolute` del dropdown
- Fix: `overflow:visible` en tbActions + dropdown z-index:9999

### 5. Config delivery error al guardar [✅ CORREGIDO commit 9146489]
- RLS Supabase bloqueaba upsert directo con anon key
- Fix: DL.saveUser usa /api/save-user (worker) cuando admin edita otro usuario

### 6. Restricciones perfil [✅ DESACTIVADAS hasta semana 2026-05-23]
- _perfilCompleto() retorna {ok:true,missing:[]} siempre
- REACTIVAR: eliminar la línea `return{ok:true,missing:[]};` en función _perfilCompleto (~línea 11973)

---

## ARQUITECTURA DEL SISTEMA (para contexto de próxima sesión)

### Frontend
- **Archivo:** `C:\Users\USUARIO\iporave-sistema\public\index.html` (~18,000 líneas)
- **SPA vanilla JS** — sin framework, todo en un solo archivo
- **Deploy:** Vercel (auto-deploy desde push a GitHub main)
- **URL prod:** iporave-sistema.vercel.app
- **Roles:** superadmin, admin, vendedor, dropshipper, delivery, proveedor, cliente

### Backend (Worker)
- **Directorio:** `C:\Users\USUARIO\iporave-worker\`
- **Deploy:** `npx wrangler deploy` desde ese directorio
- **URL prod:** iporave-api.iporaveparaguay.workers.dev
- **Auth:** JWT custom (signInWithPassword Supabase → token propio del worker)
- **DB:** Supabase Postgres con RLS

### Archivos clave
- `public/index.html` — SPA completa
- `public/track.html` — Tracking público para clientes (URL enviada por WA)
- `iporave-worker/src/api/` — Endpoints del worker
- `iporave-worker/src/utils.js` — corsHeaders(), verifyToken(), getSupaAdmin()
- `.agentes/` — Archivos de contexto para agentes (no se committean)
- `validate.js` — Validador de sintaxis del index.html (ejecutar antes de commit)

### Variables de entorno necesarias (worker)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
- `JWT_SECRET` — para firmar tokens del worker
- `MAPBOX_TOKEN` — para geocodificación en worker
- `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` — push notifications
- En `wrangler.toml` o Cloudflare dashboard

---

## REPORTES COMPLETOS DE AUDITORÍA (resumen ejecutivo de los 5 agentes)

### Agente 1 — JS Global (60 hallazgos)
Los 3 más críticos:
1. **Order de declaración**: `_notificaciones`, `_shownMsgIds`, `SVG` se usan en callbacks Realtime ANTES de ser declarados (declarados ~línea 5159-5346). Si Realtime se conecta rápido → crash.
2. **_cleanAllAppStorage doble**: definida líneas ~4356 Y ~4565. Segunda sobreescribe primera. Usar Grep `_cleanAllAppStorage` para encontrar ambas y mergear en una sola con try/catch.
3. **_perfilCompleto y viewOrder**: si no están definidas en las líneas >5900 → bloquean navegación. Verificar que existen.

### Agente 2 — Superadmin/Admin (32 hallazgos)
Los más críticos:
1. **o.zonaId vs o.zona**: bug en PAGES.clientes_zonas y exportarClientesZonasCSV (ver Agente C que lo corrige)
2. **editUser sin protección**: admin puede editar superadmin (fix pendiente C10)
3. **saveNewZona fire-and-forget**: muestra éxito antes de confirmar con Supabase

### Agente 3 — Vendedor/Dropshipper/Proveedor (35 hallazgos)
Los más críticos:
1. **crearPedidoDesdeProducto IDs incorrectos**: (ver Agente C que lo corrige)
2. **_liqDrop ganancia con ganVend()**: muestra lógica de vendedor al dropshipper — montos incorrectos
3. **Comisión × qty inconsistente**: _liqDrop multiplica, analitica_drop no → contradicción financiera

### Agente 4 — Delivery/Cliente/Mapa/Track (22 hallazgos)
Los más críticos:
1. **Cliente filtrado por nombre** (no ID) — dos clientes mismo nombre ven pedidos del otro (sin clienteId en schema)
2. **_fotoBase64 no se resetea** entre pedidos
3. **Mapa: token vacío → crash** si loadServerConfig falla

### Agente 5 — CSS Mobile + Worker Backend (25 hallazgos)
Los más críticos:
1. **backup.js sin auth**: /api/backup ejecuta sin verificar rol; /api/backup/list sin auth alguna
2. **corsHeaders() sin request**: fija CORS al primer origen — bug afecta múltiples handlers
3. **runBackup sin límite filas**: puede crashear worker por OOM con tablas grandes

---

## PENDIENTES DEL USUARIO PARA PRÓXIMA SESIÓN

### Inmediato (esta semana)
1. [ ] Verificar que agentes A/B/C completaron sus cambios correctamente
2. [ ] Commit + push + deploy después de verificar agentes
3. [ ] Probar config delivery: abrir modal, llenar campos, guardar → debe funcionar ahora
4. [ ] Probar mapa mobile: combos zona/usuario deben ser visibles y abrir dropdown
5. [ ] Definir número real de WA para soporte en track.html
6. [ ] Discutir modelo de comisión exacto del dropshipper (afecta _liqDrop bug A11/A12)

### Semana del 2026-05-23 (cobros comienzan)
1. [ ] Reactivar _perfilCompleto() — eliminar `return{ok:true,missing:[]};` en línea ~11973
2. [ ] Definir estructura de cobros por plataforma (proyecto)
3. [ ] Rol empresa (sub-admin mejorado) — diseñar

### Largo plazo
- Mapbox V6 premium (después de estabilizar actual)
- API keys propias por cliente (WA, Shopify)
- Auto-registro usuarios externos (tienda pública lista)
- Módulo B2B entre roles (facturación largo plazo)

---

## CÓMO CONTINUAR EN PRÓXIMA SESIÓN

1. **Leer este archivo** para contexto completo
2. **Verificar estado de agentes** — buscar si hay commits nuevos desde `9146489`
3. **Revisar index.html** — los agentes A y C editan el mismo archivo en paralelo, verificar que no hayan conflictos
4. **Ejecutar validate.js** antes de cualquier deploy
5. **Hacer git push** cuando todo esté verificado → Vercel auto-deploya

### Prompt inicial recomendado para próxima sesión:
```
Hola Claude. Soy iporaveparaguay@gmail.com. Sesión 2026-05-16 continuación.
Leer .agentes/RELEVO_MAESTRO_2026-05-16_v7.md para contexto completo.
Estado: hay agentes que corrían en background (CSS mapa mobile, track.html, bugs críticos).
Verificar si sus cambios se aplicaron, hacer commit+push si todo OK.
Prioridad: verificar + deploy. Luego continuar con bugs pendientes.
```

---

## NOTAS TÉCNICAS IMPORTANTES

### validate.js — usar siempre antes de commit
```bash
cd C:\Users\USUARIO\iporave-sistema && node validate.js
```
Detecta: etiquetas `</script>` sin escapar dentro de strings JS, funciones críticas faltantes.

### Deploy frontend (Vercel)
```bash
git add public/index.html
git commit -m "..."
git push origin main   # Vercel auto-deploya
```

### Deploy worker (Cloudflare)
```bash
# En PowerShell, navegar a:
Set-Location "C:\Users\USUARIO\iporave-worker"
npx wrangler deploy
```

### Caché de preview (desarrollo local)
El index.html está visible en el panel de preview de Claude Code durante la sesión.

---
*Documento generado al cierre de sesión 2026-05-16. Siguiente sesión en ~3 horas.*
