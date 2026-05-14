# RELEVO Claude Sesión 6 — 2026-05-14 (continuación tarde/noche)

## Versiones actuales
- **Worker:** `4077a8ab` (iporave-api.iporaveparaguay.workers.dev)
- **Frontend:** `4adb53d` (iporave-sistema.vercel.app) — en deploy Vercel ahora
- **Supabase:** hrpnqbmknmgdaaokjelb.supabase.co

---

## Qué se resolvió esta sesión

### Problema crítico: Login "Usuario no encontrado"
**Causa raíz:** `auth_id` desincronizado entre `auth.users` y tabla `usuarios` (quedó NULL)
**Solución:**
- `login.js`: fallback por email cuando `auth_id IS NULL` + auto-repair del `auth_id` para futuros logins
- `save-user.js`: recuperación de usuarios huérfanos en Auth, denylist de campos sensibles para admin
- `login.js` SELECT_COLS expandido para incluir banco, wallet, dirección, etc.

### Problema crítico: Perfiles bloqueados por perfilCompleto
**Causa:** `_perfilCompleto()` siempre retornaba `true` (destructuring roto)
**Solución:** Función ahora retorna `{ok, missing}`. Admin solo necesita nombre+email. Cliente no requiere pago.

### Problema crítico: NAV vacío para vendedor, proveedor, dropshipper
**Causa:** `_ensureClientesNavCfg` y `_ensureFacturasB2BNavCfg` empujaban objetos planos como secciones
**Solución:** Ambas funciones corregidas para agregar items a secciones existentes

### Problema crítico: Todos roles no-admin aparecen "Offline"
**Causa:** `config.js` solo retornaba claves Supabase a admin/superadmin
**Solución:** Config devuelve claves a TODOS los usuarios autenticados (anon key es pública de todos modos)

### Device verification loop
**Causa:** `hashDevice()` usaba `JSON.stringify()` con orden de claves inestable
**Solución:** Normalizados a objeto con claves en orden fijo antes de hash

---

## Fixes deployados esta sesión (commit 4adb53d — frontend)

### Agente 1 — Modal cleanup + cliente nav
- `nav()` cierra todos los modales al cambiar de página (evita modales zombies)
- Cliente bloqueado de páginas de admin (redirige a dashboard)
- Perfil auto-open solo se dispara una vez (`window._perfilAutoOpened`)
- Subtítulo del sistema en español: "PLATAFORMA INTEGRAL DE COMERCIO Y LOGÍSTICA"

### Agente 2 — Performance TOP 4
- Scroll listener leak: guard `window._winScrollTopBound` evita re-bind en cada tick
- Polling mensajes condicionado a `!_realtimeSub` (solo si realtime está caído)
- Debounce 1.5s en `_rtRefreshOrders()` para evitar ráfagas de refreshes
- Charts.js: ya tenían `.destroy()` previo — no requirió cambios

---

## Fixes deployados esta sesión (commit 21d705e — worker)

### Seguridad
- Device bypass `@iporave.com` eliminado de login.js (era solo para testing)
- Archivo `sql/migraciones_pendientes.sql` creado con la migración de auto-increment

---

## Estado de usuarios de prueba (todos funcionales)
| Usuario | Email | Password | Auth OK |
|---------|-------|----------|---------|
| admin (Luis) | admin@iporave.com | Admin1234! | ✅ |
| vendedor | vendedor@iporave.com | V3nd3d0r_Ip0r@!26 | ✅ |
| delivery | delivery@iporave.com | D3l!v3ry_Ip0r@26 | ✅ |
| dropshipper | dropshipper@iporave.com | Dr0pSh!p_Ip0r@26 | ✅ |
| proveedor | proveedor@iporave.com | Pr0v3d0r_Ip0r@26 | ✅ |
| cliente | cliente@iporave.com | Cliente123! | ✅ |

**Nota:** Todos los usuarios tienen perfiles completos con banco, wallet, dirección, cédula.
Los dispositivos de los usuarios de prueba ya están autorizados en la tabla `dispositivos`.
El device bypass fue eliminado, pero los usuarios reales en `dispositivos` siguen autorizados.

