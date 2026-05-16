# RELEVO MAESTRO v8 — Iporãve Connect
**Fecha:** 2026-05-16  
**Autor:** Claude Sonnet 4.6 (sesión actual)  
**Estado:** Listo para compactar — LEE ESTO PRIMERO antes de cualquier otra cosa

---

## ⚡ ESTADO INMEDIATO — QUÉ PASÓ EN ESTA SESIÓN

### Commits realizados esta sesión:
- `94d0d56` — docs: MASTER_PENDIENTES + RELEVO v7
- `f358f5e` — docs: MASTER_PENDIENTES v2 — consolidación final 10 agentes

### Lo que se hizo:
1. Se leyó el RELEVO v7 (creado por otra instancia Claude con plan $20 que agotó tokens)
2. Se lanzaron 10 agentes de auditoría en 3 oleadas paralelas cubriendo TODO el sistema
3. Se creó MASTER_PENDIENTES v1 → luego v2 con 94 bugs totales
4. **NO se modificó ningún archivo de código** — solo documentación

### Lo que NO se hizo aún (esperando capturas del usuario):
- Reorganización de botones en topbar
- Cualquier cambio de UI/mobile

---

## 🆕 BUGS NUEVOS REPORTADOS POR EL USUARIO EN ESTA SESIÓN

Estos son bugs que el usuario reportó EN CONVERSACIÓN — no estaban en auditoría anterior:

### BUG-U1 — ALTO | Campo "enlaces" en carga de pedidos muestra cartel negro "Paraguay"
- **Qué pasa:** Al usar el campo de links/coordenadas en el formulario de nuevo pedido, aparece un tooltip/dropdown negro que solo dice "Paraguay" y no desaparece.
- **Causa probable:** Autocompletar del browser, o un componente de maps (Mapbox/Google) que inicializa en ese input y muestra una sugerencia de país.
- **Dónde buscar:** `openNuevoPedido()` o el formulario de nuevo pedido — el input de dirección/enlace/coordenadas.
- **Fix probable:** Agregar `autocomplete="off"` al input, o desactivar el componente de geo-sugerencias en ese campo.

### BUG-U2 — ALTO | Carga de pedidos: falta dropdown para elegir proveedor existente
- **Qué pasa:** Antes había un `<select>` o botón desplegable para elegir el proveedor asignado al pedido. Actualmente no aparece — hay que ingresarlo manualmente.
- **Contexto:** El usuario tiene un proveedor cargado en el sistema pero no aparece en el desplegable de "nuevo pedido".
- **Dónde buscar:** Formulario `openNuevoPedido()` — el campo de proveedor.
- **Fix probable:** Restaurar el `<select>` que se poblaba con `_proveedoresCache`.

### BUG-U3 — ALTO | Carga de pedidos: se eliminaron campos que estaban antes
- **Qué había antes:** Dirección de calle, nombre del sitio (ej: "Shopping Salema San Lorenzo"), enlace URL, coordenadas GPS.
- **Qué falta ahora:** También quieren agregar: ciudad, barrio/zona, para mejor búsqueda.
- **Estado actual:** Estos campos pueden haberse perdido en algún refactor reciente.
- **Fix:** Restaurar campos eliminados + agregar ciudad y barrio.

### BUG-U4 — MEDIO | Zonas: mejorar geocodificación para que el mapa reconozca nombres
- **Qué pasa:** Cuando se elige una zona (ej: "Lambaré"), el mapa no reconoce automáticamente que "Lambaré" = coordenadas de Lambaré, Paraguay.
- **Fix sugerido:** En `saveNewZona()` o en el mapa, usar la API de Mapbox Geocoding para resolver el nombre de la zona a coordenadas, y guardar `lat`+`lng` junto con el nombre.

### BUG-U5 — CRÍTICO | Botones en topbar/header están MAL en toda la app
- **Qué pasa:** En casi todas las páginas, los botones de la barra superior están desorganizados, confusos, ilegibles.
- **Estado:** Usuario SUSPENDIÓ la entrega de la app por este motivo.
- **Plan acordado:** El usuario va a enviar capturas de pantalla. NO tocar botones hasta tener las capturas.
- **Páginas afectadas:** Prácticamente todas — especialmente: pedidos, mapa, zonas, delivery.

### BUG-U6 — MEDIO | Datos de superadmin se comparten con sub-admin (no debería)
- **Qué pasa:** Hay info/datos que pertenecen al superadmin que el sub-admin puede ver o que se muestran compartidos.
- **Fix:** Verificar filtros `created_by` y RLS en tablas de usuarios/pedidos para que sub-admin solo vea su propio scope.

