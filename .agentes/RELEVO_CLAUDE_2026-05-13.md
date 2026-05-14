# RELEVO COMPLETO — Sesión Claude Code 2026-05-13

> **Lector de este documento:** Supervisor que toma el control (Codex / Claude próxima sesión / otro).
> **Objetivo del relevo:** Que puedas seguir trabajando exactamente desde donde quedamos, sin pérdida de contexto, sin volver a auditar lo ya auditado, sin pisar fixes ya aplicados.

---

## Estado al cierre

### Worker en producción
- **Versión actual:** `346119a1-63d2-4550-9631-1eb670c53b9b`
- **URL:** https://iporave-api.iporaveparaguay.workers.dev
- **8 deploys** esta sesión, todos exitosos.

### Frontend en producción
- **Último commit:** `8909aa2` (mobile login title fix). Hoy NO se tocó el frontend.
- **URL:** https://iporave-sistema.vercel.app

### Base de datos
- **RLS aplicada en:** `usuarios`, `pedidos`, `catalogo`, `calificaciones`, `dispositivos`, `push_subscriptions`, `pizarron` (preexistente).
- **RLS pendiente al cierre:** `mensajes` (el usuario está pegando el SQL en Supabase ahora).

---

## Lo que se hizo esta sesión (resumen ejecutivo)

### Bloque 1 — Hardening de seguridad (21 fixes deployados)

**Por archivo del worker:**

| Archivo | Fix aplicado |
|---|---|
| `aprobar-dispositivo.js` | Token single-use + expiración + escape HTML (sesión previa) |
| `rechazar-dispositivo.js` | Token expiry check + select explícito + escapeHtml(titulo) |
| `calificaciones.js` | Verificar participación en pedido + corregir columnas (drop_id, no dropshipper_id) |
| `upload.js` | Sanitización de folder (prevenir path traversal) |
| `push-subscribe.js` | Validar user_id en DELETE + allowlist de hosts push (fcm/mozilla/apple) anti-SSRF |
| `whatsapp-webhook.js` | HMAC SHA-256 validation (sesión previa) — requiere `WHATSAPP_APP_SECRET` |
| `orders.js` | Role check (admin/superadmin/vendedor) + sanitización de campos WA |
| `catalog-public.js` | Fix 500 (columna `precio` no existe → usa `presentaciones` JSON) + console.error temporal |
| `catalogo-publico.js` | Igual fix de `precio` + validación de username (`eq` con caracteres seguros) |
| `export-catalog.js` | Igual fix de `precio` + parsear precio desde JSON `presentaciones` para Meta Ads |
| `resolve-link.js` | **SSRF crítico** → agregar verifyToken + whitelist de hosts Google Maps |
| `track-public.js` | Remover datos personales del response público (telefono, patente, dirección, precio) |
| `claude.js` | Proxy sin restricciones → fijar model+max_tokens server-side, solo aceptar `messages[]` |
| `pizarron.js` | GET con columnas explícitas + POST con `X-Agent-Key` opcional via env `PIZARRON_SECRET`. **NOTA:** El GET no requiere auth para permitir lectura del supervisor Python (no tiene token). |
| `notif-entrega.js` | Role check (solo `delivery`) + corregir columnas (`de_id`/`para_id` en vez de `de`/`para`) |
| `dispositivos-pendientes.js` | Select explícito sin `token_aprobacion` + **regresión arreglada** (quitar `usuario_id` que no existe) |
| `order-status.js` | Allowlist de estados válidos |
| `geocode.js` | **Crash crítico**: ReferenceError `lat`/`lng` antes de auth → eliminar líneas muertas + cap longitud |
| `file.js` | Path traversal prevention + `X-Content-Type-Options: nosniff` |
| `config.js` | Cleanup mensajes al borrar usuarios demo: `de_id`/`para_id` en vez de `de`/`para` |

**Frontend:**
- `vercel.json`: headers de seguridad (HSTS, X-Frame, X-Content-Type, Permissions-Policy)
- `public/index.html`: tap targets 44px, font-size 16px iOS, safe-area notch, `touch-action:manipulation`

### Bloque 2 — Bugs silenciosos descubiertos hoy

