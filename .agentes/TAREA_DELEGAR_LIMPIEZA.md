# Tarea para delegar: limpieza de código muerto y inconsistencias

## Contexto
Las rondas 10, 12, 14 y 15 de auditoría identificaron varios issues menores que son trabajo de limpieza, no urgentes pero conviene cerrar.

## Tareas

### 1. Borrar código legacy Express en el worker
Los siguientes archivos NO están en el router (`iporave-worker/src/index.js`) y son código muerto con patrones Express/Node que ni siquiera ejecutarían en Cloudflare Workers. Borrarlos para evitar confusión futura:

- `iporave-worker/src/api/auto-registro.js`
- `iporave-worker/src/api/boletas.js`
- `iporave-worker/src/api/ai-chat.js`
- `iporave-worker/src/api/analytics-admin.js`
- `iporave-worker/src/api/delivery-ubicacion.js`
- `iporave-worker/src/api/whatsapp-config.js`
- `iporave-worker/src/api/order-status-logs.js`

**Cómo hacerlo:** verificar primero que NINGUNO esté importado en `src/index.js`. Después `git rm` cada uno y commit.

### 2. Resolver inconsistencia aprobado_at vs autorizado_at
- **Archivo:** `iporave-worker/src/api/aprobar-dispositivo.js`
- **Problema:** la línea 48 escribe `aprobado_at` y la línea 82 escribe `autorizado_at`. Solo una de las dos existe en la tabla `dispositivos` de Supabase — la otra estaría haciendo UPDATE con error silencioso.
- **Cómo resolverlo:**
  1. En Supabase SQL Editor: `SELECT column_name FROM information_schema.columns WHERE table_name='dispositivos' AND column_name LIKE '%_at';`
  2. Ver cuál existe realmente
  3. Cambiar en `aprobar-dispositivo.js` el que no existe por el que sí
  4. Probar el flujo de aprobación de dispositivo nuevo

### 3. Unificar User-Agents de scripts Python
- **Archivos en `.agentes/`:** varios scripts Python usan User-Agents distintos cuando llaman a `/api/pizarron`:
  - `codex-solucionador.py`: `IporaveAgent/1.0`
  - `cerebro-monitor.py`: `CerebroMonitor/1.0`
  - `orquestador.py`: `IporaveOrquestador/1.0`
  - `orquestador-supervisor.py`: `IporaveSupervisor/1.0`
  - `orquestador-worker.py`: `IporaveWorker/1.0`
  - `telegram-bridge.py`: `IporaveBot/1.0`
  - `verificador.py`: `Verificador-Iporave/1.0`
- **Fix:** todos a `IporaveAgent/1.0` para simplificar reglas de Cloudflare WAF.
- Búsqueda y reemplazo simple.

### 4. (Opcional) Documentar schema de Supabase
- **Tarea:** generar `docs/schema.md` con el schema real de cada tabla (column_name + data_type).
- **Cómo:** en Supabase SQL Editor:
  ```sql
  SELECT table_name, column_name, data_type
  FROM information_schema.columns
  WHERE table_schema='public'
  ORDER BY table_name, ordinal_position;
  ```
- Pegar resultado en `docs/schema.md` formateado en markdown.
- Sirve para que futuras auditorías no tengan que reconstruir el schema desde código.

## Quién la puede hacer
- Tareas 1, 3 — Aider / Antigravity (trabajo mecánico)
- Tarea 2 — Codex (requiere verificar contra DB)
- Tarea 4 — Cualquiera (es solo pegar SQL)

## Prioridad
LOW. Estas tareas no rompen producción. Conviene cerrarlas en un sprint de limpieza después de los issues críticos.
