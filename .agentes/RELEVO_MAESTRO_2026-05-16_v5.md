# RELEVO MAESTRO — 2026-05-16 v5 (SESIÓN EXTENDIDA — ~92% tokens)

> Para Codex, Antigravity, o cualquier Claude que retome. Leer TODO antes de tocar código.

---

## 🔑 ESTADO INMEDIATO

| Componente | Último commit | Estado |
|-----------|--------------|--------|
| Frontend (Vercel) | `759d170` | ✅ Live |
| Worker (Cloudflare) | `7c0b14c` | ✅ Live — hay commit LOCAL `dca0010` SIN deployar |
| DB (Supabase) | — | ✅ Migraciones aplicadas |

**Archivo principal:** `C:\Users\USUARIO\iporave-sistema\public\index.html` (~17.800 líneas)  
**Worker:** `C:\Users\USUARIO\iporave-worker\src\`  
**Usuario:** iporaveparaguay@gmail.com  
**Modelo:** Claude Sonnet 4.6  

---

## ✅ COMMITS DE ESTA SESIÓN (orden cronológico)

| Commit | Descripción |
|--------|-------------|
| `91e25da` | Escáner: formatos EAN/UPC/CODE128, qrbox rectangular, beep, lookup Open Food Facts |
| `c6deebd` | Tabla usuarios: badges por rol (color+borde+dot), avatar iniciales, nombre+username apilados |
| `b3cbcba` | RELEVO v4 (checkpoint 80%) |
| `557ba10` | Codex: DOMPurify CDN + escáner mejorado (cámara trasera auto, qrbox dinámico, fallback manual) |
| `c5df8a4` | Mapa mobile: panel filtros colapsado por defecto, mapa más alto (160px offset), botones nowrap |
| `a193657` | Delivery: campo descripción textarea expandible, botones tarjetas en fila horizontal |
| `a0cd6bc` | Mapa: botones estilo → dropdown mobile (toggle engranaje), botón Volver movido a top-left |
| `759d170` | Mapa: combos zona/vendedor compactos en mobile, topbar nowrap con `!important` |

---

## 🚨 PENDIENTES CRÍTICOS — CON CÓDIGO EXACTO

### CRÍTICO 1 — XSS: DOMPurify importado pero NUNCA usado
**Problema:** `DOMPurify` está cargado en línea ~27 pero no se llama en ningún lado. `descripcion_html` se inserta crudo.

**3 instancias a corregir:**

**Instancia A** (línea ~11461 — modal vista producto):
```js
// ANTES:
'<div class="desc-html">'+p.descripcion_html+'</div>'
// DESPUÉS:
'<div class="desc-html">'+(typeof DOMPurify!=='undefined'?DOMPurify.sanitize(p.descripcion_html||''):escHtml(p.descripcion_html||''))+'</div>'
```

**Instancia B** (función `_setRichContent` línea ~11308):
```js
// ANTES:
v.innerHTML = content || ''
// DESPUÉS:
v.innerHTML = typeof DOMPurify!=='undefined' ? DOMPurify.sanitize(content||'') : (content||'')
```

**Instancia C** (función `_toggleHTMLMode` línea ~11323):
```js
// ANTES:
v.innerHTML = h.value
// DESPUÉS:
v.innerHTML = typeof DOMPurify!=='undefined' ? DOMPurify.sanitize(h.value||'') : (h.value||'')
```

---

### CRÍTICO 2 — GPS sin persistencia: posiciones se pierden si el Worker falla
**Función:** `_gpsSendPos` — línea ~14573  
**Problema:** `catch(e){console.warn}` silencioso. Si falla la red, la posición se pierde.

**Fix (agregar cola local):**
```js
async function _gpsSendPos(lat,lng){
  const body=JSON.stringify({lat,lng});
  try{
    const r=await fetch(WORKER_URL+'/api/tracking',{
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+(_sessionToken||'')},
      body
    });
    if(!r.ok) throw new Error('status '+r.status);
    // Si OK, vaciar cola pendiente
    localStorage.removeItem('gps_queue');
  }catch(e){
    const q=JSON.parse(localStorage.getItem('gps_queue')||'[]');
    q.push({lat,lng,ts:Date.now()});
    if(q.length>20) q.shift();
    localStorage.setItem('gps_queue',JSON.stringify(q));
    console.warn('[GPS] queued:',e.message);
  }
}
```

---

### CRÍTICO 3 — Botón "Llamar" ausente en tarjetas delivery
**Función:** `_renderDlvCard` — línea ~6619-6623  
**Problema:** Las tarjetas tienen WhatsApp pero NO tienen botón de llamada directa.

**Fix (dentro del div de botones de la tarjeta):**
```js
// Buscar el bloque con href="https://wa.me/..." y agregar ANTES:
+(tel?'<a href="tel:+'+waNum+'" class="btn btn-secondary btn-sm" style="text-decoration:none;display:inline-flex;align-items:center;gap:4px" title="Llamar al cliente">'+SVG.phone+' Llamar</a>':'')
```

---

### ALTO 1 — `delUser` no verifica pedidos activos
**Función:** `doDelUser` — línea ~10176  
**Agregar AL INICIO de la función:**
```js
const pedidosActivos=_ordersCache.filter(o=>
  (String(o.vendedorId)===String(id)||String(o.deliveryId)===String(id))&&
  ['Pendiente','Despachado','En Ruta'].includes(o.estado)
);
if(pedidosActivos.length){
  pushNotif('No se puede eliminar: tiene '+pedidosActivos.length+' pedido(s) activo(s)','e');
  return;
}
```

---

### ALTO 2 — Email sin validación regex en JS
**Función:** `saveNewUser` — línea ~9979  
**Agregar después de `const nom=...,email=...`:**
```js
if(!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)){showAlert('nuAlert','e','Email inválido');return;}
```

---

### ALTO 3 — WhatsApp sin validación formato Paraguay
**Funciones:** `saveNewUser` (línea ~9986) y `saveEditUser` (línea ~10136)  
**Agregar para el campo `nuWa`/`euWa`:**
```js
const wa=gv('nuWa').trim();
if(wa&&!/^595[9][0-9]{8}$/.test(wa)){showAlert('nuAlert','e','WhatsApp: formato 5959XXXXXXXX');return;}
```

---

### ALTO 4 — Dashboard delivery: "Recaudado HOY" (no total acumulado)
**Función:** `PAGES.entregas` o zona stats delivery — línea ~6030  
**Buscar `Recaudado total` y cambiar lógica a filtrar por fecha de hoy:**
```js
const hoyStr=new Date().toISOString().slice(0,10);
const recHoy=_ordersCache.filter(o=>
  o.deliveryId===CU.id&&o.estado==='Entregado'&&
  (o.updated_at||o.fecha||'').slice(0,10)===hoyStr
).reduce((a,b)=>a+(b.precio||0)*(b.qty||1),0);
// En el HTML cambiar "Recaudado total" por "Recaudado HOY" y usar recHoy
```

---

### ALTO 5 — Open Food Facts: error silenciado, sin mensaje al usuario
**Función:** `_scanLookupOpenFood` (o el bloque inline en `_scanParaNuevoProducto`) — línea ~10555-10568  
**Fix:**
```js
const ctl=new AbortController();
const tid=setTimeout(()=>ctl.abort(),4000);
try{
  const resp=await fetch('https://world.openfoodfacts.org/api/v0/product/'+encodeURIComponent(codigoN)+'.json',{signal:ctl.signal});
  clearTimeout(tid);
  const d=await resp.json();
  // ... resto del código ...
}catch(e){
  clearTimeout(tid);
  const rNP=$('qr-result-np');
  if(rNP)rNP.textContent='Código listo: '+escHtml(codigoN)+' (sin info en base pública)';
}
```

---

### ALTO 6 — Badge urgencia >24h: existe en mapa pero NO en tarjetas delivery
**Función:** `_renderDlvCard` — línea ~6592  
**Fix:** Llamar `_mapaUrgencia(o)` dentro de la tarjeta:
```js
// Al inicio de _renderDlvCard, antes del return:
const urg=typeof _mapaUrgencia==='function'?_mapaUrgencia(o):0;
const urgBadge=urg>1?'<span class="badge bc" style="font-size:9px">⚡ '+urg+'h sin movimiento</span>':
               urg>0?'<span class="badge bp" style="font-size:9px">⏱ '+urg+'h</span>':'';
