# PLAN ARQUITECTÓNICO — SISTEMA DE SUSCRIPCIONES IPORÃVE SaaS

**Fecha:** 2026-05-16
**Estado:** PROPUESTA — NO IMPLEMENTAR SIN APROBACIÓN
**Autor:** Claude (sesión de diseño)
**Alcance:** Documento de planificación. NO se modifica ningún archivo del sistema actual.

---

## 0. RESUMEN EJECUTIVO

Iporãve evoluciona de plataforma interna multi-rol a **SaaS multi-tenant** con suscripciones mensuales. Cada usuario (proveedor, vendedor, dropshipper, tienda pública) paga una mensualidad para acceder a su set de herramientas. El superadmin y admin (operación interna Iporãve) quedan exentos. El cliente final también queda exento.

**Principio UX clave:** Todos los menús son visibles para todos los usuarios. Lo que no está incluido en su plan aparece con candado y al hacer click se muestra modal "🔒 Desbloqueá con Plan X". Esto convierte cada feature bloqueada en una oportunidad de upsell.

**Principio arquitectónico clave:** Las restricciones de creación/gestión de otros usuarios NO son del plan pago — son **estructurales del rol**. Un proveedor NUNCA puede crear delivery, ni con Plan Enterprise. Eso es función exclusiva del admin/superadmin Iporãve.

---

## 1. TIERS DE SUSCRIPCIÓN PROPUESTOS

### 1.1 Plan Gratis (Free) — Gs 0/mes

**Objetivo:** Onboarding sin fricción, demostrar valor, generar leads.

**Incluye:**
- Acceso al panel del rol
- Hasta 10 productos en catálogo (proveedor/vendedor)
- Hasta 20 pedidos/mes
- 1 sucursal
- Soporte por FAQ/comunidad
- Marca Iporãve visible en boletas y tienda pública
- Reportes básicos (últimos 7 días)

**Límites:**
- Sin acceso a WhatsApp automation
- Sin acceso a Gemini Pro
- Sin exportar PDF
- Sin operaciones masivas
- Sin API access

---

### 1.2 Plan Pro — Gs 99.000/mes (Gs 990.000/año, ahorro 17%)

**Objetivo:** Pequeños emprendedores que ya facturan.

**Incluye TODO lo de Free, más:**
- Hasta 200 productos
- Hasta 500 pedidos/mes
- WhatsApp automation (notificaciones automáticas)
- Reportes avanzados (90 días, comparativas)
- Exportar PDF (boletas, reportes)
- Operaciones masivas (subir CSV)
- Gemini Pro (análisis IA básico)
- Soporte por chat (24-48h)
- Branding: ocultar logo Iporãve

---

### 1.3 Plan Business — Gs 249.000/mes (Gs 2.490.000/año)

**Objetivo:** Negocios establecidos con volumen.

**Incluye TODO lo de Pro, más:**
- Productos ilimitados
- Pedidos ilimitados
- Hasta 3 sucursales (multi-branch)
- Analítica avanzada (heatmaps, cohorts, predictivo)
- API access (read+write con rate limit)
- Branding completo (dominio propio CNAME, colores)
- Soporte prioritario (4-12h, WhatsApp directo)
- Gemini Pro avanzado (recomendaciones, forecasting)
- Integraciones (Shopify sync, Meta Ads pixel propio)
- Exportar Excel, integraciones contables

---

### 1.4 Plan Enterprise — Custom (desde Gs 800.000/mes)

**Objetivo:** Empresas grandes, franquicias, contratos B2B.

**Incluye TODO lo de Business, más:**
- Sucursales ilimitadas
- SLA contractual (99.9% uptime)
- Soporte dedicado (account manager)
- White-label total (sin mención Iporãve en ningún lado)
- Onboarding personalizado y capacitación
- Integraciones a medida (ERP, contabilidad propia)
- Servidor dedicado / región propia (opcional)
- Términos legales personalizados

---

### 1.5 Tabla comparativa rápida