---

## 📋 PLAN DE TRABAJO ACORDADO CON EL USUARIO

### LO QUE EL USUARIO PIDIÓ EXPLÍCITAMENTE:
1. **"Mientras yo saco capturas, vos arreglás todo lo que no tenga que ver con botones de la aplicación y celular"**
   → Arreglar: bugs backend (backup.js, monitor.js), TDZ crashes, seguridad, lógica financiera
   → NO tocar: reorganización de botones, layouts, UI visual, mobile responsive

2. **"Cuando tenga las capturas te las doy"**
   → Esperar capturas antes de cualquier cambio de UI

3. **"Quiero que guardes con todo el contexto para que no pierdas nada cuando lo leas otra vez"**
   → Este documento es esa guarda

---

## 🔴 LISTA PRIORIZADA — QUÉ HACER PRIMERO (SIN CAPTURAS)

### GRUPO A — Crashes en producción (hacer SIN esperar capturas):

**A1. TDZ crash — `const SVG` (index.html línea 2520 vs 4809)**
- El objeto SVG se declara en línea 4809 pero se usa desde línea 2520
- JavaScript TDZ: ReferenceError en runtime
- Fix: Mover `const SVG = { ... }` ANTES de línea 2520
- ⚠️ SVG son ~50 iconos, mover todo el bloque cuidadosamente

**A2. TDZ crash — `_notificaciones` (línea 2101 vs 5370)**
- `_notificaciones` se usa en el canal Realtime (línea ~2101) pero se declara en ~5370
- Fix: Agregar `if(!window._notificaciones) window._notificaciones = [];` ANTES de línea 2101
- O mover la declaración completa arriba

**A3. TDZ crash — `_shownMsgIds` (línea 4649 vs 5183)**
- Fix: Mover declaración antes de línea 4649

**A4. Función duplicada — `_cleanAllAppStorage` (líneas 4380 y 4589)**
- Dos definiciones → la segunda sobreescribe la primera → logout inconsistente
- Fix: Mergear las dos en una sola (la de línea 4589 es más completa, pero verificar qué tiene la de 4380 que no tenga la otra)

**A5. Función fantasma — `openNuevoPedido()` (atajo teclado 'N')**
- El atajo de teclado 'N' llama a `openNuevoPedido()` que no existe
- Fix: Crear la función o remover el atajo

### GRUPO B — Seguridad worker (hacer SIN esperar capturas):

**B1. backup.js — auth fake (CRÍTICO SEGURIDAD)**
- `handleBackupRun` solo verifica que el header empiece con "Bearer " — no llama `verifyToken`
- `handleBackupList` sin autenticación de ningún tipo
- Fix en `iporave-worker/src/api/backup.js`:
  ```js
  import { verifyToken } from '../utils.js';
  // Al inicio de handleBackupRun y handleBackupList:
  const decoded = await verifyToken(request, env);
  if (!decoded || decoded.rol !== 'superadmin') {
    return new Response(JSON.stringify({error:'Forbidden'}), {status:403, headers:corsHeaders(request)});
  }
  ```

**B2. monitor.js — sin autenticación (CRÍTICO SEGURIDAD)**
- `handleMonitorRun` no tiene ninguna auth → expone estado de Supabase, R2, Groq a cualquiera
- Fix: mismo patrón que backup.js

**B3. catalogo-publico.js — expone proveedor_nombre + codigo_barras**
- Líneas 56-58 del archivo
- Fix: Quitar esas 2 columnas del SELECT

### GRUPO C — Lógica financiera incorrecta (sin capturas):

**C1. `_liqDrop` (index.html línea 8223)**
- Usa `ganVend(o)` = (precio×qty) - (costo×qty) - zona.precio
- Debe usar `(o.comision||0) * (o.qty||1)` — la comisión real del dropshipper
- Muestra montos 5-10x mayores al dropshipper

**C2. `analitica_drop` (líneas 9658-9659)**
- Calcula comisión sin multiplicar por qty
- Fix: `(o.comision||0) * (o.qty||1)`

**C3. `_liqDrop` cierre de jornada sin rol check (línea 9067)**
- `ejecutarCierre()` sin verificación de rol
- Fix: `if(!['superadmin','admin'].includes(CU?.rol)) return;`

### GRUPO D — Chat IA (sin capturas):

**D1. `window._asistHistorial` no se limpia en logout (línea 16427)**
- Segundo usuario ve historial del primero
- Fix: En la función de logout, agregar `window._asistHistorial = [];`

