# TAREA PARA CODEX — Infraestructura multi-agente
**Fecha actualizada:** 2026-05-13 22:30
**Asignado por:** Claude Code
**Prioridad:** ALTA
**Estado:** Tareas A y B verificadas OK — pendiente Tarea C

---

## ESTADO ACTUAL DE TAREAS

### ✅ COMPLETADAS (por Claude Code o Codex)
- **cerebro-monitor.py**: reparado completamente — emojis corruptos fixados, `py_compile` OK
- **codex-solucionador.py**: `notificar_telegram` → `escribir_alerta` (ya estaba hecho)
- **model_pool.py**: `_enviar_telegram` → `_escribir_alerta_pool` + `ultimo_switch` logging
- **User-Agent fix**: todos los POSTs Python al pizarrón ahora usan `User-Agent: IporaveAgent/1.0` (8 archivos)
- **TAREA A**: ✅ VERIFICADA — `leer_pizarron()` en `codex-solucionador.py` L64-65 tiene `{"User-Agent": "IporaveAgent/1.0"}` ✓
- **TAREA B**: ✅ VERIFICADA — `ALERTS_FILE = _BASE / "alerts.json"` en `model_pool.py` L44 correcto ✓

---

## BUGS URGENTES — PRIORIDAD 1 (hacer antes que todo lo demás)

### BUG 1 — Campanita (#ntBell) visible en pantalla de login
El ícono de notificaciones aparece en la pantalla de login (donde se pone email/contraseña). NO debe aparecer ahí.
- Buscar en el HTML dónde se renderiza `#ntBell` y asegurarse que solo sea visible dentro de `#appScreen.show`
- Probablemente hay que agregar CSS: `#loginScreen ~ * #ntBell, #loginScreen:not(.hidden) ~ #ntBell { display:none !important; }` o mover el bell dentro del appScreen
- NO tocar login.js ni verifyToken

### BUG 2 — Barra de búsqueda de pedidos en topbar tapa botones
El `#bgWrap` (barra de búsqueda global) fue movida al topbar y en pantallas no maximizadas tapa otros botones.
- El comportamiento correcto: `#bgWrap` debe estar en su posición ORIGINAL (dentro del contenido de la sección pedidos, NO en el topbar)
- En el commit `b0df980` se movió al topbar — hay que revertir eso: sacar `bgWrap` del topbar y devolverlo a su posición original dentro del body/sección
- En mobile especialmente está muy grande y cubre todo

### BUG 3 — Módulo de analítica por rol (PENDIENTE — no urgente)
Falta panel de "cuánto me deben / cuántas entregas / cuánto por cobrar" para vendedor, dropshipper y admin.
Dejar para después de resolver BUG 1 y BUG 2. Tarea: `feature-analytics-admin` en ORQUESTADOR.md.

---

## TAREAS PENDIENTES PARA CODEX (en orden)

### TAREA C — Resolver tareas [!] bloqueadas en ORQUESTADOR.md

Las siguientes tareas están marcadas `[!]` (fallaron 3 veces) en ORQUESTADOR.md:

```
- [!] visual-inputs
- [!] visual-modals
- [!] visual-topbar
```

**Qué hace cada una (ya leído ORQUESTADOR.md):**
- `visual-inputs`: SOLO CSS — buscar selectores input/select/textarea → agregar `border-radius:8px` base + `border-color:var(--accent,#6c63ff); outline:none; transition:border-color .2s ease` en `:focus`
- `visual-modals`: SOLO CSS — buscar `.modal-overlay` → agregar `backdrop-filter:blur(4px); background:rgba(0,0,0,.55)` + en contenedor `.modal-content` agregar `border-radius:14px`
- `visual-topbar`: SOLO CSS — buscar `.topbar`/`#topbar` → agregar `box-shadow:0 1px 8px rgba(0,0,0,.3)` solo si no tiene box-shadow ya

**Por qué fallaron probablemente:** el modelo tocó JS o HTML fuera del bloque `<style>`.

**Tu misión (TAREA C):**
1. Verificar en `iporave-sistema/public/index.html` si esos estilos ya existen (buscar `border-radius:8px` en inputs, `backdrop-filter`, `box-shadow` en topbar)
2. Si el estilo YA EXISTE → marcar `[x]` en ORQUESTADOR.md
3. Si el estilo NO EXISTE → marcar `[ ]` en ORQUESTADOR.md (para que el orquestador reintente)
4. Regla crítica: SOLO modificar el bloque `<style>` — NUNCA tocar `<script>` ni HTML
5. Reportar en este archivo qué se decidió para cada una

**IMPORTANTE:** El archivo index.html tiene 9000+ líneas. Buscar con grep `border-radius.*8px`, `backdrop-filter`, `box-shadow.*topbar` antes de editar.

---

### TAREA D — Tareas visuales [~] pendientes en index.html

Estas tareas estan marcadas `[~]` (en progreso) en ORQUESTADOR.md. Son TODAS solo CSS en el bloque `<style>`.
NUNCA tocar bloques `<script>` ni HTML. SOLO agregar/modificar reglas CSS.

Ejecutar en orden, una a la vez. Despues de cada una: `node validate.js` → commit → push.

1. **visual-sidebar**: buscar `.sidebar` o `#sidebar` → agregar en ese selector: `transition:width .25s ease; overflow:hidden;`

2. **visual-empty-states**: buscar `.empty-state` o `.no-data` o `.lista-vacia` → agregar: `text-align:center; color:var(--text2,#888); font-size:13px; padding:2rem;`

3. **visual-loading**: buscar `@keyframes spin` → asegurar que sea `@keyframes spin { to { transform:rotate(360deg) } }` y el spinner tenga `animation:spin 1s linear infinite;`

4. **visual-tabs**: buscar `.tab` o `.nav-tab` → en selector inactivo: `border-bottom:2px solid transparent;` → en `.tab.active` o `.nav-tab.active`: `border-bottom:2px solid var(--accent,#6c63ff);`

5. **visual-cards-hover**: buscar `.card`, `.lcard2` → agregar `transition:box-shadow .2s ease;` → en `:hover`: `box-shadow:0 4px 20px rgba(0,0,0,.25);`

6. **visual-btn-primary**: buscar `.btn-primary` → agregar: `box-shadow:0 4px 14px rgba(108,99,255,.35);`

7. **visual-scrollbar**: al final del bloque `<style>` agregar: `::-webkit-scrollbar{width:6px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.15);border-radius:3px}`

Para cada tarea completada: marcar `[x]` en ORQUESTADOR.md y reportar al pizarron.

---

## NOTA SOBRE PIZARRÓN

El pizarrón ahora funciona correctamente desde Python con User-Agent.
Para reportar desde tu entorno (si tienes acceso a red), usa:

```python
import json, urllib.request
body = json.dumps({
    'agente': 'Codex',
    'tarea': 'nombre-tarea',
    'archivos': 'archivo.py',
    'estado': 'Finalizado',
    'resumen': 'Que se hizo'
}).encode()
req = urllib.request.Request(
    'https://iporave-api.iporaveparaguay.workers.dev/api/pizarron',
    data=body,
    headers={'Content-Type': 'application/json', 'User-Agent': 'IporaveAgent/1.0'},
    method='POST'
)
urllib.request.urlopen(req, timeout=10)
```

Si no tienes acceso a red, reporta en este archivo.

---

## REGLAS CRÍTICAS

- NO tocar: login.js, utils.js, verifyToken, save-user.js
- NO hacer commits sin correr `node validate.js` primero
- NO hacer `wrangler deploy` — solo git push
- NO modificar cerebro-monitor.py — ya reparado por Claude Code