**Tabla `pedidos`** — Columnas reales: `id, estado, cliente (texto), telefono, direccion, producto, precio, fecha, gps_lat, gps_lng, vendedor_id, delivery_id, drop_id, updated_at`. NO tiene `cliente_id`, NO tiene `dropshipper_id` (es `drop_id`).

**Tabla `catalogo`** — Columnas reales: `id, nombre, presentaciones (JSON), owner_user_id, visibility, proveedor_nombre, foto, fotos (JSON), videos (JSON), descripcion_html, categoria, stock, codigo_barras, precio_comparacion, publicar_tienda`. NO tiene `precio` (está en `presentaciones`). NO tiene `descripcion` ni `owner_id`.

**Tabla `dispositivos`** — Se conecta al usuario por `username` (texto), no por `usuario_id`.

**Tabla `mensajes`** — Columnas: `id, de_id, de_nombre, para_id, mensaje, leido, created_at`. NO tiene `de` ni `para` (texto). Esto significa que `notif-entrega.js` estaba roto silenciosamente: las notificaciones de delivery a admin nunca se guardaban en producción hasta el fix de hoy.

### Bloque 3 — Archivos legacy descartados (no en router, no se ejecutan)

No tocar, son código muerto: `auto-registro.js`, `boletas.js`, `delete-user.js` (legacy variant), `ai-chat.js`, `analytics-admin.js`, `delivery-ubicacion.js`, `whatsapp-config.js`, `order-status-logs.js`. Tienen referencias a columnas y patrones obsoletos pero no se importan en `src/index.js`.

---

## Pendiente — Acciones manuales del usuario

1. **RLS de `mensajes`** — Usuario está pegando este SQL ahora mismo:
   ```sql
   ALTER TABLE mensajes ENABLE ROW LEVEL SECURITY;
   DROP POLICY IF EXISTS mensajes_select ON mensajes;
   CREATE POLICY mensajes_select ON mensajes FOR SELECT
   USING (
     my_rol() IN ('admin', 'superadmin')
     OR de_id = my_id() OR para_id = my_id()
   );
   DROP POLICY IF EXISTS mensajes_insert ON mensajes;
   CREATE POLICY mensajes_insert ON mensajes FOR INSERT
   WITH CHECK (de_id = my_id());
   ```

2. **`WHATSAPP_APP_SECRET`** (deferido a más tarde por decisión del usuario):
   ```powershell
   cd C:\Users\USUARIO\iporave-worker
   npx wrangler secret put WHATSAPP_APP_SECRET
   ```
   Valor: App Secret de Meta Developers → tu App de WhatsApp → Settings → Basic → App Secret → Show.

3. **`PIZARRON_SECRET` (opcional)** — Si se configura, los agentes Python que escriben al pizarrón deben enviar header `X-Agent-Key: <valor>`. Sin configurar, el POST queda abierto.

---

## Pendientes técnicos (no urgentes)

- **Verificar columnas en `usuarios` y `calificaciones`** que el agente Round 10 marcó como "a verificar" (`badge_confianza`, `calificaciones_total`, `created_by`, `de_rol`, `para_rol`, `fotos`, `video`, etc). Estas probablemente SÍ existen ya que el sistema funciona, pero conviene confirmarlo con un `SELECT column_name FROM information_schema.columns WHERE table_name='usuarios'` en Supabase.
- **Round 11 (frontend audit) corriendo en background** — agente ID `ac0ba11b91146c450`. Resultado pendiente al cierre. Buscaba: endpoints llamados desde el frontend que no existan, queries directas con columnas erróneas, código muerto.
- **`file.js` sin auth** — Decisión consciente: es público para imágenes del catálogo. Si se necesitan archivos privados en el futuro, separar por prefijo (`public/` vs `private/`).
- **CORS wildcard en `utils.js`** — `Access-Control-Allow-Origin: *`. Acceptable por ahora ya que la auth está en `Authorization` header, pero ideal restringir a dominios conocidos.

---

## Features futuras solicitadas (NO prioridad)

Mencionadas por el usuario, guardar para después:

1. **API keys propias por cliente** — Cada cliente con su WhatsApp/Shopify/etc. Implementar tabla `integraciones` con `user_id`, `tipo`, `config` (JSON encriptado).
2. **Puente directo a Shopify** — Como ya existe `/api/export-catalog` para Meta Ads, agregar sync bidireccional con Shopify (productos, pedidos, stock).

---

## Sistema de agentes — Cómo trabajamos

### Arquitectura mental
- **Yo (Claude supervisor)** orquesto y monitoreo. Casi no escribo código directo. Delego.
- **Agentes Explore** (background) buscan, analizan, reportan. No modifican.
- **Aider/Codex/Antigravity** ejecutan tareas más grandes (delego de a poco según conviene).
- **Agentes Python** (en `.agentes/`): supervisor + orquestadores + cerebro + verificador. Trabajan en bucle continuo y reportan al pizarrón.

### Cómo lancé agentes esta sesión
Patrón general por ronda de auditoría:
```
Agent tool con run_in_background: true
Múltiples agentes en paralelo (3-4 por ronda)
Cada agente cubre un slice no-overlapping (ej: "auditar X, Y, Z files")
Espero notificaciones de completion
Aplico fixes en orden de prioridad (CRITICAL → HIGH → MEDIUM)
Deploy frecuente (8 deploys hoy)
Smoke test después de cada deploy
```

### Rondas ejecutadas esta sesión
- Round 6: catalog, orders, export — 4 agentes paralelos
- Round 7: routing, tracking, claude, pizarron, etc — 4 agentes
- Round 8: geocode, services, workers — 1 agente
- Round 9: utils, locationService, r2, geocoding, whatsapp-config — 1 agente
- Round 10: column mismatches en TODO el worker — 1 agente (encontró bug critical de regresión)
- Round 11: frontend audit — 1 agente (pendiente al cierre)

### Cómo monitoreo
- Verificación inmediata post-deploy con `curl` smoke tests
- `wrangler tail --format pretty` para ver errores de Postgres en tiempo real
- Pizarrón leído por supervisor Python desde `/api/pizarron` GET
- Commits con prefijo `fix(seg):` o `fix(regression):` para trazabilidad

### Reglas en automático
Cuando el usuario dice "permiso total" / "modo automático":
- NO pido confirmaciones para fixes y deploys
- NO toco archivos prohibidos: `login.js`, `utils.js` core, `save-user.js`, `verifyToken`
- NO destructivo: `rm -rf`, `git push --force`, `DROP DATABASE`, etc.
- Validar sintaxis con `node --check` antes de commit
- Reportar todo al final

### Si el próximo supervisor toma el control
1. Leer este archivo completo.
2. Revisar el último resultado de Round 11 (agente `ac0ba11b91146c450`) si terminó.
3. Confirmar con usuario que el SQL de `mensajes` se aplicó (debería ser "Success").
4. Si el usuario quiere seguir auditando: lanzar Round 12 en áreas no cubiertas (ej: scripts en `.agentes/`, Vue files en `public/views/` si los hay, schemas en migration files).
5. Si el usuario quiere features nuevas: priorizar las del bloque "Features futuras".

---

## Línea de tiempo de deploys del worker (hoy)

1. `b9b2fbaf` — Round 6: catalog-public 500, orders role check, export-catalog ilike
2. `f85ff7fa` — Round 7: 8 fixes (SSRF, data leaks, proxy abuse)
3. `57bf5639` — rechazar-dispositivo token expiry
4. `5e824545` — Round 8: geocode crash + push SSRF
5. `940d2aff` — file.js path traversal
6. `403197ed` — file.js nosniff + SQL ASCII
7. `c3a544e8` — catalog-public con console.error + pizarron GET público
8. `e6d00db3` — columnas reales catalogo (`presentaciones`) + calificaciones (`drop_id`)
9. `aaa35a5d` — mensajes columns (`de_id`/`para_id`)
10. `346119a1` — **regression fix** dispositivos-pendientes (quitar `usuario_id`)

## Línea de tiempo de commits frontend (hoy)

1. `9535f79` — notifEnRutaAdmin fix (de_id/para_id) + verificador.py endpoints reales
2. `44a50d5` — 7 XSS críticos (chat, renderTable, dlvCard, track-public, catalogo, autocomplete) + SSL local en gemini_resolver
3. `7e6f115` — !important en hide flotantes login + SW cache v9→v10