**D2. `escHtml()` en respuestas IA (líneas 16444, 3970)**
- Las respuestas del asistente se escapan como HTML plano
- Markdown no se renderiza
- Fix: usar `marked(m.content)` o similar en lugar de `escHtml(m.content)`

---

## 🏗️ ARQUITECTURA DEL SISTEMA (resumen técnico)

### Proyectos en disco:
```
C:\Users\USUARIO\iporave-sistema\    ← Frontend SPA (Vercel)
  public\
    index.html          ← ~18.000 líneas, TODO el app JS+CSS+HTML
    track.html          ← Tracking público (626 líneas)
    sw.js               ← Service Worker (167 líneas)
    manifest.json       ← PWA manifest
  .agentes\             ← Documentación de sesiones
    MASTER_PENDIENTES_2026-05-16_v2.md  ← LISTA PRINCIPAL DE BUGS
    RELEVO_MAESTRO_2026-05-16_v8.md     ← ESTE ARCHIVO

C:\Users\USUARIO\iporave-worker\     ← Backend Cloudflare Workers
  src\
    api\
      backup.js         ← 🔴 SIN AUTH — fix urgente
      monitor.js        ← 🔴 SIN AUTH — fix urgente
      catalogo-publico.js ← 🔴 Expone datos sensibles
      config.js         ← 🟡 Sin rate limit, expone mapboxToken
      file.js           ← 🟡 Sin rate limit
      delete-user.js    ← 🟡 Sin verificar pedidos activos
      save-user.js      ← OK
      orders.js         ← OK (con muchos otros endpoints)
      ...
    utils.js            ← verifyToken, corsHeaders (corsHeaders bug: fija primer origen)
    index.js            ← Router principal
  wrangler.toml         ← Config deploy Cloudflare
```

### Stack:
- **Frontend:** Vanilla JS, HTML, CSS — SPA en un solo archivo `index.html`
- **Backend:** Cloudflare Workers (wrangler deploy)
- **DB:** Supabase Postgres con RLS
- **Auth:** Supabase Auth nativa (signInWithPassword). `CU.auth_id` como puente UUID
- **Storage:** Cloudflare R2 (fotos cédulas, comprobantes)
- **Deploy frontend:** Vercel auto-deploy desde GitHub main
- **Push notifications:** VAPID + aes128gcm en producción

### Variables globales clave en index.html:
```js
CU                    // usuario actual {id, auth_id, rol, nombre, ...}
DL.*                  // DataLayer — llama al worker + gestiona localStorage
SVG.*                 // 50+ iconos SVG como strings HTML (línea 4809 — ¡DECLARA TARDE!)
_zonasCache           // array de zonas (poblado al login)
_proveedoresCache     // array de proveedores
_aiHistory            // historial chat IA flotante (se limpia en logout ✅)
window._asistHistorial // historial PAGES.asistente (NO se limpia en logout ❌)
_pendingQueue         // cola offline
_fotoBase64           // foto última entrega (no se resetea ❌)
```

### Roles del sistema:
- `superadmin` — dueño, acceso total
- `admin` — sub-administrador (solo ve su scope created_by)
- `vendedor` — crea pedidos, ve sus comisiones
- `delivery` — entrega pedidos, GPS tracking
- `dropshipper` — vende externamente, ve su panel comisiones
- `proveedor` — ve pedidos de sus productos
- `cliente` — ve sus propios pedidos

### Patrón `DL.*` (DataLayer):
```js
DL._ls(key)           // localStorage con prefijo ipv5_{uid}_{key}
DL._lg(key)           // getter del mismo
DL.getOrders()        // lista pedidos filtrada por rol
DL.saveOrder(o)       // guarda pedido (worker POST /api/orders)
DL.saveZona(z)        // guarda zona (worker POST /api/zonas)
// etc.
```

### Commits en orden cronológico (últimos conocidos):
```
3fcc1b3  fixes críticos (XSS, localStorage prefijo, confirm delivery, topbar kebab)
9146489  mapa mobile (mapaBackBtn, combos mobile, sidebar z-index)
f7d536c  track.html fix + crearPedidoDesdeProducto + clientes_zonas + proveedor realtime
94d0d56  docs: MASTER_PENDIENTES + RELEVO v7
f358f5e  docs: MASTER_PENDIENTES v2 — consolidación final 10 agentes
```

---

## 📸 PENDIENTE: CAPTURAS DEL USUARIO

