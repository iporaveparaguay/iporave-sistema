# 🎯 ORQUESTACIÓN IPORÃVE — CONTROL CLAUDE CODE
# Claude Code es el Director Técnico. Nadie hace nada sin su aprobación.
# Actualizado: 2026-05-10

---

## CÓMO FUNCIONA

### Sprint sincronizado
1. Claude Code escribe las tareas de cada agente (TAREA_PARTE_X_AGENTE.md)
2. Todos los agentes trabajan en paralelo en su zona asignada
3. Cada agente reporta al pizarrón cuando termina su tarea
4. Node-RED + Groq/Cerebras validan automáticamente
5. Usuario trae el pizarrón a Claude Code
6. Claude Code verifica integración → aprueba o pide corrección
7. Deploy de esa parte
8. Recién entonces empieza la Parte siguiente

### Regla de oro
**NADIE empieza la Parte N+1 hasta que Claude Code aprueba la Parte N.**
Si un agente termina antes que los demás → espera. No sigue solo.

---

## ZONAS — Qué puede tocar cada agente

| Agente | Puede tocar | NUNCA puede tocar |
|---|---|---|
| **Claude Code** | `iporave-worker/src/**` completo | — (tiene acceso total) |
| **Codex** | `index.html` solo en su zona asignada | Auth, verifyToken, DL core, login |
| **Antigravity** | Archivos nuevos en `public/` (catalog.html, etc.) | `index.html` existente |
| **Aider** | `index.html` solo zonas de limpieza definidas | Auth, verifyToken, DL core, login |
| **Plandex** | Worker + Supabase migrations (tareas largas) | Auth core |

### Archivos VETADOS para todos excepto Claude Code
- `iporave-worker/src/utils.js` → verifyToken()
- `iporave-worker/src/api/login.js`
- `iporave-worker/src/api/save-user.js` → SAFE_SELF_FIELDS
- Políticas RLS en Supabase (solo vía dashboard)

---

## PARTES DEL TRABAJO

### ✅ PARTE 1 — Estado: PENDIENTE
Ver archivos: TAREA_PARTE1_CODEX.md | TAREA_PARTE1_ANTIGRAVITY.md | TAREA_PARTE1_AIDER.md

| Agente | Tarea Parte 1 | Estado |
|---|---|---|
| Claude Code | WhatsApp Webhook (worker) | ✅ Finalizado — deployado |
| Codex | Clientes recurrentes vendedor | ⏳ Pendiente |
| Antigravity | Catálogo público sin login (catalog.html) | ⏳ Pendiente |
| Aider | Limpieza código legacy zona 1 (index.html) | ✅ Finalizado — validado |

**Gate Parte 1:** Todos reportan → Claude Code revisa → aprueba → deploy

---

### ⏸️ PARTE 2 — Estado: BLOQUEADA (espera aprobación Parte 1)
| Agente | Tarea Parte 2 |
|---|---|
| Claude Code | WhatsApp mensajes por estado |
| Codex | Notificaciones in-app (badge + lista) |
| Antigravity | Filtros catálogo + detalle producto |
| Aider | Rol empresa — estructura UI |

---

### ⏸️ PARTE 3 — Estado: BLOQUEADA
| Agente | Tarea Parte 3 |
|---|---|
| Claude Code | Seguridad Opción B — migrar data layer |
| Codex | Analítica vendedor ampliada |
| Antigravity | Carrito + formulario pedido |
| Aider | Meta Ads portafolio |

---

### ⏸️ PARTE 4 — Estado: BLOQUEADA
| Agente | Tarea Parte 4 |
|---|---|
| Claude Code | Facturación B2B |
| Codex | Reportes exportables por fecha |
| Antigravity | Auto-registro cliente + aprobación |
| Plandex | Shopify — subir productos |

---

### ⏸️ PARTE FINAL — Solo cuando todo lo anterior está aprobado
| Agente | Tarea |
|---|---|
| Claude Code | Mapbox V6 — reemplazar Leaflet |
| Codex | Dashboard superadmin mejorado |
| Antigravity | Login cliente + estado pedido público |

---

## PROTOCOLO DE REPORTE (para cada agente)

Cuando terminás tu tarea:

```bash
# 1. Validar sintaxis si tocaste index.html
node C:\Users\USUARIO\iporave-sistema\validate.js

# 2. Reportar al pizarrón
curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"TU_NOMBRE\",\"tarea\":\"PARTE_1_nombre\",\"archivos\":\"ruta/archivo\",\"resumen\":\"Qué hice exactamente\",\"estado\":\"Finalizado\"}"

# 3. Esperar confirmación VALIDADO del pizarrón
# 4. No continuar hasta que Claude Code apruebe la parte completa
```

---

## ESTADO DEL PIZARRÓN — Cómo saber cuándo están todos listos

El usuario trae el Google Sheets (ID: 1auJBPn6bko5NR99Rd1Z0AOb6minTxUk4drbjckq122c) a Claude Code.
Claude Code verifica que todos los agentes de esa parte tienen estado VALIDADO.
Si alguno tiene CONFLICTO → se resuelve antes de continuar.

---

## HISTORIAL DE APROBACIONES

| Parte | Fecha | Aprobado por | Deploy |
|---|---|---|---|
| — | — | — | — |
