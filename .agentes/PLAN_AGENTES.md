# 🏗️ PLAN DE AGENTES — IPORAVE SISTEMA
# Actualizado: 2026-05-10 (reorganización por rendimiento y confianza)
# Supervisor: Groq + Cerebras (fallback) vía Node-RED
# Pizarrón: Google Sheets — ID: 1auJBPn6bko5NR99Rd1Z0AOb6minTxUk4drbjckq122c
# Node-RED: http://localhost:1880 (endpoint POST /reporte)

---

## JERARQUÍA DE MODELOS IA

### 🔒 TIER 1 — Confianza total (pueden ver código sensible)
| Modelo | Velocidad | Uso principal |
|---|---|---|
| **Ollama llama3.2** | Local, sin límites | Pre-validación, código privado, siempre disponible |
| **Cerebras llama3.1-8b** | 4ms — más rápida del mundo | Supervisor fallback, tareas rápidas |
| **Groq llama-3.3-70b** | Muy rápido | Supervisor principal Node-RED |
| **Claude Code** | — | Seguridad, auth, revisión final |

### ⚠️ TIER 2 — Solo texto/ideas (NO código sensible)
| Modelo | Contexto | Uso permitido |
|---|---|---|
| **Kimi moonshot-v1-128k** | 128k tokens | Análisis de documentos grandes, brainstorming |
| **DeepSeek** | — | Razonamiento complejo sin código auth |
| **OpenRouter** | Multi-modelo | Consultas generales únicamente |

### ❌ NUNCA pasan por Tier 2
- verifyToken(), login.js, SAFE_SELF_FIELDS
- Claves Supabase, R2, Resend, VAPID, Anthropic
- Políticas RLS
- Cualquier credencial o secret

---

## FLUJO DE SUPERVISIÓN NODE-RED

```
Agente reporta → Google Sheets (registro)
        ↓
Ollama pre-check (local, instantáneo)
        ↓ ok
Groq supervisor final (llama-3.3-70b)
        ↓ si Groq falla/límite
Cerebras fallback (llama3.1-8b, 4ms)
        ↓
VALIDADO → siguiente tarea
CONFLICTO → stop.flag → avisar usuario
        ↓ cuando todos terminan
Claude Code revisión final
        ↓
Usuario aprueba → deploy
```

---

## HERRAMIENTAS POR AGENTE

### 🔵 CLAUDE CODE — Backend crítico y seguridad
**Modelo:** Claude Sonnet 4.6 (esta sesión)
**Tareas:**
1. WhatsApp Webhook — reconstruir con tabla pedidos
2. WhatsApp — entrada/salida mensajes por estado
3. Seguridad Opción B — migrar data layer al worker
4. Comisión dropshipper — modelo exacto en schema
5. Facturación B2B — diseño e implementación
6. Mapbox V6 — reemplazar Leaflet (AL FINAL)
7. Revisión final antes de cada deploy

### 🟢 CODEX — Frontend y analítica
**Herramienta:** Codex (instalado en terminal)
**Tareas:**
1. Clientes recurrentes para vendedor
2. Notificaciones in-app (badge + lista)
3. Mejorar formularios de perfil por rol
4. Ampliar analítica vendedor/proveedor
5. Reportes exportables por rango de fechas
6. Dashboard superadmin mejorado
7. Meta Conversiones offline (API)
8. TikTok Ads — conectar feed existente

### 🟡 ANTIGRAVITY — Tienda pública
**Herramienta:** Antigravity (instalado en terminal)
**Tareas:**
1. Catálogo público sin login
2. Filtros por categoría y precio
3. Detalle de producto
4. Carrito de compras básico
5. Formulario auto-registro cliente externo
6. Flujo aprobación superadmin
7. Login cliente separado
8. Formulario de pedido con dirección
9. Estado de pedido público sin login

### 🟣 AIDER — Refactoring múltiples archivos
**Modelo:** Cerebras (rápido) + Groq (complejo)
**Tareas:**
1. Limpiar código legacy del frontend (index.html)
2. Rol empresa — estructura y UI nueva
3. Meta Ads — conectar Mensajes al portafolio

### 🟠 PLANDEX — Tareas largas (WSL)
**Modelo:** configurable
**Tareas:**
1. Auto-registro completo (frontend + worker + Supabase)
2. Shopify — subir productos pendientes

### ⚪ OLLAMA — Pre-validación local
**Modelo:** llama3.2 (local, sin límites, privado)
**Rol:** Primera capa de supervisión en Node-RED. Siempre disponible aunque fallen las APIs externas.

### ⚡ CEREBRAS — Fallback ultrarrápido
**Modelo:** llama3.1-8b (4ms de respuesta)
**Rol:** Reemplaza a Groq automáticamente cuando este alcanza el límite diario.

### 🔍 GROQ — Supervisor principal
**Modelo:** llama-3.3-70b-versatile
**Rol:** Supervisión final en Node-RED. El más capaz para detectar conflictos de arquitectura.

### 🧵 CONTINUE.DEV — Asistente en VS Code/editor
**Modelos disponibles:** Groq, Cerebras, Ollama, Kimi, DeepSeek, OpenRouter
**Rol:** Autocompletado y chat dentro del editor. Usar Cerebras para velocidad, Groq para análisis.

### 🔬 FABRIC — Análisis de texto y patrones
**Rol:** Analizar documentación, PRs, reportes. Resumir contexto largo antes de pasarlo a otros agentes.

---

## REGLAS DE ORO

1. Nadie hace commit hasta que TODOS terminaron su bloque
2. Nadie hace deploy hasta que el usuario lo aprueba
3. Cada tarea completada → reportar al pizarrón (Node-RED POST /reporte)
4. Groq valida → VALIDADO o CONFLICTO DETECTADO (Cerebras si Groq falla)
5. Si CONFLICTO → stop.flag → ese agente se detiene
6. Claude Code tiene veto sobre: verifyToken(), login.js, RLS, SAFE_SELF_FIELDS
7. Siempre ejecutar `node validate.js` antes de reportar (si tocó index.html)
8. Kimi/DeepSeek/OpenRouter → NUNCA reciben código sensible

---

## CÓMO REPORTAR AL PIZARRÓN

```bash
curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"NOMBRE\",\"tarea\":\"DESCRIPCION\",\"archivos\":\"ruta/archivo\",\"resumen\":\"Qué se hizo\",\"estado\":\"Finalizado\"}"
```

---

## ACCIONES MANUALES PENDIENTES (usuario)
1. Isidro debe re-tap botón "🔔 Activar notif" en panel Mis Entregas
2. Meta Ads — identificar página correcta y conectar Mensajes al portafolio
3. Shopify — continuar subiendo productos
4. Importar flujo actualizado en Node-RED (menú → Import → flujo-pizarron.json)
5. Configurar límite $5 en OpenRouter: openrouter.ai/settings/limits
