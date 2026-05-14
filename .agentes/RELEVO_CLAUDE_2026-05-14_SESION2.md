# RELEVO SESIÓN CLAUDE — 2026-05-14 (Sesión 2, tarde)
**Escrito por:** Claude Sonnet 4.6 (esta sesión)
**Para:** El próximo agente que tome el mando
**Hora de corte:** ~15:00 hora Paraguay
**Razón del corte:** Usuario pidió parada de emergencia completa por riesgo a sistemas

---

## ⚠️ ADVERTENCIA CRÍTICA PARA EL PRÓXIMO AGENTE

**EL SUPERVISOR PYTHON AUTO-RELANZA TODO.** Cada vez que matás un orquestador, el supervisor lo reinicia en segundos. Si querés hacer limpieza de procesos, tenés que matar el supervisor PRIMERO, o no va a funcionar.

**EL AIDER-WRAPPER ES PELIGROSO.** Durante esta sesión, el orquestador-features lanzó un `aider-wrapper.py` que comenzó a destruir `index.html` — borró 9205 líneas. Lo detecté y restauré desde HEAD antes de que se hiciera push. Pero el riesgo es real y permanente mientras los orquestadores tengan acceso a Aider.

---

## ESTADO DEL REPO AL CORTE

### Último commit pusheado: `5162630`
```
5162630 chore: gitignore + docs — ignorar archivos playwright/aider/test
e20a0c2 docs: AVENTON — prohibir modo monitoreo pasivo y loops
226f0a8 docs: AVENTON_URGENTE — instrucciones ejecutables paso a paso para Claude nuevo
ff5bd77 fix: campanita scroll opacity effect — faded al bajar, solida al subir
bcb5f98 fix: kebab menu derecha, botones mobile tactiles, act-btns spacing
1c6b9d8 fix: padding lcard2 mobile, topbar flex-wrap mobile
a68c8c4 fix: login mobile h1 responsive, bgWrap flex, campanita transicion, catalog touch-friendly
```

### Archivos con cambios sin commitear:
- `.agentes/ORQUESTADOR.md` — modificado (estado de tareas actualizado por orquestadores + por mí)
- `.agentes/RELEVO_GEMINI_2026-05-10.md` — modificado por orquestadores (no tocar)
- `.aider.chat.history.md` y `.aider.input.history` — ignorados en .gitignore pero aparecen (ya en .gitignore)

### Archivos untracked que NO se commitearon (quedan locales):
```
.agentes/INSTRUCCIONES_ANTIGRAVITY.md
.agentes/RELEVO_CLAUDE_2026-05-13.md
.agentes/RELEVO_CODEX_2026-05-12.md
.agentes/RELEVO_URGENTE_MANANA.md
.agentes/TAREA_ANTIGRAVITY_CATALOGO.md
.agentes/TAREA_CODEX_INFRAESTRUCTURA.md
.agentes/abrir-ventanas-agentes.bat
.agentes/aider-wrapper.py          ← PELIGROSO, ver abajo
.agentes/codex-solucionador.py     ← ROTO, no usar
.agentes/crear-datos-prueba.py
.agentes/iniciar-todos.ps1
.agentes/lock_util.py
.agentes/monitor-pizarron-codex.ps1
.agentes/no-browser.bat / .py
.agentes/orq_base.py
.agentes/orquestador-catalog.py    ← orquestadores nuevos (no commiteados)
.agentes/orquestador-features.py   ← orquestadores nuevos (no commiteados)
.agentes/orquestador-paginas.py    ← orquestadores nuevos (no commiteados)
.agentes/tester-visual.py
abrir-pizarron-iporave.bat
public/App.vue / css/ / js/ / router/ / src/ / views/  ← carpetas Vue (no parte del SPA, ignorar)
serve-public.js
specs-real.txt
```

---

## QUÉ HICE EN ESTA SESIÓN (en orden cronológico)

