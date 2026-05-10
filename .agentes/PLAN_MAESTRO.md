# 🏛️ PLAN MAESTRO — IPORÃVE CONNECT
# Director Técnico: Claude Code
# Última actualización: 2026-05-10
#
# PRINCIPIO FUNDAMENTAL:
# Despacio y seguro vale más que rápido y roto.
# Cada Sprint es pequeño, verificable y 100% reversible con git revert.

---

## 1. CÓMO FUNCIONA — El ciclo completo

```
┌─────────────────────────────────────────────────────────────┐
│  Claude Code escribe la tarea exacta del Sprint             │
│  (archivo TAREA_SPRINT_X_AGENTE.md)                         │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Todos los agentes del Sprint trabajan EN PARALELO          │
│  cada uno en su zona asignada — sin pisarse                 │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  Cada agente al terminar:                                   │
│  1. node validate.js (si tocó index.html)                   │
│  2. POST /reporte → Node-RED                                │
│  3. Ollama pre-valida → Groq supervisa → Cerebras fallback  │
│  4. VALIDADO → espera a los demás                           │
│  5. CONFLICTO → stop.flag → Claude Code interviene          │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  GATE — todos completan su tarea del Sprint                 │
│  Claude Code revisa integración                             │
│  Usuario prueba en el navegador                             │
│  → Funciona: git commit + avanzar al Sprint siguiente       │
│  → Falla: agente corrige, vuelve al inicio del ciclo        │
└─────────────────────────────────────────────────────────────┘
```

**Regla de oro:** Nadie hace commit hasta que el usuario confirma que funciona.
**Regla de oro 2:** Nadie empieza Sprint N+1 hasta que Gate N está aprobado.
**Regla de oro 3:** Si un agente alcanzó su límite → se pausa, los demás continúan, el Gate espera.

---

## 2. AGENTES — Modelos, límites y fallbacks

### Agentes de código (hacen el trabajo)

| Agente | Modelo base | Límite aprox. | Fallback si alcanza límite |
|---|---|---|---|
| **Claude Code** | Claude Sonnet 4.6 | Por sesión | Nueva sesión (contexto en memoria) |
| **Codex** | Propio | Por sesión/día | Aider toma sus tareas |
| **Antigravity** | Propio | Por sesión/día | Plandex toma sus tareas |
| **Aider** | Cerebras (primario) | Generoso | Cambia a Groq automático |
| **Plandex** | Configurable | Sin límite fijo | — (WSL, tareas largas) |

### Modelos de supervisión (Node-RED)

| Modelo | Límite | Fallback automático |
|---|---|---|
| **Ollama** (pre-check) | Sin límite — local | — (siempre disponible) |
| **Groq** (supervisor) | ~14.400 req/día | → Cerebras automático |
| **Cerebras** (fallback) | Generoso — free tier | → Ollama si falla |

### Modelos de consulta (análisis, no código sensible)

| Modelo | Uso permitido | Límite |
|---|---|---|
| **Kimi 128k** | Leer archivos grandes, análisis | Mensual |
| **DeepSeek** | Razonamiento complejo | Diario |
| **OpenRouter** | Consultas generales únicamente | Por modelo |

---

## 3. PROTOCOLO DE LÍMITE ALCANZADO

Cuando un agente llega a su límite durante un Sprint:

### Paso 1 — El agente reporta su estado parcial
```bash
curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"NOMBRE\",\"tarea\":\"SPRINT_X — PAUSADO POR LÍMITE\",
       \"archivos\":\"ruta/archivo\",
       \"resumen\":\"Completado hasta: [describir hasta dónde llegó]. Pendiente: [qué falta]\",
       \"estado\":\"Pausado\"}"
```

### Paso 2 — Quién lo reemplaza
| Agente pausado | Lo reemplaza | Cómo |
|---|---|---|
| **Codex** | Aider | Claude Code escribe tarea específica para Aider |
| **Antigravity** | Plandex (WSL) | Claude Code escribe tarea específica |
| **Aider** | Cambia modelo en config | `model: groq/llama-3.3-70b-versatile` en .aider.conf.yml |
| **Claude Code** | Nueva sesión | Memoria persistente → contexto completo disponible |
| **Groq supervisor** | Cerebras (automático) | Ya configurado en Node-RED |

