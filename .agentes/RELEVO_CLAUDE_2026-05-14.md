# RELEVO COMPLETO — Claude → próxima sesión
**Fecha:** 2026-05-14  
**Sesión:** Auditoría de seguridad / hardening masivo  
**Estado al cierre:** ACTIVO — agentes corriendo

---

## 1. CONTEXTO DEL PROYECTO

### Arquitectura
| Componente | URL / Detalle |
|---|---|
| Frontend SPA | https://iporave-sistema.vercel.app — auto-deploy desde `github.com/iporaveparaguay/iporave-sistema` rama `main` |
| Worker API | https://iporave-api.iporaveparaguay.workers.dev — Cloudflare Workers, deploy con `cd iporave-worker && npx wrangler deploy --minify` |
| Base de datos | Supabase (PostgreSQL + Auth nativa) |
| Repo worker | Local en `C:\Users\USUARIO\iporave-worker` (rama `master`) |
| Repo frontend | Local en `C:\Users\USUARIO\iporave-sistema` (rama `main`) + GitHub |

### Versiones en producción al cierre
- **Worker:** `5a9173eb` (seguridad headers + rate limits + save-user fix)
- **Frontend:** `b93c630` (notifHistory XSS fix — puede tener más commits de agentes en curso)

---

## 2. QUÉ SE COMPLETÓ EN ESTA SESIÓN (2026-05-14)

