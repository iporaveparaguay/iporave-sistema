# 📚 CONTEXTO COMPLETO — IPORAVE SISTEMA
# Leer COMPLETO antes de tocar cualquier archivo.

---

## 1. QUÉ ES ESTE PROYECTO

**Iporãve Connect** — sistema de gestión logística con múltiples roles para Paraguay.
Está EN PRODUCCIÓN con usuarios reales. Cada error afecta pedidos reales.

**Roles del sistema:** superadmin, admin, vendedor, dropshipper, delivery, proveedor, cliente

---

## 2. ARQUITECTURA

| Componente | Detalle |
|---|---|
| **Frontend** | SPA monolítica — TODO en un solo archivo: `iporave-sistema/public/index.html` (~7000 líneas, HTML/CSS/JS vanilla, sin framework) |
| **Backend** | Cloudflare Workers — `iporave-worker/src/` (ES modules) |
| **Base de datos** | Supabase (PostgreSQL). Tabla principal: `pedidos` |
| **Auth** | Supabase Auth nativa — `signInWithPassword()` + `access_token` / `refresh_token` |
| **Storage** | Cloudflare R2 para imágenes |
| **Deploy frontend** | Vercel — auto-deploy en push a branch `main` |
| **Deploy backend** | Manual: `npx wrangler deploy` desde `iporave-worker/` |
| **URLs producción** | Frontend: https://iporave-sistema.vercel.app — Worker: https://iporave-api.iporaveparaguay.workers.dev |

---

## 3. REPOS LOCALES

```
C:\Users\USUARIO\iporave-sistema\   ← frontend
C:\Users\USUARIO\iporave-worker\    ← backend/API
```

**Estado Git:**
- iporave-sistema: branch `main`, commit `625cd87`
- iporave-worker: branch `master`, commit `e30e18a`

---

## 4. DOCUMENTOS DE TRABAJO (leer en este orden)

| Documento | Qué contiene |
|---|---|
| `CONTEXTO_SISTEMA.md` | Este archivo — arquitectura y reglas |
| `PLAN_MAESTRO.md` | **LEER OBLIGATORIO** — sprints, zonas, límites, protocolo completo |
| `TAREA_SPRINT1_TUAGENTE.md` | Tu tarea específica del Sprint actual |
| `check-stop.js` | Verificar si hay stop flag antes de empezar |
| `onboarding.js` | Verificación completa del entorno |

---

## 4b. ARCHIVOS CRÍTICOS — NO TOCAR SIN CLAUDE CODE

| Archivo | Por qué es crítico |
|---|---|
| `iporave-worker/src/utils.js` → `verifyToken()` | Corazón de toda la autenticación |
| `iporave-worker/src/api/login.js` | Flujo Supabase Auth nativa — NO volver a JWT custom |
| `iporave-worker/src/api/save-user.js` → `SAFE_SELF_FIELDS` | Campos que el usuario puede guardar — agregar con cuidado |
| Políticas RLS en Supabase | Configuradas en dashboard, NO en código |

---

## 5. REGLAS TÉCNICAS OBLIGATORIAS

1. **NUNCA** poner `</script>` dentro de strings JS en index.html — rompe TODO. Usar `'<scr'+'ipt>'`
2. **SIEMPRE** ejecutar `node validate.js` después de cambiar index.html
3. `openA()` toma EXACTAMENTE 4 args: `openA(title, body, footer, size)`
4. `getVisibleOrders()` filtra por rol automáticamente — usar SIEMPRE para páginas de usuario
5. RLS usa `auth.role() = 'authenticated'` — NO usar `auth.uid()` (el id es entero, no UUID)
6. NO deployar sin confirmación explícita del usuario

---

## 6. COMANDOS ÚTILES

```bash
# Validar sintaxis antes de reportar
cd C:\Users\USUARIO\iporave-sistema
node validate.js

# Chequear si hay stop flag activo
node C:\Users\USUARIO\iporave-sistema\.agentes\check-stop.js

# Worker en local
cd C:\Users\USUARIO\iporave-worker
npx wrangler dev

# Deploy worker
cd C:\Users\USUARIO\iporave-worker
npx wrangler deploy

# Ver últimos commits
cd C:\Users\USUARIO\iporave-sistema
git log --oneline -5
```

---

## 7. CÓMO REPORTAR AL PIZARRÓN (OBLIGATORIO al terminar cada tarea)

```bash
curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"TU_NOMBRE\",\"tarea\":\"NOMBRE_TAREA\",\"archivos\":\"ruta/archivo.js\",\"resumen\":\"Qué se hizo y por qué\",\"estado\":\"Finalizado\"}"
```

El supervisor (Groq vía Node-RED) responde:
- `VALIDADO` → podés continuar con la siguiente tarea
- `CONFLICTO DETECTADO` → detenerse y avisar al usuario

---

## 8. INFRAESTRUCTURA DE COORDINACIÓN

| Componente | Detalle |
|---|---|
| **Node-RED** | http://localhost:1880 — orquestador central (corre en la PC del usuario) |
| **Pizarrón** | Google Sheets ID: `1auJBPn6bko5NR99Rd1Z0AOb6minTxUk4drbjckq122c` |
| **Supervisor** | Groq + Llama 3.3 70B — valida cada tarea automáticamente |
| **Stop flag** | `C:\Users\USUARIO\node-red-config\stop.flag` — si existe, nadie trabaja |
| **Credenciales Google** | `C:\Users\USUARIO\node-red-config\google-credentials.json` |

---

## 9. LO QUE ESTÁ IMPLEMENTADO Y FUNCIONANDO

- Auth Supabase nativa completa (login, reset password, dispositivos)
- Perfil obligatorio por rol con bloqueo de navegación
- Fotos de cédula para delivery
- Panel dropshipper completo (5 stats + gráficas + liquidación)
- Panel proveedor con liquidación propia
- NAV completo para todos los roles
- Push notifications VAPID (Isidro debe re-tap el botón)
- GPS tracking delivery en tiempo real
- 4 paneles analíticos por rol
- Boletas IVA con PDF + WhatsApp para todos los roles
- Liquidación para vendedor/dropshipper/admin/proveedor
- Mapa en tiempo real con Leaflet
- Meta Pixel instalado (ID: 1863034214304562)
- Feed catálogo Meta Ads activo
- Seguridad: RLS + rate limiting + JWT

---

## 10. PENDIENTES POR AGENTE (ver PLAN_MAESTRO.md — documento principal)

- **Claude Code:** WhatsApp webhook, seguridad Opción B, comisiones, facturación B2B, Mapbox V6
- **Codex:** clientes recurrentes, analítica ampliada, reportes, Meta/TikTok Ads
- **Antigravity:** tienda pública completa (catálogo, carrito, checkout, auto-registro)
- **Aider:** refactoring, rol empresa, Meta Ads portafolio
- **Plandex:** auto-registro completo, Shopify productos

---

## 11. VARIABLES DE ENTORNO (Worker)

No están en el código — están en Cloudflare como secrets (wrangler secrets).
Para ver cuáles existen: `npx wrangler secret list` desde `iporave-worker/`.

---

## 12. SHOPIFY (tienda externa)

- Dominio interno API: `iporaveparaguay.myshopify.com`
- Dominio público: `iporaveparaguay.com`
- Pendiente: continuar subiendo productos