### 1. Arranque y diagnóstico
- Leí `RELEVO_CLAUDE_2026-05-14.md` y `AVENTON_URGENTE_CLAUDE.md` completos
- Encontré que la sesión anterior dejó instrucciones de 5 pasos ejecutables
- Estado inicial: 8 procesos Python corriendo (supervisor, cerebro-monitor, 5 orquestadores, codex-solucionador)

### 2. Fixes aplicados a `public/index.html` (ya commiteados y en producción)

**Commit `a68c8c4`:**
- `.llogo h1` responsive: `font-size:clamp(22px,7vw,30px)` en mobile
- `.llogo > span[title="Paraguay"]` reposicionado en mobile
- `body:has(#appScreen.show) #bgWrap{display:inline-flex !important;max-width:200px;flex-shrink:1;}` — fix para bgWrap que tapaba botones
- `#codexNotifBell{transition:opacity .25s ease;}` — transición suave para campanita

**Commit `1c6b9d8`:**
- `.lcard2{padding:14px 14px 14px 20px;}` — padding uniforme en mobile
- `.topbar{flex-wrap:wrap;gap:4px;padding:8px 14px;}` — topbar responsive
- `.tbar-actions{flex-wrap:wrap;gap:6px;}` — acciones del topbar en mobile

**Commit `bcb5f98`:**
- `.lcard2 .order-menu-wrap{margin-left:auto;flex-shrink:0;}` — kebab siempre a la derecha
- `.act-btns{justify-content:flex-start;gap:8px;}` — botones de acción con spacing correcto
- `.order-menu-btn{min-width:40px;min-height:40px;}` en mobile, `min-height:44px;min-width:44px` global

**Commit `ff5bd77`:**
- `#codexNotifBell.scroll-faded{opacity:0.3;}` — campanita se desvanece al hacer scroll
- En `_notifSessionInit()`: listener de scroll que agrega/quita clase `scroll-faded`
- Fix campanita antes del login: `setTimeout(function(){if(typeof CU!=='undefined'&&CU&&CU.id)_notifSessionInit();},500);` — la campanita solo se muestra SI el usuario está logueado

### 3. Fix en archivos de agentes Python

**`model_pool.py` línea 122:** `encoding='utf-8'` → `encoding='utf-8-sig'`
- Razón: `api-keys.json` tiene BOM UTF-8. Sin este fix, Python no puede leer las API keys y cerebro-monitor falla con "google_ai_studio no encontrado"

**`cerebro-monitor.py` línea 79:** `encoding='utf-8'` → `encoding='utf-8-sig'`
- Misma razón

### 4. Commit docs y gitignore (`5162630`)
- Actualicé `.gitignore` para ignorar: `playwright_state.json`, `test-screenshots/`, `pyoverrides/`
- Commiteé: `TAREA_DATOS_PRUEBA_EXTENDIDOS.md`, `TAREA_PEDIDOS_BOTONES_OVERFLOW.md`, `TAREA_UI_LOGIN_MOBILE.md`, `PLAYBOOK_SUPERVISOR.md`
- Actualicé `ORQUESTADOR.md`: marqué `visual-campanita-scroll` como `[x]`

### 5. EMERGENCIA DETECTADA Y RESUELTA: aider-wrapper destruyó index.html
- El orquestador-features lanzó `aider-wrapper.py` con una tarea CSS para index.html
- Aider en Windows tiene UnicodeEncodeError (barra de progreso con caracteres UTF-8)
- En lugar de fallar limpio, Aider borró casi todo el contenido del archivo (9205 líneas eliminadas)
- Lo detecté con `git diff --stat HEAD public/index.html` ANTES de hacer push
- Restauré con `git checkout HEAD -- public/index.html`
- Verificado con `node validate.js` → ✅ Todo OK
- **LECCIÓN: Nunca dejar que Aider toque index.html en Windows sin supervisión**

---

## PROBLEMAS ESTRUCTURALES QUE ENCONTRÉ

### Problema 1: El supervisor es contraproducente para limpieza
El `orquestador-supervisor.py` tiene lógica de auto-relaunch: si un orquestador muere, lo reinicia. Esto hace imposible matar orquestadores individualmente mientras el supervisor corre. Al matar los orquestadores, el supervisor inmediatamente los relanza. Terminé teniendo 16 procesos Python en algún momento.

