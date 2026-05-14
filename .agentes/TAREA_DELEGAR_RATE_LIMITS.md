# Tarea para delegar: rate limits en endpoints costosos restantes

## Contexto
Hoy se aplicó rate limit a `/api/claude` en `iporave-worker/src/api/claude.js` (20 req/min por user_id, Map en memoria). Falta replicar el mismo patrón en otros endpoints que también consumen API keys pagas o recursos finitos.

## Endpoints a proteger

### 1. `/api/route` — `iporave-worker/src/api/route.js`
- **Costo:** consume ORS (OpenRouteService) o Google Maps Directions API. Pago.
- **Límite sugerido:** 20 requests por minuto por user_id.

### 2. `/api/geocode` — `iporave-worker/src/api/geocode.js`
- **Costo:** consume Google Maps Geocoding API. Pago por request.
- **Límite sugerido:** 30 requests por minuto por user_id.

### 3. `/api/upload` — `iporave-worker/src/api/upload.js`
- **Costo:** R2 storage (espacio + operaciones clase A). Cada upload escribe.
- **Límite sugerido:** 30 uploads por hora por user_id (más restrictivo porque son archivos pesados).

### 4. `/api/resolve-link` — `iporave-worker/src/api/resolve-link.js`
- **Costo:** hace fetch saliente + geocoding. Bajo, pero scrapeable.
- **Límite sugerido:** 10 requests por minuto por user_id.

### 5. `/api/orders/notify` y `/api/notif-entrega` — WhatsApp
- **Costo:** mensajes WhatsApp via Green API o Meta (cuota mensual).
- **Límite sugerido:** 30 por hora por user_id.

## Patrón a copiar (de claude.js)

```js
// Al inicio del archivo, después de los imports:
const _xLimits = new Map();
const X_WINDOW_MS = 60_000;   // ajustar según endpoint
const X_MAX_REQ = 20;          // ajustar según endpoint

// Dentro del handler, después de verifyToken:
const now = Date.now();
const entry = _xLimits.get(decoded.id) || { count: 0, reset: now + X_WINDOW_MS };
if (now > entry.reset) { entry.count = 0; entry.reset = now + X_WINDOW_MS; }
entry.count++;
_xLimits.set(decoded.id, entry);
if (entry.count > X_MAX_REQ) {
  return json({ error: 'Demasiadas requests. Esperá un minuto.' }, 429);
}
```

Renombrar `_xLimits`, `X_WINDOW_MS`, `X_MAX_REQ` con el nombre del endpoint (ej `_geocodeLimits`).

## Validación
- `node --check src/api/<archivo>.js` antes de commit
- `npx wrangler deploy --minify` después de commit
- Smoke test con curl: hacer 25 requests seguidas y verificar que la 21+ devuelva 429

## Quién la puede hacer
- Codex / Aider — patrón mecánico de copiar/pegar/adaptar, ideal para automatizar
- Bajo riesgo, no toca auth ni utils.js core

## Notas
- El Map en memoria no es perfecto en Workers multi-isolate. Para protección robusta usar Cloudflare KV o Durable Objects en una segunda iteración.
- Considerar agregar logging de IPs sospechosas en `utils.js getClientIP()` cuando se supere el límite.
