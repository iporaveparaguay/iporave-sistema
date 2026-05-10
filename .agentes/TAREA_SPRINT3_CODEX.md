# Sprint 3-A para Codex — Visual profesional + botones compactos

## Zona asignada
`public/index.html` — **SOLO líneas 2669 a 4888**. No tocar líneas 1–2668.

## Restricciones críticas
- `validate.js` debe pasar ✅ antes de reportar. Ejecutar: `node validate.js`
- No agregar CSS nuevo (el CSS está en zona de Claude, líneas 1–2668). Usar solo **inline styles**.
- No usar `</script>` sin escapar dentro de strings JS. Si necesitás ese tag, dividirlo: `'<scr'+'ipt>'`.
- No tocar `#nbCount` ni `#ntPanel` directamente.
- Respetar todas las funciones y variables definidas antes de línea 2669.

## Objetivo general
Mejorar la experiencia visual del sistema: métricas del dashboard más profesionales y botones de acción más organizados, priorizando que se vea bien en **celular** (mobile-first).

---

## Tarea 1 — Dashboard: métricas más visuales y profesionales

### Problema actual
Las métricas del dashboard (`.sgrid` / `.sc`) se ven planas. Los números son pequeños, sin jerarquía visual. No llaman la atención.

### Qué hacer
Rediseñar el HTML de los stat cards dentro de `PAGES.dashboard` (línea ~2688).  
Mantener la clase `.sgrid` para el contenedor y las clases de color existentes (`.gr`, `.bl`, `.re`, `.ac`) como referencia para el acento, pero **reescribir el interior de cada `.sc`** usando inline styles para lograr:

1. **Número grande y destacado** — el valor principal (`sval`) debe tener `font-size: 2.4rem; font-weight: 900; letter-spacing: -1px; line-height: 1`.
2. **Ícono grande** arriba del número — agregar un emoji decorativo grande (`font-size: 1.6rem; opacity: .7; margin-bottom: 4px`).
3. **Etiqueta chica abajo** — el label (`slabel`) con `font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--text2); margin-top: 4px`.
4. **Separador de color** — una barra fina de 3px en el tope de la card usando `border-top: 3px solid` con el color del rol (verde para entregados, azul para tránsito, naranja para pendientes, rojo para cancelados, violeta para comisión).
5. **La card debe verse bien en celular**: en mobile (`max-width: 480px` no disponible en inline styles, usar la clase `.sgrid` que ya aplica el grid — no cambiar el grid).

### Íconos sugeridos por métrica
- Total pedidos → 📋
- Entregados → ✅
- En tránsito → 🚴
- Pendientes → ⏳
- Cancelados/Dev. → ❌
- Ganancia neta → 💰
- Cupo delivery → 🏆
- Mis pedidos / Comisión → 💎
- Órdenes activas → 📦

### Estructura HTML objetivo (ejemplo para una card)
```html
<div class="sc gr" style="border-top:3px solid #22c55e;display:flex;flex-direction:column;align-items:center;text-align:center;padding:16px 10px">
  <div style="font-size:1.4rem;opacity:.75;line-height:1;margin-bottom:6px">✅</div>
  <div style="font-size:2.2rem;font-weight:900;letter-spacing:-1px;line-height:1;color:var(--green)">42</div>
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--text2);margin-top:5px">Entregados</div>
  <div style="font-size:12px;color:var(--text3);margin-top:2px">85% éxito</div>
</div>
```

### Roles a actualizar
Hay 5 bloques de stat cards, uno por rol:
- `admin/superadmin/vendedor` → sgrid con 6 cards (línea ~2769)
- `delivery` → sgrid con 3 cards + barra de cupo (línea ~2790)
- `dropshipper` → sgrid con 5 cards (línea ~2808)
- `proveedor` → sgrid con 4 cards (línea ~2819)
- `cliente` → sgrid con 3 cards (línea ~2828)

---

## Tarea 2 — Botones de acción en tabla de pedidos: compactos y organizados

### Problema actual
La columna "Acciones" en `renderTable` (línea ~3159) tiene hasta 9 botones en una sola fila:
`Ver | Editar | Actualizar | 📍 | IVA | 🖨️ | 🏷 | WA | ✕`

En móvil se apilan y se ven mal. El usuario lo describe como "se juntan muchísimo".

### Qué hacer
Dentro de la función `renderTable` (zona Codex), reorganizar los botones en **dos grupos** visuales:

**Grupo 1 — Acciones principales** (siempre visibles):
- `Ver` → btn-secondary
- `Editar` (solo si canEdit) → btn-primary
- `WA` → btn-blue
- `Actualizar` (solo si delivery) → btn-success

**Grupo 2 — Acciones secundarias** (en una segunda fila o separadas visualmente):
- `📍` Navegar → fondo rojo
- `IVA` → btn-secondary
- `🖨️` Guía → btn-secondary
- `🏷` Ticket → btn-secondary
- `✕` Eliminar (canEdit) → btn-danger

### Estructura HTML objetivo
```html
<div class="act-btns" style="display:flex;flex-direction:column;gap:4px;min-width:0">
  <!-- Fila 1: principales -->
  <div style="display:flex;gap:4px;flex-wrap:wrap">
    [Ver] [Editar] [WA] [Actualizar]
  </div>
  <!-- Fila 2: secundarias -->
  <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:0">
    [📍] [IVA] [🖨️] [🏷] [✕]
  </div>
</div>
```

Ajustar `padding` de los botones secundarios a `2px 6px` y `font-size: 11px` para que sean más compactos.

---

## Tarea 3 — Reducir espacio entre nombre del pedido y botones (mobile)

En la vista mobile, la columna Cliente muestra nombre + teléfono + badge de estado. Luego viene la columna de botones.

Verificar que en la columna Cliente (línea ~3175) el `div` de nombre tenga `line-height: 1.3` y `margin: 0` para que no agregue espacio extra. No cambiar la lógica, solo el estilo.

---

## Entregables

1. Métricas del dashboard rediseñadas (inline styles, todos los roles)
2. Botones de acción en tabla de pedidos organizados en 2 grupos
3. validate.js ✅ pasando
4. Reporte al Worker con resultado:
   - POST `https://iporave-worker.iporaveparaguay.workers.dev/api/notif-entrega`
   - Body: `{ "mensaje": "Sprint 3-A completado — visual profesional + botones compactos", "tipo": "codex" }`

## Nota final
- **Mobile first**: todo debe verse bien en pantalla de 360px de ancho.
- Usar variables CSS del sistema: `var(--green)`, `var(--blue)`, `var(--red)`, `var(--accent)`, `var(--cyan)`, `var(--card)`, `var(--text2)`, `var(--text3)`.
- No inventar variables nuevas — solo las que ya existen.
