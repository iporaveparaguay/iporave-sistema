# PLAN_MULTI_ROL — Arquitectura multi-cuenta del mismo usuario

> Documento arquitectónico. Fecha: 2026-05-16.
> Sistema: Iporãve (single-tenant, multi-rol por usuario).
> Objetivo: permitir que un mismo dueño humano gestione varias cuentas con roles distintos y vea un panel agregado de todos sus balances.

---

## 0. Resumen ejecutivo

Iporãve es single-tenant: hay UNA instancia, UNA base de datos, UN dominio. Pero un mismo dueño humano (ej: la distribuidora Iporãve Paraguay) necesita operar bajo varios roles a la vez:

- Cuenta A — "Iporãve - Proveedor" (rol: proveedor)
- Cuenta B — "Iporãve - Vendedor" (rol: vendedor)
- Cuenta C — "Iporãve - Dropshipper" (rol: dropshipper)
- Cuenta D — "Iporãve - Distribuidora Admin" (rol: admin)

Cada cuenta tiene su balance, sus pedidos, su liquidación independiente. Pero el dueño quiere:

1. Saltar entre cuentas sin re-login (switcher).
2. Ver un balance consolidado de todas sus cuentas en una sola pantalla ("Mi Negocio").

Este documento define la arquitectura para soportar ese caso.

---

## 1. Estrategia de implementación

### Opciones evaluadas

**Opción A — Linked Users (grupos de cuentas)**
- Tabla `user_groups` (un grupo) + `user_group_members` (N cuentas dentro).
- Cada cuenta sigue siendo un `usuarios.id` independiente, con su propio rol y sus propios datos.
- Una cuenta es designada `owner` del grupo y tiene permiso para ver agregados.
- Ventajas: máxima flexibilidad, no rompe nada de la arquitectura actual de roles únicos por usuario, RLS sigue funcionando igual, fácil de auditar.
- Desventajas: requiere UI extra (switcher, página agregada), una capa más en queries de balance.

**Opción B — Owner ID (campo en usuarios)**
- Agregar `usuarios.owner_user_id` apuntando al "dueño real".
- Ventajas: simple, una sola columna.
- Desventajas: jerarquía rígida (un solo nivel), difícil migrar después a estructura más rica, no permite que dos personas físicas compartan dueñazgo, no escala a permisos compartidos.

**Opción C — Roles array (un usuario con múltiples roles)**
- Reemplazar `usuarios.rol` por `usuarios.roles: text[]`.
- Ventajas: una sola cuenta, balance natural agregado.
- Desventajas: ROMPE TODA LA ARQUITECTURA actual. Cada query de RLS, cada `_perfilCompleto()`, cada panel asume un rol único. Los balances financieros NO se separarían por rol (un solo bolsillo), lo cual contradice el requerimiento del dueño de tener "cada cuenta con balance financiero por separado".

### Recomendación: **Opción A — Linked Users**

Es la única que cumple los tres requisitos simultáneamente:
1. Cada cuenta conserva su balance independiente.
2. El dueño puede ver un agregado opt-in.
3. No rompe la arquitectura actual de un-usuario-un-rol ni la RLS de Supabase.

Además se alinea con la dirección que ya planteó el usuario.

---

## 2. Schema de base de datos

```sql
-- Grupo de cuentas pertenecientes a un mismo dueño humano
CREATE TABLE user_groups (
  id          bigserial PRIMARY KEY,
  owner_id    int NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
  nombre      text NOT NULL,
  descripcion text,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Miembros (cuentas) del grupo
CREATE TABLE user_group_members (
  group_id     bigint NOT NULL REFERENCES user_groups(id) ON DELETE CASCADE,
  user_id      int    NOT NULL REFERENCES usuarios(id)    ON DELETE CASCADE,
  rol_en_grupo text   NOT NULL DEFAULT 'member',  -- 'owner' | 'admin' | 'member'
  added_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (group_id, user_id)
);

CREATE INDEX idx_ugm_user  ON user_group_members(user_id);
CREATE INDEX idx_ugm_group ON user_group_members(group_id);
CREATE UNIQUE INDEX idx_ug_owner_nombre ON user_groups(owner_id, nombre);

-- Log de auditoría de cambios de contexto
CREATE TABLE user_group_context_log (
  id           bigserial PRIMARY KEY,
  group_id     bigint REFERENCES user_groups(id) ON DELETE SET NULL,
  from_user_id int,
  to_user_id   int,
  actor_id     int NOT NULL,        -- quién hizo el switch
  ip           inet,
  user_agent   text,
  created_at   timestamptz NOT NULL DEFAULT now()
);
```

