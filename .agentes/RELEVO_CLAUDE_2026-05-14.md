# RELEVO COMPLETO — Claude → próxima sesión
**Fecha de cierre:** 2026-05-14
**Próxima sesión esperada:** 2026-05-15 (lanzamiento a 10 usuarios reales)
**Estado al cierre:** CERRADO LIMPIO — todo commiteado, pusheado y deployado. Agentes detenidos.

---

## 🚨 INSTRUCCIONES DE ARRANQUE — LEER ANTES QUE NADA

Si sos el próximo Claude y acabás de abrir esta sesión, hacé EXACTAMENTE estos pasos en orden:

### Paso 1 — Confirmar estado del repo
```powershell
cd C:\Users\USUARIO\iporave-sistema; git log --oneline -5
cd C:\Users\USUARIO\iporave-worker; git log --oneline -5
```
Esperado: frontend cabeza en `46d0726` o posterior, worker en `528a00c` o posterior.

### Paso 2 — Confirmar que NO hay agentes Python corriendo
```powershell
Get-Process python* 2>&1
```
Esperado: **vacío**. Si hay procesos vivos = el cierre anterior no fue limpio. Decidir con el usuario si pararlos.

### Paso 3 — Leer el pizarrón (última actividad de agentes)
```powershell
$r = Invoke-WebRequest -Uri "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron" -UseBasicParsing
($r.Content | ConvertFrom-Json).registros | Select-Object -First 5 | ConvertTo-Json
```

### Paso 4 — Saludar al usuario en español y preguntar qué arrancamos
**NO LANZAR AGENTES SIN ORDEN EXPLÍCITA.** El usuario tiene que decir "arrancá los agentes" o equivalente. Hasta entonces: solo monitoreo y conversación.

---

## 🔴 REGLAS ABSOLUTAS (LÍNEAS ROJAS)

### Comunicación
1. **SIEMPRE responder en español** (rioplatense/paraguayo). Nunca cambiar a inglés salvo pedido explícito.
2. **Esperar confirmación SIEMPRE** antes de cualquier acción que toque código, secrets, deploy o roles.
3. **Explicar antes de pedir permiso** — si va a aparecer un permission prompt, traducir las opciones al español primero.

### Cierre de sesión
4. **PARADA DE EMERGENCIA antes de cerrar.** Si los agentes están corriendo cuando se cierra la sesión: PARARLOS PRIMERO, antes de cualquier otra cosa, incluso antes de responder al usuario. El usuario lo dejó claro: "primero acción antes que responder, parada de emergencia de inmediato".
5. **No re-lanzar agentes solo porque parecía buena idea.** Solo arrancan cuando el usuario da la orden explícita.

### Código
6. **NO TOCAR JAMÁS sin permiso explícito:**
   - `iporave-worker/src/api/login.js` — auth, dispositivos, emails
   - `iporave-worker/src/api/save-user.js` — escalación de roles
   - `iporave-worker/src/utils.js verifyToken()` — verificación JWT
   - Migrations / schemas de Supabase destructivos (DROP, ALTER destructivo)

7. **NO HACER NUNCA:**
   - `git push --force` a `main`
   - `wrangler delete` (borra el worker entero)
   - `wrangler secret delete` sin confirmar el valor
   - DROP TABLE / DROP DATABASE / TRUNCATE en Supabase
   - Dos agentes editando el mismo archivo simultáneamente
   - `node validate.js` saltado antes de commit de `public/index.html`

8. **NO ASUMIR columnas o endpoints existen.** Verificar siempre contra código real. Las columnas reales están en sección "SCHEMA DB" más abajo.

---

## 🤖 ESTRUCTURA COMPLETA DEL SISTEMA DE AGENTES

> Esta sección es la más importante. Si la entendés, podés operar todo.

### Arquitectura general