| Feature | Free | Pro | Business | Enterprise |
|---|---|---|---|---|
| Precio mensual (Gs) | 0 | 99.000 | 249.000 | desde 800.000 |
| Productos | 10 | 200 | ∞ | ∞ |
| Pedidos/mes | 20 | 500 | ∞ | ∞ |
| Sucursales | 1 | 1 | 3 | ∞ |
| WhatsApp automation | ❌ | ✅ | ✅ | ✅ |
| Gemini Pro | ❌ | básico | avanzado | avanzado |
| API access | ❌ | ❌ | ✅ | ✅ |
| Branding propio | ❌ | parcial | total | white-label |
| Soporte | FAQ | chat | prioritario | dedicado |
| Exportar PDF/Excel | ❌ | PDF | PDF+Excel | todo |

---

## 2. SCHEMA DE BASE DE DATOS (PostgreSQL / Supabase)

### 2.1 Tabla `planes`

```sql
CREATE TABLE planes (
  id              SERIAL PRIMARY KEY,
  codigo          TEXT NOT NULL UNIQUE,       -- 'free' | 'pro' | 'business' | 'enterprise'
  nombre          TEXT NOT NULL,              -- 'Plan Pro'
  descripcion     TEXT,
  precio_mes      INTEGER NOT NULL DEFAULT 0, -- en Guaraníes
  precio_anual    INTEGER NOT NULL DEFAULT 0, -- en Guaraníes
  features_json   JSONB NOT NULL DEFAULT '{}',-- {"create_users": false, "max_productos": 200, ...}
  limites_json    JSONB NOT NULL DEFAULT '{}',-- {"max_productos": 200, "max_pedidos_mes": 500}
  visible         BOOLEAN NOT NULL DEFAULT true, -- ocultar Enterprise del checkout público
  activo          BOOLEAN NOT NULL DEFAULT true,
  orden           INTEGER NOT NULL DEFAULT 0, -- para ordenar en UI
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_planes_codigo ON planes(codigo);
CREATE INDEX idx_planes_activo ON planes(activo) WHERE activo = true;
```

### 2.2 Tabla `suscripciones`

```sql
CREATE TABLE suscripciones (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
  plan_id         INTEGER NOT NULL REFERENCES planes(id),
  estado          TEXT NOT NULL DEFAULT 'activa',
                  -- 'activa' | 'pendiente_pago' | 'vencida' | 'cancelada' | 'trial' | 'grandfathered'
  fecha_inicio    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  fecha_fin       TIMESTAMPTZ NOT NULL,       -- cuándo expira el periodo actual
  fecha_cancelacion TIMESTAMPTZ,
  periodo         TEXT NOT NULL DEFAULT 'mensual', -- 'mensual' | 'anual'
  metodo_pago     TEXT,                       -- 'transferencia' | 'tigo_money' | 'tarjeta' | 'manual_admin'
  auto_renovar    BOOLEAN NOT NULL DEFAULT true,
  grant_motivo    TEXT,                       -- si fue otorgada manualmente por admin
  granted_by      UUID REFERENCES usuarios(id),
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_suscripciones_user_activa
  ON suscripciones(user_id) WHERE estado IN ('activa', 'trial', 'grandfathered');
CREATE INDEX idx_suscripciones_estado ON suscripciones(estado);
CREATE INDEX idx_suscripciones_fecha_fin ON suscripciones(fecha_fin);
```

### 2.3 Tabla `pagos_suscripcion`

```sql
CREATE TABLE pagos_suscripcion (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  suscripcion_id  UUID NOT NULL REFERENCES suscripciones(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL REFERENCES usuarios(id),
  monto           INTEGER NOT NULL,           -- en Guaraníes
  moneda          TEXT NOT NULL DEFAULT 'PYG',
  metodo          TEXT NOT NULL,              -- 'transferencia' | 'tigo_money' | 'tarjeta' | etc
  estado          TEXT NOT NULL DEFAULT 'pendiente',
                  -- 'pendiente' | 'confirmado' | 'rechazado' | 'reembolsado'
  comprobante_r2_key TEXT,                    -- key en Cloudflare R2 del comprobante subido
  referencia      TEXT,                       -- nro de transacción externo
  fecha_pago      TIMESTAMPTZ,
  fecha_confirmacion TIMESTAMPTZ,
  confirmado_por  UUID REFERENCES usuarios(id),
  notas           TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pagos_susc_id ON pagos_suscripcion(suscripcion_id);
CREATE INDEX idx_pagos_estado ON pagos_suscripcion(estado);
CREATE INDEX idx_pagos_fecha ON pagos_suscripcion(fecha_pago DESC);
```