---

## PENDIENTE CRÍTICO: Migración DB

**pedidos.id no tiene auto-increment.** Esto causa error al crear pedidos sin ID explícito.

**Solución:** Ejecutar en Supabase SQL Editor (`iporave-worker/sql/migraciones_pendientes.sql`):

```sql
CREATE SEQUENCE IF NOT EXISTS pedidos_id_seq;
-- Primero verificar: SELECT MAX(id) FROM pedidos;
-- Luego ajustar: SELECT setval('pedidos_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM pedidos));
ALTER TABLE pedidos ALTER COLUMN id SET DEFAULT nextval('pedidos_id_seq');
ALTER TABLE pedidos ALTER COLUMN id SET NOT NULL;
```

**Impacto si no se hace:** Crear pedidos desde el frontend fallará a menos que el frontend envíe id manual.

---

## Pendientes PRE-PRODUCCIÓN

1. **email_confirm: true en save-user.js** → Está en `true` (correcto para admin-creados). Revisar si se necesita `false` para auto-registro cuando se implemente.

2. **Migración pedidos.id** → Ver sección anterior.

3. **Dispositivos de usuarios de prueba** → Antes de producción real, limpiar la tabla `dispositivos` o revocar los hashes de testing.

---

## Auditoría de seguridad (completada)

### Resueltos
- ✅ Fallback login por email (solo cuando auth_id IS NULL)
- ✅ Recuperación huérfanos en Auth
- ✅ lat/lng=0 rechazados como inválidos en tracking
- ✅ Columnas sensibles en denylist para admin
- ✅ Device bypass de testing eliminado
- ✅ config.js no expone service key

### Pendientes MEDIUM
- ⚠ Delivery PATCH puede modificar cualquier columna (falta validación column-level)
- ⚠ Rate limiting en tracking endpoint (puede floodear la DB con posiciones)

---

## Próximos pasos sugeridos

1. **[URGENTE]** Ejecutar migración pedidos.id en Supabase SQL Editor
2. **[CORTO]** Fix delivery: validar columnas permitidas en PATCH
3. **[CORTO]** Rate limit en tracking (máx 1 update cada 5s por usuario)
4. **[MEDIO]** Proveedor: charts muestran vacío (seed sin datos de ventas del proveedor)
5. **[MEDIO]** Catálogo: imágenes de productos rotas (seed sin imagen_url)
6. **[FUTURO]** Auto-registro público de usuarios externos (después de tienda pública)
7. **[FUTURO]** Mapbox V6 — reemplazar Leaflet

---

## Archivos modificados esta sesión

### iporave-sistema/public/index.html
- `_ensureClientesNavCfg()` — fix NAV vendedor
- `_ensureFacturasB2BNavCfg()` — fix NAV proveedor/dropshipper
- `_perfilCompleto()` — retorna {ok,missing} correctamente
- `nav()` — cierra modales + bloquea cliente de páginas admin + guard perfilAutoOpened
- subtítulo español
- `window._winScrollTopBound` guard
- `_realtimeSub` condicional en polling mensajes
- `_rtRefreshOrders` con debounce 1.5s

### iporave-worker/src/api/login.js
- SELECT_COLS con todos los campos de perfil
- Fallback email + auto-repair auth_id
- hashDevice normalizado (orden fijo)
- Device bypass @iporave.com ELIMINADO ← importante

### iporave-worker/src/api/save-user.js
- placeholder `[managed-by-auth]` para columna password legacy NOT NULL
- Preservar username/email/rol en updates parciales
- Denylist para admin (verificado, badge_confianza, tracking)
- Recuperación de usuarios huérfanos en Auth

### iporave-worker/src/api/config.js
- Claves Supabase a TODOS los usuarios autenticados (no solo admin)

### iporave-worker/sql/migraciones_pendientes.sql (nuevo)
- SQL para auto-increment en pedidos.id