**Solución correcta:** Matar supervisor PRIMERO → matar orquestadores → reiniciar solo lo que se necesita.

### Problema 2: codex-solucionador.py está roto pero el supervisor lo relanza
`codex-solucionador.py` aparece relanzado por el supervisor aunque no está en la lista `ORQUESTADORES` del supervisor. Puede estar en otra lista o el script se auto-inicia. Hay que revisar qué lo relanza y deshabilitarlo.

### Problema 3: Los orquestadores están usando Aider en modo peligroso
El `aider-wrapper.py` existe y los orquestadores lo llaman con tareas CSS sobre `index.html`. En Windows, Aider tiene bugs con encoding que pueden destruir archivos. Los orquestadores NO deberían usar Aider sobre index.html — deben usar la herramienta Edit directa o delegar al Claude humano.

### Problema 4: El POST al pizarrón no funciona para nadie salvo el worker
El endpoint POST de `/api/pizarron` requiere header `X-Agent-Key` con el valor de `PIZARRON_SECRET` (variable de entorno en Cloudflare). Este secret NO está en `api-keys.json` ni en ningún archivo local. Los orquestadores Python intentan postear pero reciben "No autorizado". El GET sí funciona. El sistema de monitoreo del pizarrón está efectivamente ciego para los agentes Python.

### Problema 5: Dos instancias de supervisor corriendo simultáneamente
Cuando maté los procesos y relancé el supervisor, quedaron 2 supervisores activos al mismo tiempo (el original sobrevivió). Esto duplicó todos los procesos. La solución correcta es verificar con tasklist antes de lanzar si ya hay uno corriendo.

---

## QUÉ FALTÓ HACER (PENDIENTE PARA PRÓXIMA SESIÓN)

### URGENTE — antes del lanzamiento de la tarde:

#### 1. SQL de datos de prueba en Supabase (el usuario lo tiene que correr)
El usuario necesita ir a supabase.com → SQL Editor y ejecutar:
```sql
-- PEDIDOS — 4 nuevos para llegar a ~10 total
INSERT INTO pedidos (cliente, telefono_cliente, address, productos, monto_total, estado, drop_id, vendedor_id, delivery_id, prioridad, observaciones) VALUES
('María Rodríguez', '+595 981 234 567', 'Av. Mariscal López 2350, Asunción', '[{"id":1,"nombre":"Yerba Mate 1kg","cant":2,"precio":35000}]'::jsonb, 70000, 'Pendiente', NULL, 1, NULL, false, 'Llamar antes de llegar'),
('Roberto Núñez', '+595 985 111 222', 'Calle Caaguazú 145, Lambaré', '[{"id":3,"nombre":"Azúcar 1kg","cant":5,"precio":12000}]'::jsonb, 60000, 'En camino', NULL, 1, 2, true, 'PRIORIDAD - entrega urgente antes 18:00'),
('Patricia Gómez', '+595 982 333 444', '-25.2890,-57.6512', '[{"id":11,"nombre":"Auriculares Bluetooth","cant":1,"precio":85000}]'::jsonb, 85000, 'Despachado', NULL, 1, 2, false, 'Coordenadas GPS exactas'),
('Andrés Villalba', '+595 971 555 666', 'Av. Eusebio Ayala 4521, Asunción', '[{"id":10,"nombre":"Lavandina 2L","cant":3,"precio":6500},{"id":12,"nombre":"Remera Algodón M","cant":2,"precio":35000}]'::jsonb, 89500, 'Entregado', NULL, 1, 2, false, 'Cliente recurrente');

-- CATÁLOGO — 4 nuevos
INSERT INTO catalogo (nombre, descripcion_html, presentaciones, foto_url, categoria, stock, activo) VALUES
('Pan Casero 500g', '<p>Pan artesanal recién horneado</p>', '[{"presentacion":"500g","precio":8000}]'::jsonb, 'https://picsum.photos/seed/pan/400/400', 'Alimentos', 50, true),
('Café Molido 250g', '<p>Café 100% paraguayo molido fino</p>', '[{"presentacion":"250g","precio":25000},{"presentacion":"500g","precio":45000}]'::jsonb, 'https://picsum.photos/seed/cafe/400/400', 'Alimentos', 30, true),
('Cargador USB-C', '<p>Cargador rápido 25W compatible Samsung/iPhone</p>', '[{"presentacion":"25W","precio":45000}]'::jsonb, 'https://picsum.photos/seed/cargador/400/400', 'Tecnología', 20, true),
('Detergente Lavavajillas', '<p>Detergente concentrado 750ml</p>', '[{"presentacion":"750ml","precio":12000}]'::jsonb, 'https://picsum.photos/seed/detergente/400/400', 'Limpieza', 100, true);
```
**Si da error de columna:** correr primero `SELECT column_name FROM information_schema.columns WHERE table_name='pedidos';` para ver columnas exactas.