```
┌─────────────────────────────────────────────────────────────┐
│  USUARIO  ←──  Claude Code (vos)  ←──  decisiones tácticas │
└─────────────────────┬───────────────────────────────────────┘
                      │ lanza / detiene
                      ▼
   ┌──────────────────────────────────────────────────────┐
   │  iniciar-todos.ps1  (script de arranque)            │
   │  → lanza Supervisor + Cerebro-Monitor               │
   └──────────────────────┬───────────────────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │  orquestador-supervisor.py       │
        │  - Vigila a los 5 orquestadores  │
        │  - Reinicia los caídos (3 max)   │
        │  - Detecta PARADA_CRITICA.txt    │
        │  - Lee STOP/RESTART del pizarrón │
        │  - Escribe en alerts.json        │
        └─────────────┬────────────────────┘
                      │ lanza y vigila
                      ▼
   ┌──────────────────────────────────────────────────────┐
   │  5 ORQUESTADORES (workers)                          │
   │  ├─ orquestador-features.py   (features generales)  │
   │  ├─ orquestador-catalog.py    (catálogo/Shopify)    │
   │  ├─ orquestador-worker.py     (worker / Cloudflare) │
   │  ├─ orquestador-paginas.py    (páginas públicas)    │
   │  └─ orquestador.py            (orq. principal)      │
   │                                                       │
   │  + codex-solucionador.py  (resuelve tareas Codex)   │
   └──────────────────────┬───────────────────────────────┘
                          │ lanza
                          ▼
   ┌──────────────────────────────────────────────────────┐
   │  AIDER processes (efímeros, ad-hoc)                  │
   │  - aider-wrapper.py los lanza con prompts específicos│
   │  - Usan vertex_ai/gemini-2.5-flash                   │
   │  - Editan archivos directamente                       │
   │  - PELIGRO: pueden colisionar si tocan mismo archivo │
   └──────────────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────────────┐
   │  cerebro-monitor.py (analista, no editor)            │
   │  - Llama a Gemini AI Studio cada 30 min              │
   │  - Lee pizarrón + alerts.json                         │
   │  - Genera análisis para que Claude lea               │
   └──────────────────────────────────────────────────────┘
```

### Quién es cada agente — tabla maestra

| Agente | Tipo | Ubicación | Función | Edita código? |
|---|---|---|---|---|
| **Claude Code (vos)** | Director técnico | esta sesión | Decide, supervisa, fixea crítico | Sí, líneas-rojas off-limits |
| **Codex** | Code editor (externo) | herramienta del user | Frontend `index.html` zona asignada | Sí, con tarea explícita |
| **Antigravity** | Code editor (externo) | herramienta del user | Archivos nuevos en `public/` | Sí, archivos nuevos solamente |
| **Aider** | CLI tool | local Python | Edits puntuales con LLM (Gemini) | Sí, archivo específico |
| **orquestador-supervisor.py** | Watchdog | local Python | Vigila a los 5 orquestadores | No |
| **orquestador-features.py** | Worker autónomo | local Python | Toma tareas "features" del pizarrón | Indirecto vía Aider |
| **orquestador-catalog.py** | Worker autónomo | local Python | Toma tareas "catálogo" | Indirecto |
| **orquestador-worker.py** | Worker autónomo | local Python | Toma tareas del Cloudflare worker | Indirecto |
| **orquestador-paginas.py** | Worker autónomo | local Python | Toma tareas de páginas públicas | Indirecto |
| **orquestador.py** | Worker general | local Python | Orquestador principal/fallback | Indirecto |
| **codex-solucionador.py** | Worker autónomo | local Python | Resuelve tareas para Codex | No, prepara contexto |
| **cerebro-monitor.py** | Analista | local Python + Gemini | Análisis cada 30 min, genera reportes | No |
| **Node-RED + Groq** | Validador (otro PC/servicio) | externo | Validación automática post-fix | No |

### El **Pizarrón** — sistema de coordinación

El **pizarrón** es la tabla `pizarron` en Supabase, expuesta vía REST en el worker.

**URL:** `https://iporave-api.iporaveparaguay.workers.dev/api/pizarron`

**Cómo funciona:**
- Cada agente Python publica un `POST` con qué hizo
- Cualquier agente puede leer con `GET` qué hicieron los demás
- Claude y el usuario miran el pizarrón para saber el estado global

**Estructura de un registro:**
```json
{
  "agente": "Codex-Solucionador",
  "tarea": "fix-login-mobile",
  "archivos": "public/index.html",
  "resumen": "Reduje padding lcard y font-size title en mobile",
  "estado": "Finalizado",   // Pendiente | Activo | Finalizado | ALERTA-CRITICA | Test
  "validacion": "Pendiente", // Pendiente | OK | Conflicto
  "created_at": "2026-05-14T01:48:29Z"
}
```

**Importante:**
- Los agentes Python usan `User-Agent: IporaveAgent/1.0` (Cloudflare bloquea `Python-urllib`)
- El endpoint GET es **público** (los agentes Python no tienen JWT)
- El endpoint POST acepta `X-Agent-Key` con env `PIZARRON_SECRET` para autenticarse

---

## 🚀 CÓMO ARRANCAR LOS AGENTES