### Reglas de integridad
- Un `user_id` puede pertenecer a varios grupos en teoría, pero en práctica restringimos a UN grupo activo (índice único parcial recomendado):
  ```sql
  CREATE UNIQUE INDEX idx_ugm_unique_user ON user_group_members(user_id);
  ```
- El `owner_id` debe estar también en `user_group_members` con `rol_en_grupo='owner'` (validar por trigger o lógica de aplicación).

### RLS (Row Level Security)
- `user_groups`: SELECT permitido si `auth.uid()` pertenece al grupo o es owner.
- `user_group_members`: SELECT igual. INSERT/DELETE solo si el actor es `owner`.
- Las tablas existentes (pedidos, balance, comisiones, etc.) NO cambian su RLS. Cada cuenta sigue viendo solo lo suyo. El agregado se construye en el worker con privilegios elevados, no en el cliente.

---

## 3. UX del switcher de contexto

### Ubicación
Header global, top-right, al lado del avatar del usuario.

### Estados visuales
- **Si el usuario no pertenece a un grupo:** no se muestra switcher (estado actual = comportamiento legacy).
- **Si pertenece a un grupo:** se muestra como pill clickeable:
  ```
  [👤 Iporãve - Distribuidora ▼]
  ```
- **Click → dropdown:**
  ```
  ┌──────────────────────────────┐
  │ Iporãve - Distribuidora ✓    │  ← cuenta activa
  │ Iporãve - Proveedor          │
  │ Iporãve - Vendedor           │
  │ Iporãve - Dropshipper        │
  ├──────────────────────────────┤
  │ 📊 Ver Mi Negocio (agregado) │
  │ ＋ Crear nueva cuenta        │
  └──────────────────────────────┘
  ```

### Cambio de contexto
1. Click en una cuenta del dropdown.
2. Frontend llama `POST /api/grupos/switch-context` con `to_user_id`.
3. Worker valida que ambas cuentas pertenezcan al mismo grupo y que el actor sea owner del grupo (o que la cuenta destino esté explícitamente delegada al actor).
4. Worker emite nuevo JWT con `sub = to_user_id`.
5. Frontend reemplaza el token, limpia caches del estado en memoria y hace soft-reload de la página actual (sin perder URL).
6. Se registra entrada en `user_group_context_log`.

### "+ Crear nueva cuenta"
- Abre modal: nombre interno, rol a asignar, email (opcional, puede reusar email del owner).
- Crea registro en `usuarios` + entrada en `user_group_members`.
- Si no hay email único, se permite reusar el email del owner pero con flag `cuenta_secundaria = true`.

---

## 4. Vista agregada — `PAGES.mi_negocio`