#### 2. Usuarios de prueba (el usuario los crea desde la UI)
Ir a https://iporave-sistema.vercel.app → login como superadmin (iporaveparaguay@gmail.com / ivan12345) → crear usuarios:
- vendedor1@test.com / test1234 / rol: vendedor / nombre: Juan Vendedor
- delivery1@test.com / test1234 / rol: delivery / nombre: Carlos Delivery / vehículo: moto / patente: ABC123
- dropshipper1@test.com / test1234 / rol: dropshipper / nombre: Marta Drop

#### 3. Fixes CSS mobile restantes (ver AVENTON_URGENTE_CLAUDE.md sección 3.2, 3.3, 3.4)
Del AVENTON, estos NO se hicieron aún:
- **3.2**: Padding izquierdo uniforme en todas las secciones con borde amarillo (`.lcard2, .section-card, .data-card {padding-left:16px;}`)
- **3.3**: Topbar mobile — verificar que en 375px no se superponga con el contenido
- **3.4**: Campanita mobile — verificar que en 375px tenga mínimo 44px de área táctil

Estos son cambios CSS directos en el bloque `<style>` de `public/index.html`. Usar la herramienta Edit, NO Aider. Correr `node validate.js` antes de cada commit.

#### 4. Worker — security headers (tarea `worker-headers-seguridad`)
En `iporave-worker/src/index.js`, verificar que `corsHeaders()` incluya:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

El deploy del worker requiere permiso explícito del usuario: `npx wrangler deploy --minify` desde la carpeta `iporave-worker`.

#### 5. Smoke test en producción
Abrir https://iporave-sistema.vercel.app en móvil (o Chrome DevTools 375px) y verificar:
- Login funciona
- Menú de roles carga
- Pedidos se ven correctamente
- El botón ⋮ está a la derecha en las cards
- La campanita no aparece antes del login
- El bgWrap no tapa botones

---

## ESTADO DE LAS TAREAS EN ORQUESTADOR.md

```
ZONA VISUAL:
[x] visual-campanita-scroll    ← COMPLETADA en ff5bd77
[x] visual-order-menu-right    ← COMPLETADA en bcb5f98
[x] visual-mobile-btn-spacing  ← COMPLETADA en bcb5f98
(resto de visual-* ya estaban [x])

ZONA CATALOG:
[~] catalog-mobile-ux          ← EN PROGRESO (orquestador-catalog lo tenía)
[~] catalog-card-img           ← EN PROGRESO

ZONA WORKER:
[x] worker-calificaciones, worker-catalog-public, worker-notif-entrega,
    worker-geocode, worker-order-status-logs, worker-audit-validaciones ← todas COMPLETADAS
[ ] worker-headers-seguridad   ← PENDIENTE

ZONA PAGINAS:
[x] paginas-meta-tags, paginas-favicon, paginas-track-mobile,
    paginas-nosotros-mobile, paginas-faq-mobile ← todas COMPLETADAS

FEATURES: todas [!] BLOQUEADAS hasta post-lanzamiento

ZONA AUDITORÍA:
[ ] audit-xss-index
[ ] audit-worker-auth
[ ] audit-mobile-index
[ ] audit-rls-supabase
[ ] audit-errores-js
[~] audit-catalog-seguridad
[ ] audit-worker-rate-limits
[ ] audit-performance-index
```