### Arranque normal
```powershell
cd C:\Users\USUARIO\iporave-sistema
.\.agentes\iniciar-todos.ps1
```

Eso lanza:
1. `orquestador-supervisor.py` en una ventana PowerShell
2. `cerebro-monitor.py` en otra ventana PowerShell
3. El supervisor automáticamente lanza los 5 orquestadores + codex-solucionador

### Verificar que arrancaron
```powershell
Get-Process python* | Format-Table Id, ProcessName, StartTime -AutoSize
```
Esperado: **7 procesos** (supervisor + 5 orquestadores + codex-solucionador) + cerebro = **8**.
Si hay Aider corriendo, se suma. Si hay más de 8, hay duplicados.

### Comprobar reportes en el pizarrón
```powershell
$r = Invoke-WebRequest "https://iporave-api.iporaveparaguay.workers.dev/api/pizarron" -UseBasicParsing
($r.Content | ConvertFrom-Json).registros | Select-Object -First 5
```

### Bloqueo de arranque — `PARADA_CRITICA.txt`
Si existe el archivo `.agentes/PARADA_CRITICA.txt`, el script de arranque se niega a iniciar. Es un seguro. Para resetear:
```powershell
Remove-Item C:\Users\USUARIO\iporave-sistema\.agentes\PARADA_CRITICA.txt
```

---

## 🛑 CÓMO DETENERLOS (PARADA DE EMERGENCIA)

### Opción 1 — Matar todo Python (más radical, más seguro)
```powershell
Get-Process python* | Stop-Process -Force
```

### Opción 2 — Matar por PIDs específicos (cuando sabés qué hay)
```powershell
Stop-Process -Id 4140,5388,8008,9512,10560,11712,13028,15532,17168 -Force
```

### Opción 3 — Listar comandos exactos antes de matar
```powershell
Get-WmiObject Win32_Process -Filter "name='python.exe'" | Select-Object ProcessId, CommandLine | Format-List
```

### Verificar que no quedó nada
```powershell
Get-Process python* 2>&1
```
Esperado: **vacío** o "Cannot find process".

### Riesgo conocido al detener Aider en medio de un edit
Si un proceso Aider estaba editando `index.html` y lo matamos, puede dejar el archivo a medio escribir o intacto. Verificar SIEMPRE:
```powershell
cd C:\Users\USUARIO\iporave-sistema; git status; node validate.js
```

---

## 🗂️ ARCHIVOS CLAVE — DÓNDE BUSCAR QUÉ

### Frontend
| Ruta | Para qué |
|---|---|
| `public/index.html` | SPA completa (~10k líneas). Toda la lógica del sistema interno. |
| `public/catalog.html` | Catálogo público sin auth |
| `public/track.html` | Tracking público de pedidos |
| `public/nosotros.html`, `faq.html`, `terminos.html` | Páginas estáticas |
| `validate.js` | **OBLIGATORIO antes de commit a index.html.** Detecta `</script>` sin escapar dentro de strings JS (rompería la SPA entera). |

### Worker (Cloudflare)
| Ruta | Para qué |
|---|---|
| `iporave-worker/src/index.js` | Router principal — todos los endpoints se registran aquí |
| `iporave-worker/src/utils.js` | `verifyToken()`, `corsHeaders()`, `json()`, `getSupaAdmin()` |
| `iporave-worker/src/api/*.js` | Cada endpoint |

### Coordinación de agentes
| Ruta | Para qué |
|---|---|
| `.agentes/PLAYBOOK_SUPERVISOR.md` | Playbook permanente — reglas que no caducan |
| `.agentes/ORQUESTACION.md` | Protocolo de sprints sincronizados (parte 1, 2, 3...) |
| `.agentes/ORQUESTADOR.md` | Lista de tareas vivas — agentes leen de acá |
| `.agentes/iniciar-todos.ps1` | Script de arranque |
| `.agentes/alerts.json` | Log local de alertas críticas del supervisor |
| `.agentes/playwright_state.json` | Sesión guardada del browser para tester-visual.py |
| `.agentes/RELEVO_CLAUDE_*.md` | Handoff de cada sesión (este archivo) |
| `.agentes/TAREA_*.md` | Tareas pendientes documentadas |