### Paso 3 — Gate sigue esperando
El Sprint no cierra hasta que TODA la tarea esté completa — ya sea por el agente original (cuando se restaure su límite al día siguiente) o por su reemplazo.

### Paso 4 — Restauración
Cuando el límite se restaura, el agente puede retomar trabajos futuros normalmente. No hace falta que reescriba lo que ya hizo el reemplazo.

---

## 4. ZONAS EN index.html — Nadie entra en zona ajena

```
LÍNEAS 1–2668       → CLAUDE CODE (auth, DL, Supabase, realtime, nav, router)
                       INTOCABLE para todos los demás

LÍNEAS 2669–4888    → CODEX (dashboard, pedidos, balance, liquidación,
                       estadísticas, analíticas, boletas)

LÍNEAS 4889–8200+   → CODEX (usuarios, suministros, zonas, catálogo, mensajes, mapa)

ZONA LIMPIEZA       → AIDER (solo líneas 1541–1633, asignadas por Claude Code)

ARCHIVOS NUEVOS     → ANTIGRAVITY (public/catalog.html, public/register.html, etc.)
                       NUNCA toca index.html existente

IPORAVE-WORKER      → CLAUDE CODE exclusivamente
```

### Archivos VETADOS para todos excepto Claude Code
- `iporave-worker/src/utils.js` → `verifyToken()`
- `iporave-worker/src/api/login.js`
- `iporave-worker/src/api/save-user.js` → `SAFE_SELF_FIELDS`
- Políticas RLS en Supabase (solo vía dashboard manual)

---

## 5. SPRINTS — ORDEN DE TRABAJO

### ▶️ SPRINT 1 — Fundamentos (ACTIVO)
**Gate 1: todos completan → usuario prueba → deploy si ok**

| ID | Agente | Tarea | Zona |
|---|---|---|---|
| 1-A | Claude Code | WhatsApp Webhook (worker) | `iporave-worker/src/` |
| 1-B | Codex | Clientes recurrentes (vendedor) | `index.html` líneas 4889+ |
| 1-C | Antigravity | Catálogo público sin login | `public/catalog.html` nuevo |
| 1-D | Aider | Limpieza código muerto | `index.html` líneas 1541–1633 |

**Prueba Gate 1 (Claude Code le indica al usuario qué probar):**
- WhatsApp Webhook recibe y responde
- Vendedor ve "Clientes Recurrentes" en nav, página carga con datos
- `catalog.html` abre en navegador sin login, muestra productos
- Login, dashboard, pedidos — todo sigue igual

---

### ⏸️ SPRINT 2 — Notificaciones y mensajes (bloqueado hasta Gate 1)

| ID | Agente | Tarea | Zona |
|---|---|---|---|
| 2-A | Claude Code | WhatsApp por cambio de estado pedido | `iporave-worker/src/` |
| 2-B | Codex | Notificaciones in-app badge + lista | `index.html` zona Codex |
| 2-C | Antigravity | Filtros catálogo + detalle producto | `public/catalog.html` |
| 2-D | Aider | Rol empresa — estructura UI | `index.html` zona asignada |

---

### ⏸️ SPRINT 3 — Analítica y seguridad (bloqueado hasta Gate 2)

| ID | Agente | Tarea | Zona |
|---|---|---|---|
| 3-A | Claude Code | Seguridad — migrar zonas al Worker | `iporave-worker/src/` |
| 3-B | Codex | Analítica vendedor ampliada | `index.html` zona Codex |
| 3-C | Antigravity | Carrito + formulario pedido público | `public/catalog.html` |
| 3-D | Aider | Meta Ads — conectar portafolio | `index.html` zona asignada |

---

### ⏸️ SPRINT 4 — Facturación y reportes (bloqueado hasta Gate 3)

| ID | Agente | Tarea | Zona |
|---|---|---|---|
| 4-A | Claude Code | Facturación B2B | `iporave-worker/src/` |
| 4-B | Codex | Reportes exportables por fecha | `index.html` zona Codex |
| 4-C | Antigravity | Auto-registro cliente + aprobación | `public/register.html` nuevo |
| 4-D | Plandex | Shopify — subir productos (tarea larga) | externo |

---

### ⏸️ SPRINT FINAL — Solo cuando producción está estable