// Agregar urgBadge en el header de la tarjeta
```

---

## 🟡 MAPA MOBILE — ESTADO ACTUAL Y LO QUE FALTA

### Lo que se hizo en esta sesión:
- ✅ Panel `#mapaContadores` colapsa por defecto en mobile (`window.innerWidth<640`)
- ✅ Mapa más alto: `calc(100vh - 160px)` en mobile (era 220px)
- ✅ Botones estilo (día/noche/satélite/etc.) → dropdown horizontal en mobile, con botón engranaje
- ✅ Botón "← Volver" movido a `top:10px;left:10px` (ya no tapa los botones de estilo)
- ✅ CSS `flex-wrap:nowrap` en topbar del mapa con `!important`
- ✅ Combos zona/vendedor compactos: `max-width:100px` en mobile

### Lo que AÚN FALTA (reportado por el usuario):
- ❌ **Botones del mapa feos en TODOS los roles** (superadmin tiene más botones = peor). El problema es que hay botones extra que NO están en el `⋯` y se ven en vertical. Revisar cuáles botones van al `⋯` para CADA rol.
- ❌ **Los combos zona/vendedor en el topbar siguen siendo muy anchos** en algunos dispositivos (el fix de `max-width:100px` puede no ser suficiente en algunos Android). Considerar moverlos DENTRO del panel `#mapaContadores` colapsable en vez del topbar.
- ❌ **Mapa delivery**: usuario dice que "no se ve bien" — posiblemente el panel de filtros aunque colapsado sigue ocupando espacio o los botones se superponen.