---

## PROCESOS AL MOMENTO DEL CORTE

**Todos los Python están PARADOS.** El usuario pidió parada de emergencia.

Para reiniciar cuando el usuario lo autorice:
```powershell
# Solo supervisor (él lanza los demás automáticamente)
$env:PYTHONIOENCODING="utf-8"
Start-Process python -ArgumentList "C:\Users\USUARIO\iporave-sistema\.agentes\orquestador-supervisor.py" -WorkingDirectory "C:\Users\USUARIO\iporave-sistema" -WindowStyle Minimized
```

**IMPORTANTE:** El supervisor relanzará features, catalog, worker, paginas, orquestador.py. Eso es 5 procesos adicionales más sus subprocesos. Si solo querés supervisor + cerebro-monitor, hay que modificar la lista `ORQUESTADORES` en `orquestador-supervisor.py` antes de arrancarlo.

---

## RECOMENDACIÓN PARA EL PRÓXIMO AGENTE

### Antes de tocar nada:
1. Leer este archivo completo
2. Hacer `git log --oneline -10` para confirmar estado
3. Hacer `git status --short` para ver qué hay sin commitear
4. NO arrancar ningún Python hasta que el usuario lo autorice

### Reglas que aprendí a los golpes:
1. **Nunca delegar Aider sobre index.html en Windows** — Aider tiene UnicodeEncodeError que destruye archivos. Usar Edit tool directo.
2. **Matar supervisor ANTES que los orquestadores** — o te va a relanzar todo
3. **Verificar con `git diff --stat HEAD`** antes de cada commit — aider puede dejar el archivo destruido sin error visible
4. **`node validate.js` es obligatorio** antes de cada commit de frontend
5. **El POST al pizarrón no funciona** — no perder tiempo intentándolo sin el PIZARRON_SECRET
6. **El aider-wrapper.py existe y es peligroso** — los orquestadores lo usan. Considerar deshabilitarlo o ponerle guardrails.

### Lo más urgente para el lanzamiento de hoy:
1. El usuario corre el SQL de pedidos y catálogo en Supabase
2. El usuario crea los usuarios de prueba desde la UI
3. Smoke test en mobile
4. Los fixes CSS restantes son menores — la app es usable en móvil ya con los fixes actuales

---

## INFORMACIÓN TÉCNICA CLAVE

### Git
- Repo frontend: `C:\Users\USUARIO\iporave-sistema` → branch `main` → auto-deploy en Vercel
- Repo worker: `C:\Users\USUARIO\iporave-worker` → branch `master` → deploy manual con `npx wrangler deploy --minify`
- Frontend live: https://iporave-sistema.vercel.app
- Worker live: https://iporave-api.iporaveparaguay.workers.dev

### Credenciales
- Superadmin: iporaveparaguay@gmail.com / ivan12345
- API keys: `C:\Users\USUARIO\node-red-config\api-keys.json` (tiene BOM UTF-8 — usar `encoding='utf-8-sig'` en Python)

### Supabase
- RLS activo — usar `auth.role()` no `auth.uid()` directo
- `auth_id` es el puente UUID entre `auth.users` y tabla `usuarios`
- Para crear usuarios de prueba: SOLO via UI de la app o via Supabase Auth API — no con INSERT directo en tabla `usuarios`

### validate.js
- Siempre correr con `node validate.js` desde `C:\Users\USUARIO\iporave-sistema\`
- Detecta: `</script>` sin escapar, balance de llaves, funciones críticas presentes
- Si falla → NO commitear hasta resolver

---

*Relevo escrito con toda la honestidad posible. Esta sesión fue caótica por el sistema de agentes auto-relanzándose. El próximo Claude debería considerar si vale la pena tener los orquestadores corriendo durante la jornada previa al lanzamiento, dado el riesgo que representan sobre index.html.*