### Worker (todos deployados):
| Fix | Descripción |
|---|---|
| Rate limits x6 | claude(20/min), geocode(30/min), orders(30/hr), resolve-link(10/min), route(20/min), upload(30/hr) |
| save-user: auth_id | Protegido contra sobreescritura por admin — impide secuestro de cuenta |
| Security headers | X-Content-Type-Options, X-Frame-Options, Referrer-Policy en `corsHeaders()` de utils.js |
| 7 archivos legacy borrados | ai-chat, analytics-admin, auto-registro, boletas, delivery-ubicacion, order-status-logs, whatsapp-config |
| User-Agents unificados | Todos los .agentes/*.py usan `IporaveAgent/1.0` |

### Frontend (todos pusheados a Vercel):
| Fix | Descripción |
|---|---|
| XSS showAlert/pushNotif | textContent en vez de innerHTML |
| safeUrl() helper | Validación http/https para todos los img src |
| safeUrl x15 puntos | catálogo, usuarios, delivery, entregas, galerías, etc. |
| notifHistory escHtml | `n.msg` escapado en panel de notificaciones |
| bgWrap → fbar | Buscador movido a .fbar inline, #fSrch eliminado |
| catalog.html safeUrl | Grilla y modal de catálogo público |
| escHtml x7 críticos | chat, renderTable, dlvCard, track-public, renderProds, autocomplete, chat-send |

### Supabase (usuario aplicó manualmente):
- RLS activo en 7 tablas: pedidos, usuarios, mensajes, catalogo, cupos, calificaciones, dispositivos
- Funciones helper: `my_id()`, `my_rol()`
- Orphans: 1 usuario + 6 dispositivos — SQL para borrar está listo (ver Sección 5)

---

## 3. TRABAJO EN CURSO — AGENTES CORRIENDO AL CIERRE

**Al cerrar esta sesión hay agentes corriendo. Cuando termine su trabajo van a intentar hacer commit/push pero pueden quedar bloqueados si no hay permisos. Revisar el estado y completar si es necesario.**

### Agente A — track.html XSS fixes
- **Tarea:** Agregar `esc()` y `safeUrl()` en `public/track.html`
- **Fixes:** 3 XSS: innerHTML con `d.producto/direccion/cliente`, `dlv.foto` src sin validar, error message con innerHTML
- **Commit esperado:** `fix: XSS en track.html — esc() y safeUrl() en datos de API`
- **Si quedó bloqueado:** Aplicar fixes manualmente (ver Sección 6 — detalles de cada fix)

### Agente B — index.html 6 XSS fixes  
- **Tarea:** 6 fixes en `public/index.html`
- **Fixes:**
  1. `filtrarBoletas()` ~L5275: `o.cliente, o.producto, o.boletaNum, o.numDoc` → `escHtml(...)`
  2. `_renderChips()` ~L7011: `u.nombre` → `escHtml(u.nombre||'')`
  3. `_shareDrop()` ~L7031: `u.nombre, u.rol` → `escHtml(...)`
  4. `_renderPresForm()` ~L7258: `pr.nombre` en `value="..."` → `escHtml(pr.nombre||'')`
  5. `renderOrderChat()` ~L7657: `m.nombre` en `<b>` → `escHtml(m.nombre||'')`
  6. lista mensajes ~L8415-8419: `u.nombre` en `mc-name` → `escHtml(u.nombre||'')`
- **Después:** `node validate.js` → commit → push
- **Commit esperado:** `fix: escHtml en boletas, chips, shareDrop, presForm, chat y mensajes`

### Agente C — views/ y js/ scan
- **Tarea:** Auditoría XSS en registro-auto.js, registro.js, app.js, RegistroForm.js, WhatsAppConfig.js
- **Es SOLO LECTURA** — va a reportar hallazgos sin hacer cambios
- **Acción:** Cuando reporte, delegar fix a otro agente

---

## 4. TAREAS PENDIENTES CONOCIDAS (por orden de prioridad)

### SEGURIDAD — alta prioridad
- [ ] **UI login — campanita antes de auth** (TAREA_UI_LOGIN_MOBILE.md): la campana de notificaciones aparece antes de loguear. Buscar en `updateNavBadges()` o render del topbar — agregar `if(!CU)return;` o condición equivalente. Archivo: `public/index.html`
- [ ] **Aplicar fixes si agentes quedaron bloqueados** (ver Agentes A y B arriba)
- [ ] **Fixes en views/js según reporte del Agente C** (pendiente resultado)

### SEGURIDAD — media prioridad
- [ ] **WHATSAPP_APP_SECRET** (usuario pendiente): `cd iporave-worker && npx wrangler secret put WHATSAPP_APP_SECRET`
- [ ] **Isidro debe re-tap botón de notificaciones push** — las push pueden no llegar

### UI/UX — baja prioridad (ver TAREA_UI_LOGIN_MOBILE.md)
- [ ] Bandera Paraguay en mobile: posicionar junto a título con 0.5-1cm separación
- [ ] Título más grande en mobile

### Funcionalidades pendientes (futuras)
- [ ] WhatsApp webhook (reconstruir con tabla `pedidos` real)
- [ ] Tienda online pública (registro cliente externo, carrito, pago)
- [ ] Mapbox V6 (reemplazar Leaflet)
- [ ] Rol empresa (sub-admin mejorado)
- [ ] Auto-registro usuarios externos con aprobación

---

## 5. ACCIONES MANUALES QUE EL USUARIO DEBE HACER

### Orphan cleanup (Supabase SQL Editor):
```sql
-- Ver primero qué hay:
SELECT id, username, email, rol FROM usuarios
WHERE auth_id IS NULL OR auth_id NOT IN (SELECT id FROM auth.users);

SELECT id, username, device_hash, ip, creado_at FROM dispositivos
WHERE username NOT IN (SELECT username FROM usuarios WHERE username IS NOT NULL);

-- Borrar dispositivos huérfanos:
DELETE FROM dispositivos
WHERE username NOT IN (SELECT username FROM usuarios WHERE username IS NOT NULL);

-- Borrar usuario huérfano:
DELETE FROM usuarios
WHERE auth_id IS NULL OR auth_id NOT IN (SELECT id FROM auth.users);
```

### WHATSAPP_APP_SECRET (terminal en iporave-worker/):
```
npx wrangler secret put WHATSAPP_APP_SECRET
```

---

## 6. SCHEMA REAL DE TABLAS (VERIFICADO EN CÓDIGO)

**IMPORTANTE: Siempre verificar contra código antes de usar. Columnas mal escritas causan errores silenciosos.**

### `dispositivos`
`id, username, device_hash, ip, autorizado, token_aprobacion, token_expires_at, aprobado_at, autorizado_at, creado_at`
- NO tiene: `usuario_id`, `nombre`, `dispositivo_info`
- `aprobado_at` = flujo email-link, `autorizado_at` = flujo panel admin (ambas existen)

### `usuarios`  
`id, username, email, rol, auth_id, nombre, estado_cuenta, created_by, whatsapp, telefono, foto_perfil, foto_cedula_frente, foto_cedula_dorso, vehiculo, patente, nombre_comercial, ruc, logo, descripcion_negocio, banco, tipo_cuenta, nro_cuenta, titular_cuenta, wallet_tipo, wallet_nro, wallet_alias, ...`
- NO tiene: `created_at`, `creado_at` (tiene `created_by` que es FK)

### `pedidos`
`id, cliente (TEXT), drop_id, vendedor_id, delivery_id, estado, address, ...`
- NO tiene: `cliente_id` (cliente es texto directo), `dropshipper_id` (es `drop_id`)

### `mensajes`
`de_id, de_nombre, para_id, mensaje, ...`
- NO tiene: `de` (texto), `para` (texto)

### `catalogo`
- Precios en columna `presentaciones` (JSON array), NO hay columna `precio`
- Descripción en `descripcion_html`, NO `descripcion`

---

## 7. METODOLOGÍA DE TRABAJO — CÓMO OPERAMOS EN ESTA SESIÓN

### Filosofía
- **Claude = supervisor/arquitecto/seguridad crítica.** Solo toca código cuando es un fix de 1-3 líneas urgente o cuando los agentes no pueden ejecutar bash.
- **Agentes = ejecutores de todo lo demás.** Corriendo en paralelo, sin conflictar entre sí.
- **Regla de no conflicto:** Nunca 2 agentes editando el mismo archivo simultáneamente.

### Cómo lanzar agentes eficientemente
```
Agent({
  description: "Descripción corta 5 palabras",
  run_in_background: true,
  prompt: "prompt muy específico con: rutas exactas, líneas exactas, qué buscar, qué cambiar, cómo commitear"
})
```
- Múltiples agentes en un solo mensaje para paralelismo real
- Subagent_type: `Explore` para SOLO LECTURA (más rápido, no gasta context en edits)
- Default agent para fixes que necesitan editar + commitear

### Ciclo de trabajo
1. **Scan** (Explore agents, solo lectura) → reportan hallazgos
2. **Fix** (agentes con permisos de Edit+Bash) → editan + validate.js + commit + push
3. **Deploy** (worker: `npx wrangler deploy --minify`, frontend: auto en push)
4. Claude revisa resultados → lanza siguiente ronda sin esperar al usuario

### Commits del worker
```
cd C:\Users\USUARIO\iporave-worker
git add src/api/archivo.js
git commit -m "fix: descripción"
npx wrangler deploy --minify
```

### Commits del frontend
```
cd C:\Users\USUARIO\iporave-sistema
node validate.js   # OBLIGATORIO antes de commit
git add public/index.html
git commit -m "fix: descripción"
git push origin main
```

### validate.js — cuándo usarlo
- SOLO para `public/index.html` (no aplica a track.html, catalog.html, etc.)
- Verifica que no haya `</script>` sin escapar dentro de strings JS (rompe toda la SPA)
- Si falla: buscar la línea con `</script>` dentro de un string y dividirla: `'</scr'+'ipt>'`

---

## 8. ERRORES COMUNES A EVITAR

1. **Columnas que no existen en Supabase** — siempre verificar contra código antes de usar. Los errores son silenciosos (Supabase simplemente ignora columnas desconocidas en UPDATE, pero falla en SELECT).
2. **`</script>` dentro de strings JS en index.html** — divide siempre: `'</scr'+'ipt>'`. Si no, rompe la SPA completa.
3. **`node validate.js` obligatorio** antes de cualquier commit de index.html.
4. **Dos agentes editando el mismo archivo** — causa conflicts git. Verificar que no haya otro agente en el mismo archivo antes de editar.
5. **pizarron.js GET debe ser PÚBLICO** — los agentes Python no tienen JWT. No agregar auth al GET.
6. **save-user.js tiene SAFE_SELF_FIELDS** — los usuarios normales NO pueden cambiar su `rol`. Está enforzado en línea 42-48.

---

## 9. ESTADO DE SEGURIDAD — MAPA COMPLETO

### ✅ CERRADO
| Área | Detalle |
|---|---|
| RLS Supabase | 7 tablas con políticas |
| Rate limits | Todos los endpoints del worker |
| XSS críticos index.html | ~30 puntos corregidos |
| XSS catalog.html | safeUrl aplicado |
| auth_id protegido | save-user.js |
| Security headers | X-Frame-Options, nosniff, Referrer-Policy |
| Legacy code | 7 archivos Express eliminados |
| SSRF resolve-link | Whitelist de dominios Google Maps |
| whatsapp-webhook | HMAC SHA-256 |
| pizarron POST | X-Agent-Key optional |
| track-public | Datos sensibles removidos de respuesta |
| claude proxy | Modelo fijo + cap max_tokens |

### 🔄 EN CURSO (agentes trabajando)
| Área | Agente | Estado |
|---|---|---|
| track.html XSS | A | corriendo |
| index.html 6 XSS | B | corriendo |
| views/js scan | C | corriendo |

### ❌ PENDIENTE
| Área | Prioridad |
|---|---|
| campanita en login | MEDIA |
| WHATSAPP_APP_SECRET | MEDIA (usuario) |
| views/js fixes (según scan C) | Depende de resultados |

---

## 10. ARCHIVOS CLAVE DEL PROYECTO

| Archivo | Para qué sirve |
|---|---|
| `iporave-worker/src/index.js` | Router principal del worker — aquí se registran todos los endpoints |
| `iporave-worker/src/utils.js` | `verifyToken()`, `corsHeaders()`, `json()`, `getSupaAdmin()` |
| `iporave-worker/src/api/login.js` | Auth flow completo |
| `iporave-worker/src/api/save-user.js` | Crear/editar usuarios, SAFE_SELF_FIELDS |
| `iporave-sistema/public/index.html` | Toda la SPA (~9500+ líneas) |
| `iporave-sistema/public/catalog.html` | Catálogo público (sin auth) |
| `iporave-sistema/public/track.html` | Tracking público de pedidos |
| `iporave-sistema/validate.js` | Validador de sintaxis OBLIGATORIO antes de commit |
| `iporave-sistema/.agentes/` | Scripts Python de agentes IA, tareas pendientes, playbooks |
| `iporave-sistema/.agentes/PLAYBOOK_SUPERVISOR.md` | Guía completa de cómo supervisar agentes |
| `C:\Users\USUARIO\node-red-config\api-keys.json` | API keys de Groq, Gemini, etc. (NO en git) |