### Solución de fondo sugerida para siguiente sesión:
En vez de parchear el CSS, reestructurar el HTML del mapa para mobile:
```
[topbar] = solo: título + recargar + ⋯
[⋯ panel] = zona, vendedor, deliverys, auto-actualizar, turno
[sobre el mapa] = solo: locate-me + estilo toggle + Volver (top-left)
[mapa] = 100% de la pantalla disponible
```

---

## 🔴 DEPLOY PENDIENTE — WORKER

**Qué hay:** Commit local `dca0010` en `iporave-worker` — fix SQL injection en `catalog-public.js` (escapa wildcards `%_\` en búsqueda por nombre)  
**Cómo deployar:**
```bash
cd C:\Users\USUARIO\iporave-worker
npx wrangler deploy
```
**IMPORTANTE:** Pedir confirmación del usuario ANTES de deployar.

---

## 🔧 ESCÁNER — ESTADO ACTUAL

### Lo que funciona:
- ✅ `Html5QrcodeSupportedFormats` con EAN-13, EAN-8, UPC-A/E, CODE-128/39/93, ITF
- ✅ `qrbox` rectangular dinámico (92% del viewport width × 38% height)
- ✅ `fps:15`, `aspectRatio:1.777`
- ✅ Detección automática de cámara trasera via `Html5Qrcode.getCameras()`
- ✅ Fallback manual: si la cámara falla, aparece campo de texto para escribir el código
- ✅ Lookup Open Food Facts para auto-completar nombre al crear producto nuevo
- ✅ Beep de confirmación (Web Audio API)

### Lo que puede seguir fallando:
- En algunos Android con labels de cámara en español, `_scannerCameraTarget` elige índice [length-1] en vez de cámara trasera real → FIX en pendientes (MEDIO 1)
- Productos paraguayos locales no están en Open Food Facts → el fallback manual resuelve esto
- Open Food Facts puede tardar o fallar sin mensaje al usuario → FIX en pendientes (ALTO 5)

### Si el usuario reporta que sigue sin funcionar:
1. Verificar que el CDN `html5-qrcode@2.3.8` carga (en devtools → Network)
2. Verificar que `Html5QrcodeSupportedFormats` es un objeto (en consola: `typeof Html5QrcodeSupportedFormats`)
3. Considerar migrar a **Quagga2** (`quagga2` npm/CDN) — mucho mejor para EAN-13 en mobile

---

## 📋 TODOS LOS PENDIENTES ORDENADOS

### Bloque A — Seguridad (hacer primero)
1. **XSS DOMPurify** — 3 instancias (ver código exacto arriba en CRÍTICO 1)
2. **delUser sin verificar pedidos** — 1 línea (ver ALTO 1)
3. **Email regex** — 1 línea (ver ALTO 2)
4. **WhatsApp validación** — 2 líneas (ver ALTO 3)
5. **Deploy worker catalog-public** — `npx wrangler deploy` (pedir permiso)

### Bloque B — UX Delivery (hacer segundo)
1. **Botón Llamar** en tarjetas delivery (ver CRÍTICO 3)
2. **Recaudado HOY** en dashboard delivery (ver ALTO 4)
3. **Badge urgencia 24h** en tarjetas (ver ALTO 6)
4. **Open Food Facts error handling** (ver ALTO 5)
5. **GPS queue local** cuando falla la red (ver CRÍTICO 2)
6. **Mensaje GPS en español** con instrucciones para habilitar permisos (ver MEDIO 5)

### Bloque C — Mapa mobile (reestructuración necesaria)
1. Mover combos zona/vendedor del topbar al panel `#mapaContadores`
2. Topbar del mapa: solo título + recargar + `⋯` en TODOS los roles
3. Revisar qué botones van al `⋯` por rol (admin tiene más que delivery)
4. Verificar que `confirm()` en el mapa se reemplaza por modal `openA`

### Bloque D — Mejoras UX (hacer cuando haya tiempo)
1. `confirm()` → modal `openA` en 11+ lugares (ver MEDIO 4)
2. Liquidación proveedor: eliminar fallback por nombre (ver MEDIO LIQ-1)
3. IVA del flete en boleta: configurable (ver BAJO BOLETA-1)
4. Sweep emojis remanentes (📦✅⚠️💬👤 etc. — ver RELEVO v4 para lista completa)
5. `_withLoading(btn, fn)` aplicar a saveOrder, saveUser, saveProducto
6. `_confirmDoubleClick` para eliminaciones críticas

---

## 🛠️ PATRONES TÉCNICOS CRÍTICOS

```
NUNCA dentro de JS en HTML: </script> → siempre '<scr'+'ipt>'
ANTES de commit: node validate.js en /c/Users/USUARIO/iporave-sistema
openA(title, body, footer) → title usa innerHTML (acepta SVG)
DL.* = DataLayer Supabase
CU = usuario actual (CU.rol, CU.id, CU.auth_id UUID)
getVisibleOrders() filtra por rol automáticamente
escHtml(str) / escAttr(str) para escapar
pushNotif(msg,'i'/'e'/'s') = toast
$('id') = getElementById
SVG.* = objeto global con 50+ íconos SVG
```

## 🏗️ STACK

| Capa | Tech |
|------|------|
| Frontend | SPA vanilla JS/HTML, 1 archivo, ~17.800 líneas |
| Backend | Cloudflare Workers, ~50 endpoints en `src/api/` |
| DB | Supabase PostgreSQL + RLS |
| Storage | Cloudflare R2 |
| Hosting | Vercel (auto-deploy desde GitHub main) |
| IA | Groq → Gemini Flash → Gemini Lite → DeepSeek R1 → Anthropic Haiku |

## 📊 EMPRESA
```
nombre: Distribuidora Iporãve
ruc: 80167603-7
timbrado: 18662937
```

---

## 🚀 PROMPT INICIO PRÓXIMA SESIÓN

> Hola. Soy iporaveparaguay@gmail.com. Continuación 16-may-2026.
> Leer `.agentes/RELEVO_MAESTRO_2026-05-16_v5.md` para contexto completo.
> Último commit frontend: `759d170`. Worker pendiente deploy: `dca0010`.
> Prioridad 1: Bloque A seguridad (XSS DOMPurify + delUser + email + whatsapp).
> Prioridad 2: Bloque B delivery (botón llamar + recaudado HOY + badge urgencia).
> Prioridad 3: Bloque C mapa (reestructurar topbar todos los roles).
> Modo ahorro tokens. Delegar a agentes todo lo posible.

---

**Fin RELEVO v5 — 2026-05-16 ~92% tokens.**