### Acceso
- Solo visible si el usuario actual es `owner` de algún `user_group`.
- Ruta: `/mi-negocio`.
- En el sidebar/nav del rol admin (y de cualquier cuenta que sea owner de grupo).

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Mi Negocio — Balance consolidado de mis cuentas        │
├─────────────────────────────────────────────────────────┤
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────┐  │
│  │💰 Ganado  │ │✅ Cobrado │ │⚠ Pendiente│ │📊 Pedid.│  │
│  │ ₲ 50M     │ │ ₲ 38M     │ │ ₲ 12M     │ │  420    │  │
│  └───────────┘ └───────────┘ └───────────┘ └─────────┘  │
├─────────────────────────────────────────────────────────┤
│  Desglose por cuenta                                    │
│  ┌──────────────┬────────┬─────────┬────────┬────────┐  │
│  │ Cuenta       │ Rol    │ Ganado  │ Cobrado│ Pend.  │  │
│  │ Proveedor    │ prov.  │ ₲ 20M   │ ₲ 15M  │ ₲ 5M   │  │
│  │ Vendedor     │ vend.  │ ₲ 15M   │ ₲ 12M  │ ₲ 3M   │  │
│  │ Dropshipper  │ drop.  │ ₲ 10M   │ ₲ 8M   │ ₲ 2M   │  │
│  │ Admin        │ admin  │ ₲ 5M    │ ₲ 3M   │ ₲ 2M   │  │
│  └──────────────┴────────┴─────────┴────────┴────────┘  │
│                                                         │
│  📊 % de ingresos por rol (donut chart)                 │
│                                                         │
│  Click en una fila → switch context a esa cuenta        │
└─────────────────────────────────────────────────────────┘
```

### Datos que NO se muestran en la vista agregada (privacy)
- Lista de clientes individuales de cada cuenta.
- Detalle de pedidos.
- Mensajes/chats.
- Solo totales financieros agregados.

Para ver el detalle de una cuenta hay que **switchear contexto** a ella.

---

## 5. Endpoints del worker

| Método | Ruta                                | Descripción                                        | Auth                |
|--------|-------------------------------------|----------------------------------------------------|---------------------|
| POST   | `/api/grupos/create`                | Crear un grupo. El llamante queda como owner.      | usuario autenticado |
| POST   | `/api/grupos/add-member`            | Agregar cuenta existente al grupo.                 | owner del grupo     |
| POST   | `/api/grupos/remove-member`         | Quitar cuenta del grupo.                           | owner del grupo     |
| POST   | `/api/grupos/create-account`        | Crear cuenta nueva y agregarla al grupo.           | owner del grupo     |
| GET    | `/api/grupos/mios`                  | Listar grupos a los que pertenece el usuario.      | usuario autenticado |
| GET    | `/api/grupos/:id/miembros`          | Listar miembros del grupo.                         | miembro del grupo   |
| GET    | `/api/grupos/mi-negocio`            | Vista agregada de balances.                        | owner del grupo     |
| POST   | `/api/grupos/switch-context`        | Cambiar JWT activo a otra cuenta del grupo.        | owner / delegado    |
| GET    | `/api/grupos/auditoria`             | Log de cambios de contexto.                        | owner del grupo     |

### Contrato del agregado (`GET /api/grupos/mi-negocio`)
```json
{
  "grupo": { "id": 12, "nombre": "Iporãve Paraguay" },
  "totales": {
    "ganado":   50000000,
    "cobrado":  38000000,
    "pendiente":12000000,
    "pedidos":  420
  },
  "por_cuenta": [
    {
      "user_id": 101,
      "nombre": "Iporãve - Proveedor",
      "rol": "proveedor",
      "ganado": 20000000,
      "cobrado": 15000000,
      "pendiente": 5000000,
      "pedidos": 180
    }
    // ...
  ]
}
```

El worker calcula sumas con privilegios elevados (service role) y NUNCA expone IDs de pedidos/clientes individuales en este endpoint.

---

## 6. Reglas de seguridad

1. **Owner exclusivo de mutaciones del grupo.** Solo el `owner_id` puede agregar/quitar miembros o crear cuentas nuevas dentro del grupo.
2. **RLS preservada por cuenta.** Cada cuenta sigue viendo solo sus propios datos. La pertenencia a un grupo NO da acceso lateral a los datos completos de otras cuentas del grupo.
3. **Switch de contexto auditado.** Cada `/switch-context` queda en `user_group_context_log` con IP, user-agent, timestamps y from/to user_id.
4. **JWT rotativo en switch.** Se emite token nuevo, el viejo se invalida (lista de revocación o tiempo corto de expiración).
5. **Privacidad en agregado.** El endpoint `/mi-negocio` devuelve solo totales numéricos por cuenta, nunca PII de clientes ni detalle de pedidos.
6. **Rate limit de switch.** Máximo N switches por minuto para detectar abuso/scripting.
7. **Notificación de cambios de membresía.** Cuando se agrega o se quita una cuenta del grupo, se notifica por email/push a TODOS los miembros del grupo.
8. **Suspensión propagada.** Si el owner es suspendido por seguridad, el grupo entero queda en modo lectura hasta resolverse.

---

## 7. Migración de usuarios existentes

### Detección automática
Tool admin que busca usuarios con:
- Mismo `email` (raro porque hay unique, pero puede haber emails alias).
- Mismo `telefono` exacto.
- Mismo `documento` / RUC.

Y los presenta como "candidatos a agrupar" en la UI de superadmin.

### Merge assistant
- UI superadmin: "Estos 4 usuarios parecen ser la misma persona. ¿Crear grupo?"
- Permite seleccionar cuál cuenta será owner.
- Crea `user_groups` + `user_group_members` para todas.
- NO toca los datos transaccionales de cada cuenta.

### Backward compatibility
- Usuarios que NO están en ningún grupo siguen funcionando exactamente igual.
- El switcher simplemente no aparece.
- La página `/mi-negocio` no es accesible.
- Cero impacto en sesiones existentes.

---

## 8. Caso de uso real — Iporãve Paraguay

Paso a paso:

1. Superadmin crea grupo "Iporãve Paraguay" con owner = `usuarios.id = 1` (admin principal).
2. Agrega las 4 cuentas:
   - Iporãve - Proveedor (rol: proveedor)
   - Iporãve - Vendedor (rol: vendedor)
   - Iporãve - Dropshipper (rol: dropshipper)
   - Iporãve - Distribuidora Admin (rol: admin) ← esta es el owner
3. El dueño hace login con la cuenta admin.
4. En el header aparece el switcher: `[Iporãve - Distribuidora ▼]`.
5. Click → ve las 4 cuentas → switchea a "Proveedor" → trabaja como proveedor.
6. Vuelve, switchea a "Vendedor" → trabaja como vendedor.
7. Click en "📊 Mi Negocio" → ve los 4 balances consolidados.
8. Toma decisiones de negocio con visión completa.

---

## 9. Conexión con suscripciones

### Modelo
- Un `user_group` puede tener UNA suscripción asociada que cubre a TODAS las cuentas miembros.
- La feature "multi-cuenta" se desbloquea a partir del tier **Business** (o equivalente).

### Schema sugerido
```sql
ALTER TABLE user_groups
  ADD COLUMN suscripcion_id bigint REFERENCES suscripciones(id),
  ADD COLUMN tier text;  -- 'free' | 'pro' | 'business' | 'enterprise'