## Round 10-15 resumen

- **Round 10** (column mismatches worker): encontró regresión `usuario_id` en dispositivos-pendientes (introducida por mí). Arreglada en deploy `346119a1`.
- **Round 11** (frontend bugs/endpoints): encontró XSS críticos + `notifEnRutaAdmin` con columnas viejas. Aplicados los CRITICAL (commits `9535f79`, `44a50d5`).
- **Round 12** (scripts Python): encontró POST sin User-Agent en `verificador.py` y `telegram-bridge.py`, endpoints inexistentes en verificador, SSL global desactivado en gemini_resolver. Arreglados.
- **Round 13** (XSS frontend): encontró 6 CRITICAL XSS. Arreglados los 7 más importantes (incluyendo self-XSS chat).
- **Round 14** (schema reconstruido): listado completo de columnas reales por tabla. Guardado para referencia. Detectó inconsistencia `aprobar-dispositivo.js`: GET escribe `aprobado_at`, POST escribe `autorizado_at` — TBD verificar cuál existe.
- **Round 15** (rate limiting): identificó `/api/claude`, `/api/route`, `/api/geocode`, `/api/upload` sin rate limit. Costo de abuso ALTO. PENDIENTE: agregar rate limit por user_id usando Map en memoria o KV.

## XSS frontend pendientes (no críticos, para próxima sesión)

- `_cargarResenasEnPerfil` L7917-7922 — `c.fotos` URL injection en `onclick`
- Imágenes de perfil L2447, L7831, L7844, L7855 — falta validar prefix `https://`
- `addAIMsg` L2400 — trazar callers
- `showAlert` y `pushNotif` L803, L814 — toasts con error.message de Supabase
- Scanner catálogo L6524 — `codigo` del QR
- `w.document.write` L5018, L5345, L7491, L8045, L8129 — páginas de impresión

## Issues actuales del usuario en sesión

- **Campana en login**: era SW cache (v9 hardcoded). Fix: v10 + `!important`. Tras hard reload debería resolverse.
- **Pedidos viejos aparecen**: localStorage pre-migración Supabase. NO es caché de archivos. El usuario confirmó: modo incógnito NO los muestra. Fix sugerido: `localStorage.clear();location.reload()` o agregar limpieza automática por versión en el siguiente release.
- **Buscador arriba**: el usuario va a mandar captura, pendiente al cierre.

---

## Comandos útiles

```bash
# Ver estado del worker
cd C:\Users\USUARIO\iporave-worker
git log --oneline -10

# Tail en vivo (capturar errores Postgres)
npx wrangler tail --format pretty

# Smoke test
curl -A "IporaveAgent/1.0" https://iporave-api.iporaveparaguay.workers.dev/api/catalog-public

# Deploy
npx wrangler deploy --minify

# Buscar columnas en el código (técnica usada hoy)
grep -A 3 "from('TABLA')" src/api/*.js
```

---

## Archivos clave para conocer el contexto

- `.agentes/RELEVO_CODEX_2026-05-12.md` — Sesión anterior
- `.agentes/orquestador-supervisor.py` — Cerebro de los agentes Python
- `sql/rls_policies.sql` — SQL RLS con las columnas REALES (ya parcheado hoy: `drop_id`, `owner_user_id`, etc)
- `~/.claude/projects/C--Users-USUARIO/memory/` — Memorias del supervisor (MEMORY.md es el índice)
- Memorias relevantes hoy:
  - `project_iporave_estado_actual.md` — actualizado al cierre con todos los fixes
  - `project_features_futuras.md` — API keys por cliente + Shopify
  - `feedback_modo_automatico.md`
  - `feedback_auditoria_continua.md`

---

## Cierre

Sesión muy productiva: 21 fixes de seguridad + 8 deploys del worker + bug silencioso de 500 en catálogo arreglado + columnas reales de la BD documentadas + RLS casi completa.

**El sistema está más blindado al cierre que al comienzo.** Pero quedan bugs por descubrir — los agentes deben seguir trabajando en rondas adicionales.

— Claude (Sonnet 4.6), 2026-05-13