| ID | Agente | Tarea |
|---|---|---|
| F-A | Claude Code | Mapbox V6 — reemplazar Leaflet |
| F-B | Codex | Dashboard superadmin mejorado |
| F-C | Antigravity | Login cliente + estado pedido público |

---

## 6. PROTOCOLO DE RESTRUCTURACIÓN — Cuando cambia el equipo disponible

### Cuándo se restructura
Cuando uno o más agentes son reemplazados o quedan fuera por límite,
Claude Code hace una pausa de restructuración **al final del Sprint en curso**
(no en medio — se espera que los activos terminen su tarea chica actual).

### Cómo funciona

```
Agente X alcanza límite → reporta estado parcial al pizarrón
        ↓
Los demás agentes terminan su tarea actual del Sprint
(no se interrumpe lo que están haciendo)
        ↓
Gate parcial: todos los activos reportaron
        ↓
Claude Code analiza:
  - ¿Quiénes quedaron disponibles?
  - ¿Qué tareas quedaron sin terminar?
  - ¿Se puede redistribuir o hay que achicarlo?
        ↓
Claude Code escribe nuevo TAREA_SPRINT_X_RESTRUCTURADO.md
con tareas reasignadas solo entre los agentes disponibles
        ↓
Los agentes activos leen el nuevo plan y continúan
El agente pausado se reincorpora al próximo Sprint cuando su límite se restaure
```

### Reglas de restructuración

1. **No se agranda el trabajo** — si hay menos agentes, hay menos tareas por Sprint
2. **Las tareas no hechas se pasan al Sprint siguiente**, no se acumulan en el actual
3. **Nunca se mezcla trabajo incompleto** — lo que quedó a medias se termina primero o se revierte
4. **Claude Code decide la redistribución** — no los agentes entre ellos
5. **Si quedan menos de 2 agentes activos** → Sprint se hace secuencial (uno a la vez) en vez de paralelo

### Señal para restructurar
Cuando en el pizarrón aparece algún reporte con `"estado": "Pausado"`,
el usuario trae esa información a Claude Code y se dispara el proceso de restructuración.

---

## 8. PROTOCOLO DE EMERGENCIA — Si algo se rompe

### Romper algo en index.html
```bash
# Ver qué cambió
git -C C:/Users/USUARIO/iporave-sistema diff

# Volver al último commit bueno (avisar a Claude Code ANTES)
git -C C:/Users/USUARIO/iporave-sistema revert HEAD
```

### Romper algo en el Worker
```bash
git -C C:/Users/USUARIO/iporave-worker revert HEAD
# El deploy anterior en Cloudflare sigue activo hasta que se vuelva a deployar
```

### Si dos agentes generan conflicto
1. Claude Code decide cuál versión queda
2. El otro agente reescribe su Sprint sobre la versión aprobada
3. No se mezclan manualmente — uno o el otro, nunca los dos mezclados a mano

### Si el stop.flag está activo
```bash
node C:/Users/USUARIO/iporave-sistema/.agentes/check-stop.js
# Si está activo → nadie trabaja → Claude Code revisa y decide
```

---

## 9. INSTRUCCIONES PARA CADA AGENTE ANTES DE EMPEZAR

```
1. node .agentes/check-stop.js          → verificar que no hay stop flag
2. curl http://localhost:1880            → verificar que Node-RED está corriendo
3. Leer CONTEXTO_SISTEMA.md             → contexto completo del sistema
4. Leer PLAN_MAESTRO.md                 → este archivo
5. Leer TAREA_SPRINT_X_TUAGENTE.md     → tu tarea específica
6. Recién entonces empezar
```

---

## 10. CUÁNDO AVISA CLAUDE CODE AL USUARIO

- Gate listo para probar → Claude Code dice exactamente qué probar y cómo
- CONFLICTO detectado por supervisor → Claude Code explica qué pasó
- Límite de agente alcanzado → Claude Code asigna reemplazo
- Antes de cualquier deploy → Claude Code pide aprobación explícita
- Algo necesita decisión de negocio → Claude Code pregunta

**El usuario no tiene que seguir cada Sprint — solo los momentos de prueba y aprobación.**

---

## 11. HISTORIAL DE GATES APROBADOS

| Gate | Fecha | Sprint completados | Aprobado por | Deploy |
|---|---|---|---|---|
| — | — | — | — | — |
