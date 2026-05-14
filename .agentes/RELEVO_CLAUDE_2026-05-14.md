# RELEVO COMPLETO — Claude → próxima sesión
**Fecha:** 2026-05-14  
**Sesión:** Auditoría de seguridad / hardening masivo + UX fixes + tester visual  
**Estado al cierre:** CERRADO — commits deployados, pendientes documentados

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
- **Worker:** último commit del día (hardening ronda 2: config, pizarron, notif-entrega, catalog-public, orders, push-subscribe, order-status, mensajes genéricos + supabase-js ^2.105.4)
- **Frontend:** commit `6b2ad15` — mapa profesional, menú ⋮ en usuarios, pines prioridad animados

> Nota: correr `git log --oneline -5` en cada repo al inicio de la próxima sesión para confirmar hashes exactos.

---

## 2. QUÉ SE COMPLETÓ EN ESTA SESIÓN (2026-05-14)

### Worker — ronda 1 (deployados temprano):
| Fix | Descripción |
|---|---|
| Rate limits x6 | claude(20/min), geocode(30/min), orders(30/hr), resolve-link(10/min), route(20/min), upload(30/hr) |
| save-user: auth_id | Protegido contra sobreescritura por admin — impide secuestro de cuenta |
| Security headers | X-Content-Type-Options, X-Frame-Options, Referrer-Policy en `corsHeaders()` de utils.js |
| 7 archivos legacy borrados | ai-chat, analytics-admin, auto-registro, boletas, delivery-ubicacion, order-status-logs, whatsapp-config |
| User-Agents unificados | Todos los .agentes/*.py usan `IporaveAgent/1.0` |

### Worker — ronda 2 — hardening adicional (todos deployados):
| Fix | Archivo | Descripción |
|---|---|---|
| Acceso restringido a admin/superadmin | `config.js` | Endpoint bloqueado para roles no privilegiados — ALTA seguridad |
| Fail-safe POST pizarrón | `pizarron.js` | Responde error claro cuando PIZARRON_SECRET no está configurado en vez de romper |
| Validar pedido_id existe | `notif-entrega.js` | Evita insertar notificaciones con FK inválida |
| Rate limit catálogo público | `catalog-public.js` | 60 req/min por IP |
| Validar delivery_id y rol | `orders.js` | Verifica que delivery_id exista y sea rol `delivery` antes de asignar |
| Prevenir endpoint takeover | `push-subscribe.js` | Sanitización de suscripciones push |
| Whitelist estados delivery | `order-status.js` | Solo estados permitidos para el rol delivery |
| Mensajes de error genéricos | `save-user.js`, `delete-user.js`, `get-users.js`, `dispositivos-pendientes.js` | Evita filtrar info interna en errores |
| Actualización dependencia | `package.json` | `@supabase/supabase-js` actualizado a `^2.105.4` |

### Frontend — ronda 1 (pusheados a Vercel):
| Fix | Descripción |
|---|---|
| XSS showAlert/pushNotif | textContent en vez de innerHTML |
| safeUrl() helper | Validación http/https para todos los img src |
| safeUrl x15 puntos | catálogo, usuarios, delivery, entregas, galerías, etc. |
| notifHistory escHtml | `n.msg` escapado en panel de notificaciones |
| bgWrap → fbar | Buscador movido a .fbar inline, #fSrch eliminado |
| catalog.html safeUrl | Grilla y modal de catálogo público |
| escHtml x7 críticos | chat, renderTable, dlvCard, track-public, renderProds, autocomplete, chat-send |

### Frontend — ronda 2 (pusheados hoy):
| Fix | Descripción |
|---|---|
| localStorage cleanup en logout | `doLogout()` limpia todos los keys de localStorage al cerrar sesión |
| Regresión showAlert | Se corrigió uso de innerHTML que se había introducido — vuelve a textContent |
| Fix cleanup realtime + deleteUser | Limpieza correcta de suscripción realtime + validación de `.ok` en deleteUser |

### Scripts de agentes creados/actualizados (en `.agentes/`):
| Archivo | Descripción |
|---|---|
| `tester-visual.py` | Tester visual automatizado con Playwright + Gemini Vision para revisar UI — **actualizado** (ver Sección 2B) |
| `crear-datos-prueba.py` | Crea usuarios/productos/pedidos de prueba en la base de datos |
| `TAREA_DATOS_PRUEBA_EXTENDIDOS.md` | Plan de datos extendidos para cubrir más escenarios de prueba en futuras sesiones |
| `playwright_state.json` | Estado guardado del browser autenticado — contiene sesión activa (anon key + JWT del usuario) |
| `TAREA_MAPA_MEJORAS.md` | Mejoras visuales mapa: botones, pines, nombres visibles sobre el mapa |
| `TAREA_ASISTENTE_BTN_CLICK.md` | Bug drag vs click en #aiBtn — **YA RESUELTO en commit dac3b9c** |
| `TAREA_ASISTENTE_VOZ_IA.md` | Asistente IA con voz — Groq+Llama 3.3+WebSpeech API |

### Supabase (usuario aplicó manualmente):
- RLS activo en 7 tablas: pedidos, usuarios, mensajes, catalogo, cupos, calificaciones, dispositivos
- Funciones helper: `my_id()`, `my_rol()`
- Orphans: 1 usuario + 6 dispositivos — SQL para borrar está listo (ver Sección 5)

---

## 2B. CAMBIOS DEPLOYADOS — RONDA TARDE (2026-05-14)

### Commit `1992f33` — `fix: notificar errores de API al usuario con pushNotif`
| Función | Cambio |
|---|---|
| `saveUser` | Muestra toast de error cuando falla Supabase (antes solo `console.warn`) |
| `saveOrder` | Ídem |
| `saveJornada` | Ídem |

**Impacto:** El usuario ahora ve errores visibles en pantalla en vez de que fallen silenciosamente.

---

### Commit `533854a` — `fix: eliminar campana duplicada + botones pedidos con menú desplegable`

Este commit incluye DOS fixes corridos en paralelo:

#### Fix A — Campanita duplicada
| Cambio | Detalle |
|---|---|
| Eliminado `#ntBell` | Bell vieja del topbar con SVG sin color — borrada |
| Solo queda `codexNotifBell` | Campanita flotante amarilla 🔔, `position:fixed` — es la única ahora |
| CSS actualizado | `#codexNotifBell` oculta en login, visible solo cuando `#appScreen.show` |
| `pushNotif()` ampliado | Ahora también alimenta `_notificaciones[]` y llama `_notifSessionRender()` |
| `_notifSessionMarkAllRead()` | También limpia `_notifHistory` y `_notifUnread` |

#### Fix B — Botones pedidos con menú ⋮
| Cambio | Detalle |
|---|---|
| 8 botones de acción reemplazados | Ver, Editar, WA, GPS, IVA, etc. → botón único `⋮` |
| Dropdown al click | Todas las opciones organizadas en menú desplegable |
| Nuevo CSS | `.order-menu-btn`, `.order-dropdown`, `.order-dropdown.open`, `.od-sep` |
| Nuevas funciones JS | `_toggleOrderMenu(e, id)`, `_closeOrderMenus()` |
| Click-fuera-cierra | Listener global para cerrar dropdown al hacer click fuera |

---

## 2E. COMMITS ADICIONALES — SEGUNDA MITAD DE SESIÓN (2026-05-14)

### Commit `845e38a` — scroll-to-top
- Color neutro (no llamativo)
- Posición `bottom:130px` para no solapar con otros elementos
- Detecta correctamente el contenedor con scroll (no siempre `window`)

### Commit `5524c30` — re-autenticación en Config y SQL
- Modal con `signInWithPassword` antes de entrar a `/config` y sección SQL
- Gracia de 5 minutos tras verificar — no vuelve a pedir en ese lapso
- Evita que roles no privilegiados accedan a settings/secrets

### Commit `dac3b9c` — fix drag vs click en `#aiBtn` + `#bgWrap`
- `#aiBtn` (botón flotante IA) ahora distingue drag de click usando `pointerCapture`
- `#bgWrap` (fondo decorativo) oculto en la pantalla de login

### Commit `8c135e8` — XSS safeUrl + escHtml + UX pedidos
| Cambio | Detalle |
|---|---|
| `safeUrl()` en img src | foto_perfil, cédulas, logos — previene XSS vía URLs de imagen |
| `escHtml()` en PDF | `exportOrdersPDF()` e `imprimirGuia()` |
| Botón ⋮ táctil | Área de toque aumentada a 44px |
| `confirm()` mejorado | Ahora incluye el número de pedido para evitar errores |

### Commit `6b2ad15` — mapa profesional + menú ⋮ usuarios + pines prioridad
| Cambio | Detalle |
|---|---|
| Clase `.map-btn` | Botones del mapa con estilo uniforme teal/cyan |
| Menú ⋮ en tabla usuarios | Igual que en pedidos — acciones en dropdown |
| Pines de prioridad | Animación `shake` + efecto sonar para pedidos marcados como prioridad |

---

## 2C. SCRIPTS ARREGLADOS (no en git — carpeta `.agentes/`)

### `tester-visual.py` — cambios importantes
| Antes | Ahora |
|---|---|
| Usaba `page.goto()` para navegar a pantallas post-login | Usa `page.evaluate("nav('seccion')")` — respeta el SPA |
| Perdía sessionStorage al cambiar URL | sessionStorage se mantiene entre navegaciones internas |
| Sin mapeo de rutas | Mapeo URL → sección: `/usuarios`→`nav('usuarios')`, `/pedidos`→`nav('orders')`, etc. |
| Sin persistencia de sesión | Guarda `playwright_state.json` tras login exitoso |

**Comando de ejecución:**
```bash
python .agentes/tester-visual.py --user iporaveparaguay@gmail.com --pass ivan12345
```

---

## 2D. DATOS DE PRUEBA INSERTADOS HOY

### Pedidos nuevos (IDs 4–7):
| ID | Cliente | Dirección | Tipo |
|---|---|---|---|
| #4 | Carlos Benítez | "Barrio Las Mercedes, frente a la cancha" | Nombre de lugar |
| #5 | Sofía Martínez | "-25.2867,-57.6471" | Coordenadas GPS |
| #6 | Diego Ramírez | "Av. Eusebio Ayala 1234, Asunción, Paraguay" | Dirección completa |
| #7 | Laura Fernández | "Casa" | Mínimo/ambiguo |

### Catálogo nuevos (IDs 10–12):
| ID | Producto | Categoría | Stock | Precio |
|---|---|---|---|---|
| #10 | Lavandina 2L | Limpieza | 80 | 6500 |
| #11 | Auriculares Bluetooth | Tecnología | 15 | 85000 |
| #12 | Remera Algodón | Indumentaria | 40 | M:35000 / L:38000 |

**Estado actual DB (actualizado al cierre):**
- 7 pedidos en total (#1–#7)
- Catálogo: IDs activos 1, 2, 3, 10, 11, 12 — **duplicados IDs 4–9 fueron eliminados**
  - #1 Yerba Mate 1kg
  - #2 Aceite Cañuelas 900ml
  - #3 Azúcar 1kg
  - #10 Lavandina 2L
  - #11 Auriculares Bluetooth
  - #12 Remera Algodón

---

## 3. TRABAJO EN CURSO — AGENTES CORRIENDO AL CIERRE

**Todos los agentes completaron. No hay trabajo en curso al cierre de esta sesión.**

### ✅ Agente A — track.html XSS fixes — COMPLETADO
- Commit `8f13cec`: esc() y safeUrl() aplicados en track.html

### ✅ Agente B — index.html 6 XSS fixes — COMPLETADO
- Commit `ad8422b`: filtrarBoletas, _renderChips, _shareDrop, _renderPresForm, renderOrderChat, lista mensajes

### ✅ Agente C — views/js scan — COMPLETADO
- views/, js/, components/ — todos limpios (sin hallazgos)
- Encontró XSS adicionales en `_boletaHTML()` y `imprimirTicket()` → delegados al Agente D

### ✅ Agente D — _boletaHTML + imprimirTicket + campanita — COMPLETADO
- Commit `e0910f6`: escHtml en _boletaHTML y imprimirTicket, guard _updateBell() pre-login

### ✅ Agente E — Errores API visibles (ronda tarde) — COMPLETADO
- Commit `1992f33`: pushNotif en saveUser, saveOrder, saveJornada

### ✅ Agente F — Campanita única + menú pedidos ⋮ (ronda tarde) — COMPLETADO
- Commit `533854a`: elimina #ntBell duplicada, dropdown ⋮ en botones de pedidos

---

## 4. TAREAS PENDIENTES CONOCIDAS (por orden de prioridad)

### ALTA PRIORIDAD

- [x] ~~**Contraseña para acceder a Config/SQL**~~ — **RESUELTO en commit `5524c30`** (modal re-auth + 5 min de gracia)
- [ ] **Agregar columna `prioridad` (boolean) a tabla `pedidos` en Supabase** — sin esto los pines de prioridad no funcionan en producción. SQL: `ALTER TABLE pedidos ADD COLUMN prioridad boolean DEFAULT false;`
- [ ] **Notificación push al delivery cuando pedido marcado como prioridad** — implementar en worker (backend)
- [ ] **Correr tester visual** para verificar pantallas reales post-login
  - `playwright_state.json` guardado, login funciona en tester (SPA navigation corregida)
  - Comando: `python .agentes/tester-visual.py --user iporaveparaguay@gmail.com --pass ivan12345`

### SEGURIDAD — media prioridad

- [ ] **UI login — campanita antes de auth** (TAREA_UI_LOGIN_MOBILE.md): revisar si `codexNotifBell` se crea antes del auth check. Buscar en `updateNavBadges()` o render del topbar — agregar `if(!CU)return;` o condición equivalente. Archivo: `public/index.html`
- [ ] **WHATSAPP_APP_SECRET** (usuario pendiente): `cd iporave-worker && npx wrangler secret put WHATSAPP_APP_SECRET`
- [ ] **Isidro debe re-tap botón de notificaciones push** — las push pueden no llegar

### MEDIA PRIORIDAD — UX

- [ ] **Asistente IA con voz** (ver `TAREA_ASISTENTE_VOZ_IA.md`)
  - Web Speech API para entrada/salida (gratis, nativo del browser)
  - Groq + Llama 3.3 70B para interpretación (gratis)
  - Pipeline: Escuchar → Entender → Extraer campos → Confirmar faltantes → Guardar
  - Botón flotante 🎙️ en la app post-login

- [ ] **Legibilidad nombres en mapa** — texto negro oscuro con letras blancas poco visible cuando estado="En camino". Ver `TAREA_MAPA_MEJORAS.md`

- [ ] **Botón ℹ️ del mapa** — posicionamiento puede seguir descentrado (verificar en producción)

- [ ] **Refinamiento visual botones pedidos** (ver `TAREA_PEDIDOS_BOTONES_OVERFLOW.md`)
  - Colores, eliminar borde redondo pequeño en esquina
  - Uniformar con el nuevo estilo de usuarios

- [ ] **Uniformar botones en catálogo y otras secciones** — después de usuarios (ya hecho)

### TESTING / QA

- [ ] **Prueba visual completa con `tester-visual.py`** — datos de prueba ya cargados. Ejecutar y revisar screenshots + análisis de Gemini Vision.
- [ ] **Mejoras visuales** — aplicar sugerencias del reporte de Gemini Vision tras correr el tester.

### BAJA PRIORIDAD / UI/UX (ver TAREA_UI_LOGIN_MOBILE.md)

- [ ] Bandera Paraguay en mobile: posicionar junto a título con 0.5-1cm separación
- [ ] Título más grande en mobile

### BAJA PRIORIDAD — DATOS

- [x] ~~**Limpiar duplicados en catálogo**~~ — **RESUELTO**: IDs 4–9 eliminados. Activos: 1, 2, 3, 10, 11, 12.

### Funcionalidades pendientes (futuras)

- [ ] WhatsApp webhook — `npx wrangler secret put WHATSAPP_APP_SECRET` + validación FROM (reconstruir con tabla `pedidos` real)
- [ ] Tienda online pública (registro cliente externo, carrito, pago)
- [ ] Mapbox V6 (reemplazar Leaflet) — después de GPS/tracking completo
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
| Rate limits | Todos los endpoints del worker (incluyendo catalog-public 60/min) |
| XSS críticos index.html | ~30 puntos corregidos |
| XSS catalog.html | safeUrl aplicado |
| XSS track.html | esc() y safeUrl() aplicados (Agente A ✅) |
| XSS index.html ronda 2 | filtrarBoletas, _renderChips, _shareDrop, etc. (Agente B ✅) |
| XSS _boletaHTML + imprimirTicket | escHtml aplicado (Agente D ✅) |
| views/js scan | views/, js/, components/ — limpios (Agente C ✅) |
| auth_id protegido | save-user.js |
| Security headers | X-Frame-Options, nosniff, Referrer-Policy |
| Legacy code | 7 archivos Express eliminados |
| SSRF resolve-link | Whitelist de dominios Google Maps |
| whatsapp-webhook | HMAC SHA-256 |
| pizarron POST | fail-safe cuando PIZARRON_SECRET no configurado |
| track-public | Datos sensibles removidos de respuesta |
| claude proxy | Modelo fijo + cap max_tokens |
| config.js | Restringido a admin/superadmin |
| orders.js | Valida delivery_id y rol delivery |
| notif-entrega.js | Valida que pedido_id exista |
| push-subscribe.js | Previene endpoint takeover |
| order-status.js | Whitelist estados para delivery |
| Mensajes error genéricos | save-user, delete-user, get-users, dispositivos-pendientes |
| localStorage cleanup | doLogout() limpia todo el localStorage |
| Regresión showAlert | Corregida — vuelve a textContent |
| Realtime cleanup + deleteUser | Fix suscripción + validación .ok |
| @supabase/supabase-js | Actualizado a ^2.105.4 |

### ✅ CERRADO — RONDA TARDE (agregados hoy)
| Área | Detalle |
|---|---|
| Errores API visibles | saveUser, saveOrder, saveJornada muestran toast en vez de fallar silenciosamente |
| Campanita duplicada eliminada | Solo queda `codexNotifBell` flotante amarilla, `#ntBell` borrada |
| CSS campanita en login | `codexNotifBell` oculta en login, visible solo con `#appScreen.show` |
| Sincronización notificaciones | pushNotif() ahora alimenta tanto _notificaciones[] como _notifHistory[] |
| Botones pedidos → menú ⋮ | 8 botones de acción reemplazados por dropdown organizado |

### ✅ CERRADO — SEGUNDA MITAD DE SESIÓN
| Área | Commit | Detalle |
|---|---|---|
| Scroll-to-top | `845e38a` | Color neutro, bottom:130px, detecta contenedor correcto |
| Re-auth Config/SQL | `5524c30` | Modal signInWithPassword + 5 min gracia |
| Fix drag vs click #aiBtn | `dac3b9c` | pointerCapture para distinguir drag de click; #bgWrap oculto en login |
| XSS safeUrl img src | `8c135e8` | foto_perfil, cédulas, logos — previene XSS vía URL |
| XSS escHtml PDF | `8c135e8` | exportOrdersPDF + imprimirGuia |
| UX botón ⋮ táctil | `8c135e8` | 44px área de toque |
| confirm() con nro pedido | `8c135e8` | Evita errores de confirmación |
| Mapa profesional | `6b2ad15` | Clase .map-btn, colores teal/cyan |
| Menú ⋮ usuarios | `6b2ad15` | Dropdown en tabla de usuarios |
| Pines prioridad animados | `6b2ad15` | shake + sonar en pedidos prioritarios |
| Duplicados catálogo | — | IDs 4–9 eliminados de DB |

### 🔄 EN CURSO
Ninguno — todos los agentes de la sesión completaron.

### ❌ PENDIENTE
| Área | Prioridad |
|---|---|
| Columna `prioridad` en tabla `pedidos` (Supabase) | ALTA — sin esto pines no funcionan en producción |
| Push al delivery cuando pedido es prioridad | ALTA |
| Prueba visual con tester-visual.py | ALTA — PRÓXIMA SESIÓN |
| campanita antes del auth (codexNotifBell pre-login) | MEDIA |
| WHATSAPP_APP_SECRET | MEDIA (usuario) |
| Asistente IA con voz (TAREA_ASISTENTE_VOZ_IA.md) | MEDIA |
| Legibilidad nombres en mapa (estado "En camino") | MEDIA |
| Botón ℹ️ mapa — posicionamiento | MEDIA |
| Refinamiento visual botones pedidos | MEDIA |
| Mejoras visuales según análisis Gemini | DESPUÉS del tester |

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
| `iporave-sistema/.agentes/playwright_state.json` | Estado del browser autenticado — sesión guardada post-login |
| `C:\Users\USUARIO\node-red-config\api-keys.json` | API keys de Groq, Gemini, etc. (NO en git) |

---

## 11. NOTAS DE CONTEXTO TÉCNICO (ronda tarde)

- **`sessionStorage` se pierde al recargar** → el tester visual ahora usa `page.evaluate("nav('seccion')")` en vez de `page.goto()` para navegar dentro del SPA post-login.
- **`_notificaciones[]`** = push notifications (ServiceWorker) — la nueva campanita usa esto.
- **`_notifHistory[]`** = notificaciones in-app generadas por `pushNotif()` — ahora ambos arrays se sincronizan.
- **`playwright_state.json`** contiene el localStorage del browser guardado (incluyendo Supabase access token). El token se regenera cada hora — para scripts usar anon key + JWT propio del usuario.
- **`codexNotifBell`** es la única campanita ahora — la vieja `#ntBell` del topbar fue eliminada definitivamente en commit `533854a`.
- **Supabase access token caduca cada 1 hora** — si el tester falla con 401, re-ejecutar para hacer login fresco y guardar nuevo `playwright_state.json`.

### Estado de infraestructura al cierre
| Componente | Estado |
|---|---|
| Worker | `iporave-api.iporaveparaguay.workers.dev` — activo |
| Frontend | `iporave-sistema.vercel.app` — commit `6b2ad15` deployado |
| Supabase | `hrpnqbmknmgdaaokjelb.supabase.co` — RLS activo en 7 tablas |
| Node-RED + Groq | Operativo (pizarrón, supervisor) |
| `playwright_state.json` | Guardado en `.agentes/` — login funciona, SPA navigation corregida (page.evaluate) |