```

### Reglas
- Tier `free` / `pro`: no puede tener grupo (máximo 1 cuenta).
- Tier `business`: hasta 5 cuentas en el grupo.
- Tier `enterprise`: cuentas ilimitadas + auditoría avanzada + API.
- Si el tier baja, no se borran cuentas: el grupo queda "congelado" en modo read-only hasta upgrade o desagrupación manual.

### Facturación
- La factura va al `owner_id`.
- El balance financiero de cada cuenta NO se ve afectado por la suscripción del grupo.

---

## 10. Plan de implementación

### Sprint 1 — Backend base (1 día)
- [ ] Migration SQL (user_groups, user_group_members, user_group_context_log, índices, RLS).
- [ ] Endpoints worker:
  - POST `/api/grupos/create`
  - POST `/api/grupos/add-member`
  - POST `/api/grupos/remove-member`
  - GET `/api/grupos/mios`
- [ ] Tests unitarios de cada endpoint.

### Sprint 2 — Switcher UI (1 día)
- [ ] Componente `<GroupSwitcher>` en el header.
- [ ] Endpoint `POST /api/grupos/switch-context` con emisión de JWT nuevo.
- [ ] Manejo del soft-reload sin perder URL.
- [ ] Logging en `user_group_context_log`.

### Sprint 3 — Vista agregada (1 día)
- [ ] Endpoint `GET /api/grupos/mi-negocio`.
- [ ] Página `PAGES.mi_negocio` con cards + tabla + donut chart.
- [ ] Permisos: solo visible para owners de grupo.
- [ ] Tests visuales (tester-visual.py).

### Sprint 4 — Conexión con suscripciones (0.5 día)
- [ ] Columnas `tier` y `suscripcion_id` en `user_groups`.
- [ ] Gating del feature según tier.
- [ ] UI: si el tier no alcanza, mostrar paywall.

### Sprint 5 — Migración assistant (futuro, no bloqueante)
- [ ] UI superadmin de detección de duplicados.
- [ ] Wizard de merge a grupo.
- [ ] Notificaciones a los usuarios afectados.

### Total estimado: 3.5 días de trabajo de desarrollo (sin merge assistant).

---

## 11. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Confusión del usuario sobre qué cuenta está activa | Banner sutil persistente "Activo como: X" en cada página |
| Abuso del switcher para evadir auditoría | Log inmutable `user_group_context_log` + alertas si > N switches/hora |
| Suplantación si JWT del owner se filtra | JWT del switch contiene claim `via_group=true` + IP binding opcional |
| Inconsistencia de balances si una cuenta cae del grupo | Soft-delete con flag `removed_at` y conservar histórico financiero en cada cuenta |
| RLS rota al introducir nuevas tablas | Tests automatizados de RLS en CI |

---

## 12. Decisiones abiertas (pendientes de validar con el usuario)

1. ¿Puede una cuenta pertenecer a **más de un grupo**? (Recomendación: NO, mantener relación 1-a-N para evitar complejidad.)
2. ¿El owner puede delegar permiso de switch a otra cuenta del grupo (ej: contador)? (Recomendación: SÍ, con `rol_en_grupo='admin'`.)
3. ¿La vista agregada incluye también métricas no-financieras (clientes únicos, calificaciones, etc.)? (Recomendación: SÍ en versión 2, NO en MVP.)
4. ¿Cuál es el límite de cuentas por grupo en cada tier exactamente? (A definir con el área comercial.)

---

**Fin del documento.**