### Tareas pendientes (al cierre 2026-05-14)
| Archivo | Prioridad |
|---|---|
| `TAREA_PRUEBA_LANZAMIENTO.md` | **CRÍTICA** — prueba completa antes de lanzamiento mañana |
| `TAREA_MOBILE_UX_FIXES.md` | **ALTA** — botones mobile, padding amarillo, campanita scroll, topbar |
| `TAREA_SCROLL_BTN_VISUAL.md` | Baja — efecto 3D scroll-to-top |
| `TAREA_ASISTENTE_VOZ_IA.md` | Media — voice IA con Groq + Llama 3.3 + Web Speech |
| `TAREA_PEDIDOS_BOTONES_OVERFLOW.md` | Baja — refinamiento visual |
| `TAREA_UI_LOGIN_MOBILE.md` | Baja — bandera PY, título mobile |
| `TAREA_MAPA_MEJORAS.md` | Media — botones mapa, pines prioridad |
| `TAREA_DATOS_PRUEBA_EXTENDIDOS.md` | Media — más datos de prueba |

---

## 📋 ESTADO DE PRODUCCIÓN AL CIERRE

### Versiones desplegadas
| Componente | Commit/Versión | URL |
|---|---|---|
| **Frontend** | `46d0726` (último push) | https://iporave-sistema.vercel.app |
| **Worker** | `528a00c` | https://iporave-api.iporaveparaguay.workers.dev |
| **Repo frontend** | `github.com/iporaveparaguay/iporave-sistema` rama `main` | auto-deploy a Vercel |
| **Repo worker** | `github.com/iporaveparaguay/iporave-worker` rama `master` | deploy manual con wrangler |
| **DB** | Supabase `hrpnqbmknmgdaaokjelb.supabase.co` | RLS activo en 7 tablas |

### Lo que se hizo esta sesión (2026-05-14)
- ✅ Hardening del worker — ronda 1 + 2 (rate limits, security headers, validaciones)
- ✅ XSS fixes en frontend (~30 puntos): textContent en pushNotif, escHtml en chats/PDFs, safeUrl en imgs
- ✅ Mapa profesional (commit `6b2ad15`): clase `.map-btn`, pines de prioridad animados (shake + sonar)
- ✅ Menú ⋮ uniforme en pedidos, usuarios, catálogo (commits `533854a`, `79d5e2b`)
- ✅ Botón Navegar azul (no más rojo) en 4 lugares (commit `67d97ec`)
- ✅ ⚡ Botón "Marcar prioridad" en dropdown de pedidos (commit `67d97ec`)
- ✅ Push notification al delivery cuando pedido se marca prioritario (commit `67d97ec`)
- ✅ **Columna `prioridad boolean` agregada a tabla `pedidos`** (SQL manual ejecutado por usuario)
- ✅ Scroll-to-top funcional (commit `845e38a`) — falta efecto visual
- ✅ Re-auth con password en Config y SQL (commit `5524c30`) — 5 min de gracia
- ✅ Fix drag vs click en botón flotante IA (commit `dac3b9c`)
- ✅ Push a GitHub completado — Vercel deployó todo
- ✅ Plan de prueba pre-lanzamiento guardado (`TAREA_PRUEBA_LANZAMIENTO.md`)
- ✅ Fixes UX mobile anotados (`TAREA_MOBILE_UX_FIXES.md`)
- ✅ Agentes detenidos en parada de emergencia limpia

### Lo que NO se hizo (pendiente)
- ⚠️ Los Aider que estaban editando `index.html` fueron cortados → los 3 bugs siguen vivos:
  1. Campanita (`codexNotifBell`) aparece antes del login
  2. `#bgWrap` (barra de búsqueda) tapa botones cuando está en el topbar
  3. Login mobile — título "Iporave Connect" se sale del recuadro `.lcard` en 375px
- ⚠️ Vercel CLI token expirado — auto-deploy desde GitHub funciona, pero `vercel --prod` directo falla. Si se necesita: `vercel login`
- ⚠️ `WHATSAPP_APP_SECRET` no configurado: `cd iporave-worker; npx wrangler secret put WHATSAPP_APP_SECRET`
- ⚠️ Isidro (admin) tiene que re-tap el botón de notif push para resubscribirse
- ⚠️ Orphan cleanup en Supabase (SQL en sección 5 del RELEVO viejo)

---

## 📅 PLAN PARA LA PRÓXIMA SESIÓN (2026-05-15)

**Contexto crítico:** Mañana a la tarde el usuario reparte usuarios+contraseñas a ~10 personas reales. Antes de eso, prueba completa.