El usuario va a enviar capturas de estas secciones para reorganizar botones:
- [ ] Pedidos (topbar, filtros, exportar)
- [ ] Mapa (topbar, botones GPS, filtros)
- [ ] Zonas (topbar, CRUD)
- [ ] Delivery (topbar, acciones)
- [ ] Formulario nuevo pedido (campos faltantes, bug "Paraguay")
- [ ] Cualquier otra página con botones mal organizados

**HASTA TENER LAS CAPTURAS: no tocar ningún layout, botón, ni CSS de UI.**

---

## 📌 CONTEXTO DE NEGOCIO

- **Empresa:** Distribuidora Iporãve
- **RUC:** 80091847-9
- **Ciudad:** San Lorenzo, Paraguay
- **Producto:** Sistema de gestión de pedidos + delivery + catálogo
- **Estado actual:** En producción pero con entrega suspendida temporalmente por bugs UI
- **Urgencia:** Alta — el usuario necesita entregar la app a su equipo lo antes posible
- **WhatsApp soporte:** Número real pendiente de configurar en track.html
- **Shopify:** iporaveparaguay.myshopify.com | Dominio: iporaveparaguay.com

---

## 🔑 PATRONES DE TRABAJO ACORDADOS

1. **Esperar capturas antes de tocar UI/botones** (acordado en esta sesión)
2. **Un tema a la vez** — presentar resultado → PARAR → esperar respuesta del usuario
3. **Siempre explicar permisos en español** antes de pedir aprobación
4. **No deployar sin confirmación** del usuario
5. **Modo automático:** si el usuario dice "permiso total" o "procede", ejecutar sin preguntar
6. **No commit sin permiso** — siempre mostrar qué va a hacer primero
7. **`validate.js`** para verificar sintaxis ANTES de cualquier commit al index.html
8. **No romper `</script>` dentro de strings JS** — siempre dividir: `'<scr'+'ipt>'`

---

## 🧠 CONTEXTO DE SESIÓN / MEMORIA

Archivos de memoria en `C:\Users\USUARIO\.claude\projects\C--Users-USUARIO\memory\`:
- `MEMORY.md` — índice de todas las memorias
- `project_iporave_sistema.md` — arquitectura y versiones actuales
- `project_iporave_estado_actual.md` — estado al 2026-05-16
- `feedback_rol_monitoreo.md` — Claude NO escribe código salvo emergencia
- `feedback_trabajo_paralelo.md` — siempre hacer tareas en paralelo
- `feedback_auditoria_continua.md` — lanzar oleadas de agentes

---

## 📊 RESUMEN ESTADÍSTICO FINAL (auditoría completa)

| Categoría | Total | Corregidos | Pendientes |
|-----------|-------|-----------|------------|
| Críticos (crash) | 17 | 5 | 12 |
| Altos (flujos) | 26 | 0 | 26 |
| Medios (UX) | 29 | 1 | 28 |
| Bajos | 7 | 0 | 7 |
| Seguridad worker | 15 | 2 | 13 |
| Bugs usuario (nuevos) | 6 | 0 | 6 |
| **TOTAL** | **100** | **8** | **92** |

**Fuentes de auditoría:** 15 agentes en total (10 esta sesión + 5 sesión anterior $20)

---

## 🔜 PRÓXIMA SESIÓN — EXACTAMENTE QUÉ HACER

### Paso 1 — Sin necesitar capturas:
1. Leer este archivo y el MASTER_PENDIENTES_v2
2. Fijar TDZ crashes (C1, C2, C3 del MASTER)
3. Fijar `_cleanAllAppStorage` duplicada (C4)
4. Fijar `backup.js` + `monitor.js` sin auth (SEC3/SEC4/SEC12)
5. Fijar `_asistHistorial` logout (A24)
6. Fijar `ejecutarCierre` confirm() + rol check (A25/A26/A21)
7. Fijar `_liqDrop` comisión real (A8)

### Paso 2 — Esperar capturas del usuario para:
- Reorganizar todos los botones de topbar por página
- Restaurar campos formulario nuevo pedido (BUG-U1/U2/U3)
- Mejorar geocodificación zonas (BUG-U4)
- Verificar scope datos superadmin vs sub-admin (BUG-U6)

### Paso 3 — Cuando todo lo anterior esté OK:
- Emoji migration (bloques `_TRACK_ESTADO_ICON`, `stateDefs`, `stepIcons`)
- Helpers `_withLoading` masivos
- Reactivar `_perfilCompleto()` semana 2026-05-23

---

**Fin del RELEVO v8 — 2026-05-16.**  
**Si lees esto en sesión futura: empieza por el Paso 1 de "Próxima sesión".**