### 2.4 Tabla `features_catalog` (catálogo maestro de features)

```sql
CREATE TABLE features_catalog (
  codigo          TEXT PRIMARY KEY,           -- 'whatsapp_automation', 'export_pdf', etc.
  nombre          TEXT NOT NULL,              -- 'WhatsApp Automation'
  descripcion     TEXT,
  categoria       TEXT,                       -- 'comunicacion' | 'analitica' | 'integracion' | 'limites'
  min_plan        TEXT NOT NULL,              -- 'free' | 'pro' | 'business' | 'enterprise'
  tipo            TEXT NOT NULL DEFAULT 'boolean', -- 'boolean' | 'numeric' | 'list'
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.5 Vista `v_features_usuario` (qué tiene desbloqueado cada usuario)

```sql
CREATE OR REPLACE VIEW v_features_usuario AS
SELECT
  u.id AS user_id,
  u.rol,
  s.id AS suscripcion_id,
  p.codigo AS plan_codigo,
  p.nombre AS plan_nombre,
  p.features_json,
  p.limites_json,
  s.estado AS suscripcion_estado,
  s.fecha_fin
FROM usuarios u
LEFT JOIN suscripciones s ON s.user_id = u.id
   AND s.estado IN ('activa', 'trial', 'grandfathered')
   AND s.fecha_fin > NOW()
LEFT JOIN planes p ON p.id = s.plan_id;
```

(Si la performance lo requiere, convertir en tabla materializada con refresh cada 5 min o al cambio de suscripción.)

### 2.6 Datos seed iniciales

```sql
INSERT INTO planes (codigo, nombre, precio_mes, precio_anual, features_json, limites_json, orden) VALUES
('free', 'Plan Gratis', 0, 0,
 '{"whatsapp_automation":false,"gemini_pro":false,"export_pdf":false,"api_access":false,"advanced_analytics":false,"custom_branding":false,"bulk_operations":false,"multi_branch":false}',
 '{"max_productos":10,"max_pedidos_mes":20,"max_sucursales":1}', 1),
('pro', 'Plan Pro', 99000, 990000,
 '{"whatsapp_automation":true,"gemini_pro":"basico","export_pdf":true,"api_access":false,"advanced_analytics":true,"custom_branding":"parcial","bulk_operations":true,"multi_branch":false}',
 '{"max_productos":200,"max_pedidos_mes":500,"max_sucursales":1}', 2),
('business', 'Plan Business', 249000, 2490000,
 '{"whatsapp_automation":true,"gemini_pro":"avanzado","export_pdf":true,"export_excel":true,"api_access":true,"advanced_analytics":true,"custom_branding":"total","bulk_operations":true,"multi_branch":true,"shopify_sync":true}',
 '{"max_productos":-1,"max_pedidos_mes":-1,"max_sucursales":3}', 3),
('enterprise', 'Plan Enterprise', 800000, 8000000,
 '{"whatsapp_automation":true,"gemini_pro":"avanzado","export_pdf":true,"export_excel":true,"api_access":true,"advanced_analytics":true,"custom_branding":"white_label","bulk_operations":true,"multi_branch":true,"shopify_sync":true,"dedicated_support":true,"sla":true,"custom_integrations":true}',
 '{"max_productos":-1,"max_pedidos_mes":-1,"max_sucursales":-1}', 4);