### Orden de trabajo sugerido
1. **Cargar datos ficticios completos** (usar `crear-datos-prueba.py` o ampliarlo):
   - 2 vendedores, 2 deliveries, 1 dropshipper, 1 empresa
   - 5+ pedidos en estados variados (uno con ⚡ prioridad)
   - 8 productos con foto
   - TODOS los campos de cada pedido completos (teléfono, dirección, ref, etc.)

2. **Fixes UX mobile** (de `TAREA_MOBILE_UX_FIXES.md`):
   - Botón ⋮ a la derecha en cards de pedido
   - Padding izquierdo uniforme (igual a Liquidación) en Balance, Usuarios, Zona/Entrega, Catálogo
   - Topbar mobile: título arriba, hamburguesa ☰ abajo-izquierda contra separador
   - Campanita: hacerla más chica, efecto transparencia al scroll down

3. **Fixes pendientes de los Aider cortados:**
   - Ocultar `codexNotifBell` antes del login
   - `#bgWrap` fuera del topbar, position:fixed
   - Login mobile padding/font reducidos

4. **Correr tester-visual.py** para screenshots + análisis Gemini:
   ```powershell
   python .agentes/tester-visual.py --user iporaveparaguay@gmail.com --pass ivan12345
   ```

5. **Probar manualmente** todos los roles según `TAREA_PRUEBA_LANZAMIENTO.md`

### Cómo lanzar agentes para esto
**SOLO si el usuario lo pide explícitamente.** Sugerencia de delegación:
- **Codex** → fixes CSS mobile (zonas claras, no toca auth)
- **Aider** → fixes muy puntuales con prompt específico (campanita, bgWrap, login mobile)
- **Claude (vos)** → datos ficticios (script Python), supervisión, fixes críticos
- **Tester-visual.py** → screenshots automatizados al final

---

## 🧱 SCHEMA REAL DE TABLAS SUPABASE (VERIFICADO)

**Las columnas que listo son las que existen. No agregues otras.**

### `pedidos`
- `id, cliente (TEXT), drop_id, vendedor_id, delivery_id, estado, address, prioridad (boolean), …`
- **NO existen:** `cliente_id` (es texto directo), `dropshipper_id` (se llama `drop_id`)

### `usuarios`
- `id, username, email, rol, auth_id, nombre, estado_cuenta, created_by, whatsapp, telefono, foto_perfil, foto_cedula_frente, foto_cedula_dorso, vehiculo, patente, nombre_comercial, ruc, logo, descripcion_negocio, banco, tipo_cuenta, nro_cuenta, titular_cuenta, wallet_tipo, wallet_nro, wallet_alias, …`
- **NO existen:** `created_at`, `creado_at` (solo `created_by` que es FK)

### `dispositivos`
- `id, username, device_hash, ip, autorizado, token_aprobacion, token_expires_at, aprobado_at, autorizado_at, creado_at`
- **NO existen:** `usuario_id`, `nombre`, `dispositivo_info`

### `mensajes`
- `de_id, de_nombre, para_id, mensaje, …`
- **NO existen:** `de` (texto), `para` (texto)

### `catalogo`
- Precios en columna `presentaciones` (JSON array). **NO hay columna `precio`.**
- Descripción en `descripcion_html`. **NO `descripcion`.**

### `pizarron`
- `id, agente, tarea, archivos, resumen, estado, validacion, created_at`

---

## 🔄 WORKFLOW DE FIX → DEPLOY (estándar de oro)

```
1. Read el archivo que vas a modificar
2. Edit con cambio mínimo focalizado
3. node validate.js   (solo si tocaste index.html)
4. git add <archivo específico>   ← NO git add . ni -A
5. git commit -m "fix: descripción concreta"
6. git push origin main           ← dispara auto-deploy Vercel
7. Smoke test con curl al endpoint o ver Vercel deployment
8. Si rompe: wrangler tail / vercel logs → fix → repetir
```

**Worker:**
```powershell
cd C:\Users\USUARIO\iporave-worker
git add src/api/archivo.js
git commit -m "fix: descripción"
npx wrangler deploy --minify   ← deploy explícito, no es auto
```

**Frontend:**
```powershell
cd C:\Users\USUARIO\iporave-sistema
node validate.js   # OBLIGATORIO para index.html
git add public/index.html
git commit -m "fix: descripción"
git push origin main   ← Vercel deploya automáticamente
```

---

## ⚠️ ERRORES COMUNES (evitar repetir)