```

(`-1` = ilimitado.)

---

## 3. ENDPOINTS DEL WORKER NECESARIOS

### 3.1 Públicos (usuario suscrito)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/suscripciones/planes` | Lista pública de planes visibles |
| GET | `/api/suscripciones/mi-plan` | Plan actual del usuario logueado |
| GET | `/api/suscripciones/features` | Lista de feature codes desbloqueadas |
| POST | `/api/suscripciones/subscribe` | Crear suscripción (genera pago pendiente) |
| POST | `/api/suscripciones/cancel` | Cancelar auto-renovación |
| POST | `/api/suscripciones/renovar` | Renovar manualmente |
| POST | `/api/suscripciones/upgrade` | Upgrade a plan superior (prorrateo) |
| POST | `/api/suscripciones/downgrade` | Downgrade (al final del periodo) |
| GET | `/api/suscripciones/historial-pagos` | Lista de pagos del usuario |
| POST | `/api/suscripciones/subir-comprobante` | Sube comprobante de transferencia a R2 |

### 3.2 Admin/Superadmin

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/admin/suscripciones` | Lista todas las suscripciones (con filtros) |
| POST | `/api/admin/suscripciones/grant` | Otorgar plan manualmente (con motivo) |
| POST | `/api/admin/suscripciones/extend` | Extender fecha_fin |
| POST | `/api/admin/suscripciones/cancel` | Cancelar forzosamente |
| POST | `/api/admin/pagos/confirmar/:id` | Confirmar pago manual (transferencia) |
| POST | `/api/admin/pagos/rechazar/:id` | Rechazar pago |
| GET | `/api/admin/suscripciones/metricas` | MRR, churn, conversion |
| PUT | `/api/admin/planes/:id` | Editar plan (features, precio) |

### 3.3 Cron / interno

| Schedule | Tarea |
|---|---|
| Diario 03:00 | `cron-suscripciones-vencer` → marca como `vencida` las que pasaron `fecha_fin` |
| Diario 04:00 | `cron-suscripciones-renovar` → intenta auto-renovar con `auto_renovar=true` |
| Cada hora | `cron-recordatorios` → email/WhatsApp 7/3/1 días antes de vencer |

### 3.4 Contratos de respuesta (ejemplo)

**`GET /api/suscripciones/features`**

```json
{
  "ok": true,
  "user_id": "uuid",
  "plan": "pro",
  "plan_nombre": "Plan Pro",
  "estado": "activa",
  "fecha_fin": "2026-06-16T00:00:00Z",
  "features": {
    "whatsapp_automation": true,
    "gemini_pro": "basico",
    "export_pdf": true,
    "api_access": false,
    "advanced_analytics": true,
    "bulk_operations": true,
    "multi_branch": false
  },
  "limites": {
    "max_productos": 200,
    "max_pedidos_mes": 500,
    "max_sucursales": 1
  },
  "uso_actual": {
    "productos": 47,
    "pedidos_mes": 123,
    "sucursales": 1
  }
}
```

---

## 4. SISTEMA DE FEATURE FLAGS (frontend)

### 4.1 Flujo de carga

1. Login exitoso → frontend recibe `CU` (Current User).
2. Inmediatamente fetch `GET /api/suscripciones/features`.
3. Guardar en `CU.plan`, `CU.features`, `CU.limites`, `CU.uso`.
4. Cachear en `sessionStorage` con TTL 5 min (refresh al expirar).
5. Invalidar cache al upgrade/downgrade.

### 4.2 Helper global (pseudo-código)

```javascript
// global-features.js
window.Features = {
  has(code) {
    const f = CU?.features?.[code];
    return f === true || (typeof f === 'string' && f !== 'false');
  },
  level(code) {
    // para features con niveles: 'basico' | 'avanzado'
    return CU?.features?.[code] || false;
  },
  withinLimit(code, currentValue) {
    const limit = CU?.limites?.[code];
    if (limit === -1 || limit === undefined) return true;
    return currentValue < limit;
  },
  requiredPlan(code) {
    // devuelve el plan mínimo necesario (consulta features_catalog)
    return CU?.featuresCatalog?.[code]?.min_plan || 'pro';
  },
  showLockedModal(code) {
    const plan = this.requiredPlan(code);
    UI.openModal('feature-locked', { code, plan });
  }
};
```

### 4.3 Uso en botones/menús

```javascript
// al renderizar un menú item
if (Features.has('whatsapp_automation')) {
  renderNormal(item);
} else {
  renderLocked(item, { onClick: () => Features.showLockedModal('whatsapp_automation') });
}
```

### 4.4 Validación dual (cliente Y servidor)

CRÍTICO: el feature flag del cliente es solo UX. El worker SIEMPRE valida el plan antes de ejecutar la acción:

```javascript
// pseudo-worker
async function requireFeature(request, code) {
  const features = await loadUserFeatures(request.userId);
  if (!features[code]) {
    return jsonError(403, 'FEATURE_LOCKED', `Requiere plan: ${minPlan(code)}`);
  }
}
```

---

## 5. UX DE BLOQUEO "🔒 Desbloqueá con Plan X"

### 5.1 Estados visuales de un menú/botón bloqueado

- Texto en color tenue (gris claro #999)
- Ícono candado 🔒 al lado del texto (12px)
- Cursor `not-allowed` al hover
- Tooltip al hover: "Plan Pro requerido — desbloqueá WhatsApp Automation"
- Badge pequeño "PRO" o "BUSINESS" en esquina (opcional)

### 5.2 Modal al click

```
┌────────────────────────────────────────┐
│ 🔒 Función bloqueada                   │
├────────────────────────────────────────┤
│                                        │
│  WhatsApp Automation                   │
│                                        │
│  Esta función está incluida en         │
│  el Plan Pro (Gs 99.000/mes).          │
│                                        │
│  Con Pro obtenés también:              │
│  ✓ Hasta 200 productos                 │
│  ✓ 500 pedidos/mes                     │
│  ✓ Exportar PDF                        │
│  ✓ Análisis IA básico                  │
│                                        │
│  [Ver todos los planes]  [Cerrar]      │
│                                        │
└────────────────────────────────────────┘
```

### 5.3 Página `/suscripciones`

- Hero con plan actual y CTA principal
- Tabla comparativa de planes (sticky header)
- Cada columna con botón "Suscribirme" / "Plan actual" / "Downgrade"
- FAQ al pie
- Testimonios (futuro)

### 5.4 Estados de la suscripción del usuario (badges en perfil)

- 🟢 **Activa** — todo OK
- 🟡 **Por vencer (7 días)** — recordatorio amable
- 🟠 **Vence hoy** — banner sticky superior
- 🔴 **Vencida** — acceso degradado al plan Free automáticamente
- ⚪ **Trial** — días restantes visibles
- 🔵 **Grandfathered** — usuario antiguo con plan especial

---

## 6. CATÁLOGO EXHAUSTIVO DE FEATURE FLAGS

### 6.1 Límites cuantitativos (`limites_json`)

| Código | Tipo | Free | Pro | Business | Enterprise |
|---|---|---|---|---|---|
| `max_productos` | int | 10 | 200 | -1 | -1 |
| `max_pedidos_mes` | int | 20 | 500 | -1 | -1 |
| `max_sucursales` | int | 1 | 1 | 3 | -1 |
| `max_usuarios_equipo` | int | 1 | 3 | 10 | -1 |
| `max_almacenes` | int | 1 | 2 | 5 | -1 |
| `max_categorias` | int | 5 | 20 | -1 | -1 |
| `storage_r2_gb` | int | 1 | 5 | 25 | -1 |

### 6.2 Features booleanas (`features_json`)

**Comunicación / Marketing:**
- `whatsapp_automation` — notificaciones automáticas
- `whatsapp_chatbot` — bot IA conversacional
- `email_marketing` — campañas email
- `sms_notifications` — SMS
- `push_notifications_avanzado` — segmentación push

**Analítica:**
- `advanced_analytics` — heatmaps, cohorts
- `predictive_analytics` — forecasting
- `custom_reports` — reportes a medida
- `historial_extendido` — más de 30 días
- `dashboard_personalizado` — widgets configurables

**IA:**
- `gemini_pro_basico` — análisis simple
- `gemini_pro_avanzado` — recomendaciones
- `ia_recomendaciones_producto` — cross-sell automático
- `ia_pricing_dinamico` — sugerencias de precio
- `ia_descripcion_automatica` — genera fichas de producto

**Operaciones:**
- `bulk_operations` — subir CSV masivo
- `export_pdf` — exportar a PDF
- `export_excel` — exportar a Excel/CSV
- `import_productos_csv` — importar catálogo
- `automatizaciones_workflow` — reglas if-then
- `inventario_multi_almacen` — stock por almacén
- `transferencias_internas` — mover stock entre sucursales

**Integraciones:**
- `api_access` — API REST pública
- `webhooks` — webhooks salientes
- `shopify_sync` — sincronizar con Shopify
- `meta_ads_pixel` — pixel propio
- `google_analytics` — GA4
- `mercado_libre_sync` — sincronizar ML
- `contabilidad_export` — export a software contable

**Branding / Tienda pública:**
- `custom_branding_parcial` — colores y logo
- `custom_branding_total` — sin marca Iporãve
- `white_label` — dominio propio + sin mención
- `dominio_propio` — CNAME a iporave
- `tienda_publica_activa` — habilita tienda pública pagada
- `tema_premium` — temas avanzados de tienda
- `paginas_personalizadas` — páginas extra (about, contacto)

**Soporte:**
- `priority_support` — soporte prioritario
- `dedicated_support` — account manager
- `sla_garantizado` — SLA contractual
- `onboarding_personalizado` — capacitación

**Multi-tenant:**
- `multi_branch` — más de 1 sucursal
- `multi_user_team` — invitar empleados al equipo
- `roles_personalizados` — definir roles custom dentro del equipo

> NOTA IMPORTANTE: `create_users` y `manage_other_users` NO son features de plan. Son permisos estructurales del rol superadmin/admin Iporãve. Un proveedor NUNCA puede crear delivery aunque tenga Plan Enterprise.

---

## 7. MÉTODOS DE PAGO PROPUESTOS

### 7.1 Fase 1 (lanzamiento)

**Transferencia bancaria manual + comprobante**
- Usuario elige plan → genera "pago pendiente" en DB
- UI muestra datos bancarios (Itaú, Continental, Visión)
- Usuario sube foto/PDF del comprobante a R2
- Admin recibe notificación → revisa → confirma o rechaza
- Al confirmar: suscripción pasa a `activa`, se calcula `fecha_fin`

**Tigo Money / Personal Pay (billeteras Paraguay)**
- Mismo flujo que transferencia pero con número de billetera
- Captura de pago como comprobante
- Confirmación manual

### 7.2 Fase 2 (3-6 meses post-lanzamiento)

**Pago con tarjeta — Bancard / Pagopar / Infonet**
- Integración con pasarela paraguaya
- Tokenización para auto-renovación
- Webhook de confirmación instantánea

**Mercado Pago Paraguay**
- API oficial, soporta tarjetas + saldo MP
- Auto-renovación nativa

### 7.3 Fase 3 (futuro)

**Stripe internacional**
- Para Enterprise con tarjetas internacionales
- USD opcional

**Cripto (USDT, USDC)**
- Wallet propia + watcher de transacciones
- Conversión a Gs al momento

### 7.4 Esquema de retry / dunning

- D-7: email recordatorio
- D-3: email + WhatsApp
- D-1: WhatsApp + banner sticky
- D 0: vencimiento → 3 días de gracia
- D+3: degradación automática a Free
- D+15: email "te extrañamos"
- D+30: marcar `churned`

---

## 8. PLAN DE MIGRACIÓN (FASES)

### Fase 0 — Preparación (semana 1)
- Aprobar este documento
- Diseñar mockups de UI (modal locked, página planes, badges)
- Validar pricing con 3-5 usuarios clave

### Fase 1 — Schema (semana 2)
- Crear tablas `planes`, `suscripciones`, `pagos_suscripcion`, `features_catalog`
- Crear vista `v_features_usuario`
- Seed con 4 planes
- **NO** activar feature flags todavía

### Fase 2 — Sistema de flags "modo permisivo" (semana 3)
- Implementar `GET /api/suscripciones/features` retornando TODO `true` para todos
- Implementar `window.Features.has()` en frontend
- A todos los usuarios existentes asignar suscripción `grandfathered` con Plan Business
- **Cero impacto funcional** — sistema sigue exactamente como antes

### Fase 3 — UI de planes (semana 4)
- Página `/suscripciones`
- Modal "feature locked" (sin uso aún)
- Página perfil muestra plan actual
- Endpoints admin para gestionar suscripciones

### Fase 4 — Activación gradual de bloqueos (semanas 5-12)
**Una feature por semana**, ordenadas por menor impacto:
1. `export_pdf` (semana 5)
2. `bulk_operations` (semana 6)
3. `advanced_analytics` (semana 7)
4. `whatsapp_automation` (semana 8)
5. `gemini_pro` (semana 9)
6. `multi_branch` (semana 10)
7. `api_access` (semana 11)
8. `custom_branding` (semana 12)

Cada activación:
- Anuncio 7 días antes (email + banner in-app)
- Toggle por feature flag en DB (`features_catalog.activo`)
- Monitoreo de soporte 48h post-activación
- Rollback rápido si churn anormal

### Fase 5 — Lanzamiento comercial (semana 13)
- Quitar `grandfathered` de usuarios nuevos (solo Free al registrarse)
- Habilitar pagos reales
- Campaña Meta Ads de adquisición
- Grandfathered existentes mantienen Business **3 meses gratis** → luego se les ofrece descuento 50% año 1

### Fase 6 — Tienda pública pagada (semana 16+)
- La activación de tienda pública requiere mínimo Plan Pro
- Subdominio propio en Business+
- Dominio propio en Enterprise

---

## 9. MÉTRICAS A TRACKEAR

### 9.1 Financieras (dashboard superadmin)

- **MRR (Monthly Recurring Revenue)** — suma de mensualidades activas
- **ARR (Annual Recurring Revenue)** — MRR × 12
- **ARPU (Average Revenue Per User)** — MRR / usuarios pagos
- **Net Revenue** — MRR cobrado real (descuenta no-pagos)
- **Churn rate mensual** — % de suscripciones canceladas/vencidas
- **Gross churn vs Net churn** (incluye upgrades como compensación)

### 9.2 Conversión

- **Free → Pro conversion rate** (objetivo: 5-10%)
- **Pro → Business conversion rate** (objetivo: 15-25%)
- **Trial → Paid conversion** (si hay trial)
- **Tiempo promedio Free → Paid** (días)
- **Funnel de checkout** (visitas planes → click suscribir → completó pago)

### 9.3 Engagement / Producto

- **Feature adoption rate** por feature
- **Feature stickiness** — DAU/MAU por feature pagada
- **Modal "locked" clicks** — cuántos clicks en features bloqueadas (indicador de demand)
- **Top features que generan upgrade** — qué bloqueo motiva pagar

### 9.4 LTV / CAC

- **LTV (Lifetime Value)** — ARPU × (1 / churn rate)
- **CAC (Customer Acquisition Cost)** — gasto marketing / nuevos pagos
- **LTV:CAC ratio** (objetivo: >3:1)
- **Payback period** — meses para recuperar CAC

### 9.5 Operacionales

- **Tiempo promedio confirmación pago manual** (objetivo: <24h)
- **Tasa de pagos rechazados** (comprobante inválido)
- **Tickets de soporte por plan**
- **NPS por plan**

---

## 10. COMPARACIÓN COMPETITIVA (PARAGUAY / LATAM)

### 10.1 Shopify

| Plan | USD/mes | Gs aprox |
|---|---|---|
| Basic | $39 | 285.000 |
| Shopify | $105 | 770.000 |
| Advanced | $399 | 2.920.000 |

Comisión 2% transacción si no usás Shopify Payments. No tiene módulo delivery/multi-rol nativo.

### 10.2 Tiendanube

| Plan | USD/mes | Gs aprox |
|---|---|---|
| Inicial | $9 | 66.000 |
| Pleno | $33 | 240.000 |
| Evolución | $66 | 480.000 |

Enfocada solo en e-commerce. No tiene gestión multi-rol ni delivery.

### 10.3 Mercado Shops

Gratis pero cobra comisión 12-16% por venta. No comparable directamente.

### 10.4 Empretienda (Paraguay/Argentina)

| Plan | USD/mes | Gs aprox |
|---|---|---|
| Básico | $15 | 110.000 |
| Avanzado | $35 | 255.000 |
| Premium | $75 | 545.000 |

### 10.5 Posicionamiento Iporãve

Iporãve NO compite solo con e-commerce — compite con **ERP + e-commerce + delivery + multi-rol** integrado. Comparables más cercanos serían **Bsale** o **Defontana** (mucho más caros, US$100-300/mes).

**Pricing propuesto vs competencia:**

| Plan Iporãve | Gs/mes | USD aprox | Vs competencia |
|---|---|---|---|
| Free | 0 | 0 | Ganamos vs Tiendanube (no tiene free real) |
| Pro 99k | 99.000 | $13 | Más barato que Tiendanube Inicial, con más features |
| Business 249k | 249.000 | $34 | Equivalente a Tiendanube Pleno pero con multi-rol/delivery |
| Enterprise 800k+ | 800.000+ | $109+ | Vs Shopify Advanced, mucho más barato |

**Ventaja competitiva clave:** ningún competidor en PY ofrece la integración delivery + dropshipper + proveedor + tienda en un solo SaaS. Iporãve puede capturar ese nicho.

### 10.6 Recomendaciones de pricing

1. **Anclar fuerte el Free** — masa crítica y boca a boca.
2. **Pro es el "default psicológico"** — destacar visualmente como "Más popular".
3. **Anual con 17% descuento** (2 meses gratis) — mejora cash flow y reduce churn.
4. **Trial 14 días de Business** al registrarse → empuja conversion.
5. **Descuentos para early adopters**: primeros 100 paying users → 30% off de por vida (lock-in + word-of-mouth).

---

## 11. RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Churn alto al activar bloqueos | Alta | Alto | Activación gradual + grandfathering generoso |
| Pagos manuales saturan al admin | Media | Medio | Automatizar con Bancard cuanto antes |
| Confusión usuarios sobre qué plan tienen | Alta | Medio | Badge persistente + página /mi-plan clara |
| Backend deja pasar feature sin validar | Media | Alto | Middleware `requireFeature()` obligatorio + tests |
| Competencia copia pricing | Baja | Bajo | Velocidad de feature delivery como moat |
| Crisis económica Paraguay | Media | Alto | Tener planes en Gs (no USD) + flexibilidad de descuentos |

---

## 12. CHECKLIST DE APROBACIÓN

Antes de pasar a implementación, validar con el usuario:

- [ ] ¿Los 4 tiers (Free/Pro/Business/Enterprise) están bien?
- [ ] ¿Los precios (99k / 249k / 800k+) son aceptables?
- [ ] ¿La regla "el rol manda sobre el plan" (proveedor nunca crea delivery) es correcta?
- [ ] ¿La UX "todos ven todo, con candado" es la deseada?
- [ ] ¿Los 30+ feature flags propuestos cubren el alcance?
- [ ] ¿La fase de grandfathering (3 meses gratis a usuarios actuales) es OK?
- [ ] ¿El orden de activación gradual (semanas 5-12) es razonable?
- [ ] ¿Se aprueba el schema de DB tal como está?
- [ ] ¿Se aprueban los métodos de pago de Fase 1 (transferencia + Tigo)?
- [ ] ¿Hay features adicionales que querés agregar al catálogo?

---

## 13. PRÓXIMOS PASOS

1. Usuario revisa este documento y marca el checklist sección 12.
2. Iteramos correcciones si las hay.
3. Una vez aprobado, generar:
   - `MIGRATIONS_SUSCRIPCIONES.sql` (Fase 1)
   - Mockups Figma/HTML de página /suscripciones y modal locked
   - Stubs de endpoints en worker (sin lógica de negocio aún)
4. Decidir agente responsable de implementación (Codex frontend, Claude backend, ¿Antigravity tienda pública?).

---

**FIN DEL DOCUMENTO**