1. **Asumir columnas que no existen.** Supabase ignora silenciosamente columnas desconocidas en UPDATE, pero falla en SELECT. Siempre verificar.
2. **`</script>` dentro de strings JS en `index.html`.** Rompe toda la SPA. Dividir como `'<scr'+'ipt>'`.
3. **Saltar `node validate.js`.** Solo se descubre el bug en producción cuando ya rompió todo.
4. **Dos agentes editando el mismo archivo.** Conflicto git garantizado. Coordinar via pizarrón antes.
5. **Agregar auth admin al GET de `/api/pizarron`.** Rompe el supervisor Python (no tiene JWT).
6. **Caracteres Unicode decorativos en SQL para Supabase Editor.** Box-drawing rompe el parser.
7. **Heredocs estilo `<<EOF` en PowerShell.** No funcionan. Usar `@'...'@` o archivo temporal.
8. **`select('*')` deja escapar tokens y secretos.** Listar columnas explícitas (pero verificadas).
9. **`git add .` / `-A`.** Trae archivos sensibles sin querer. Listar archivos específicos.
10. **Re-lanzar agentes sin orden del usuario.** Sesión anterior cerró con parada de emergencia explícita.

---

## 💬 ESTILO DE COMUNICACIÓN CON EL USUARIO

- **Idioma:** español rioplatense/paraguayo, siempre.
- **Tono:** directo, conciso, sin jerga innecesaria.
- **Si el user dice "modo automático" o "permiso total":** trabajar a fondo sin pedir confirmaciones extra, **pero respetar líneas rojas**.
- **Si el user dice "esto es para después, no reacciones":** GUARDAR la info en un `TAREA_*.md`, commitear, y NO ejecutar nada.
- **Si el user dice "dame X minutos":** no lanzar tareas que requieran su atención. Hacer trabajo silencioso (docs, audits seguros).
- **Permisos de Claude Code en inglés:** TRADUCIR las opciones al español ANTES de pedir el permiso. Ejemplo en `CLAUDE.md`.
- **Cuando el user es ambiguo:** preguntar antes de actuar. No interpretar.

---

## 🎁 FEATURES FUTURAS — NO BLOQUEAN LANZAMIENTO

- Correo corporativo con dominio propio (iporave@iporaveparaguay.com)
- API keys propias por cliente: WhatsApp Business, Shopify, Dropi
- Botones de integración en perfil de cliente: Meta Ads, Shopify, Dropi
- Asistente IA con voz (Web Speech API + Groq + Llama 3.3 70B)
- Mapbox V6 (reemplazar Leaflet)
- Tienda online pública con auto-registro
- Rol "empresa" — sub-admin mejorado
- Plan Google One — explorar beneficios

---

## 📞 RECURSOS Y CONTACTOS

- **Cuenta del negocio:** iporaveparaguay@gmail.com (Shopify, admin)
- **Cuenta Claude:** iporave@gmail.com (esta sesión)
- **Supabase Project:** `hrpnqbmknmgdaaokjelb`
- **Cloudflare Worker:** `iporave-api` (account: iporaveparaguay)
- **Vercel Project:** `iporave-sistema` (auto-deploy desde GitHub)
- **API Keys (locales):** `C:\Users\USUARIO\node-red-config\api-keys.json` (NO en git)

---

## 🏁 ÚLTIMA COSA — CHECKLIST DE PRIMER MENSAJE

Cuando saludes al usuario en la próxima sesión, hacé esto en este orden:

1. Confirmar en español que leíste el RELEVO
2. Reportar estado: commits, procesos Python (debería ser 0), última entrada del pizarrón
3. Listar las 3 tareas más críticas para el día (mobile UX, datos ficticios, prueba)
4. **Preguntar qué arrancamos primero. NO lanzar agentes solo.**

Ejemplo:

> Hola. Leí el RELEVO completo. Estado actual:
> - Frontend en commit `46d0726`, todo deployado en Vercel
> - 0 procesos Python (parada limpia)
> - Última entrada del pizarrón: hace XX horas, sin actividad nueva
>
> Las 3 prioridades de hoy según lo que dejaste anotado:
> 1. Cargar datos ficticios completos para prueba (TAREA_PRUEBA_LANZAMIENTO.md)
> 2. Fixes UX mobile — botones, padding, topbar, campanita (TAREA_MOBILE_UX_FIXES.md)
> 3. Probar manualmente todos los roles antes de entregar a las 10 personas
>
> ¿Por dónde arrancamos? ¿Querés que prepare los datos ficticios con un script o que primero levante los agentes?

---

*Documento de relevo generado al cierre de sesión 2026-05-14. Próxima sesión: leerlo entero antes de tocar nada.*
