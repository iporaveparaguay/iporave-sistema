# 🚨 AVENTÓN URGENTE — Claude Code chat nuevo

> **Quién te escribe:** la sesión Claude anterior que cerró ayer a las 02:00 UTC y escribió el RELEVO.
> **Para qué:** darte instrucciones EJECUTABLES sin que pienses ni explores. Copiá-pegá comandos. NO HAGAS ANÁLISIS PREVIO de este mensaje. Ejecutá en orden.
> **Tiempo estimado total:** 60–90 minutos para todo.

---

# 🛑 LO QUE NO TENÉS QUE HACER (regla universal)

- **NO lanzar Explore agents** para encontrar selectores CSS, funciones, etc. Usá `Grep` directo, 1 vez, listo.
- **NO leer index.html entero**. Tiene 9.5K líneas. Usá `Grep -n` para encontrar la línea y `Read` con offset+limit chico.
- **NO relanzar `codex-solucionador.py`**. Está roto. Ignoralo.
- **NO usar `git add .` ni `-A`**. Siempre archivo específico.
- **NO commitear sin antes correr `node validate.js`** si tocaste `public/index.html`.
- **NO hacer auditorías del proyecto.** El usuario ya las hizo.
- **NO preguntarle al usuario qué hacer.** Está todo acá. Solo reportar al final.

---

# ⚡ PASO 1 — LIMPIEZA INMEDIATA (5 min)

## 1.1 Matar orquestadores Python idle
**Razón:** llevan 6+ horas sin reportar al pizarrón, consumen RAM sin producir nada. Dejar solo los 2 útiles.

```powershell
Get-WmiObject Win32_Process -Filter "name='python.exe'" |
  Where-Object { $_.CommandLine -match 'orquestador-(features|catalog|worker|paginas)\.py|orquestador\.py$|codex-solucionador\.py' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Output "Matado PID $($_.ProcessId)" }
```

## 1.2 Verificar que quedaron solo supervisor + cerebro-monitor
```powershell
Get-WmiObject Win32_Process -Filter "name='python.exe'" | Select-Object ProcessId, CommandLine | Format-List
```
**Esperado:** SOLO 2 procesos:
- `orquestador-supervisor.py`
- `cerebro-monitor.py`

Si ves más → repetir 1.1.

## 1.3 Git status — decidir archivos sueltos
```powershell
cd C:\Users\USUARIO\iporave-sistema; git status --short
```

**Política rápida (no pensar mucho):**
- `?? .agentes/*.py` (scripts de agentes) → **DEJAR sin commitear** (son locales/operativos)
- `?? .agentes/TAREA_*.md` y `?? .agentes/RELEVO_*.md` → **commitear** (documentación)
- `?? .agentes/playwright_state.json` → **NO commitear** (tiene tokens)
- `?? .agentes/pool_estado.json` → **NO commitear** (estado runtime)
- `?? abrir-pizarron-iporave.bat` → **commitear**
- `?? public/App.vue`, `?? public/css/`, etc → **commitear si son intencionales, sino borrar**
- `M .aider.chat.history.md`, `M .aider.input.history` → **NO commitear** (cache local)

**Acción concreta — solo commitear los .md de docs que falten:**
```powershell
cd C:\Users\USUARIO\iporave-sistema
git add .agentes/TAREA_DATOS_PRUEBA_EXTENDIDOS.md .agentes/TAREA_PEDIDOS_BOTONES_OVERFLOW.md .agentes/TAREA_UI_LOGIN_MOBILE.md .agentes/PLAYBOOK_SUPERVISOR.md
git status --short
```
Si está OK → `git commit -m "docs: agregar tareas pendientes y playbook supervisor"` → `git push origin main`

Para los archivos que NO querés commitear pero molestan en `git status`, agregarlos a `.gitignore`:
```powershell
@"

# Archivos locales de agentes
.agentes/playwright_state.json
.agentes/pool_estado.json
.agentes/test-screenshots/
.agentes/pyoverrides/
.aider.chat.history.md
.aider.input.history
.aider.tags.cache.v4/
"@ | Add-Content C:\Users\USUARIO\iporave-sistema\.gitignore

git add .gitignore
git commit -m "chore: ignorar archivos locales de agentes"
git push origin main
```

---

# ⚡ PASO 2 — DATOS FICTICIOS COMPLETOS (30 min)

**Objetivo:** que el sistema tenga datos realistas para la prueba de la tarde. SIN datos no se puede probar nada.

## 2.1 Ver qué hace `crear-datos-prueba.py` actualmente
```powershell
Get-Content C:\Users\USUARIO\iporave-sistema\.agentes\crear-datos-prueba.py | Select-Object -First 50
```

## 2.2 Ampliarlo o usar Supabase directo
Si `crear-datos-prueba.py` ya funciona y solo le faltan datos, ampliar las listas dentro del script. Si no funciona, usar el SQL Editor de Supabase con este SQL listo:

**SQL para Supabase SQL Editor — copy-paste tal cual:**
```sql
-- USUARIOS (ya hay 1, agregar más)
-- Nota: la creación de usuarios reales requiere auth.users via signUp. Saltearse esto y crear directo en tabla usuarios solo si NO necesitan login.
-- Mejor: crearlos desde el panel superadmin de la app, que dispara el flujo correcto.

-- PEDIDOS — agregar 4 más para completar 10 con datos llenos
INSERT INTO pedidos (cliente, telefono_cliente, address, productos, monto_total, estado, drop_id, vendedor_id, delivery_id, prioridad, observaciones) VALUES
('María Rodríguez', '+595 981 234 567', 'Av. Mariscal López 2350, Asunción', '[{"id":1,"nombre":"Yerba Mate 1kg","cant":2,"precio":35000}]'::jsonb, 70000, 'Pendiente', NULL, 1, NULL, false, 'Llamar antes de llegar'),
('Roberto Núñez', '+595 985 111 222', 'Calle Caaguazú 145, Lambaré', '[{"id":3,"nombre":"Azúcar 1kg","cant":5,"precio":12000}]'::jsonb, 60000, 'En camino', NULL, 1, 2, true, 'PRIORIDAD - entrega urgente antes 18:00'),
('Patricia Gómez', '+595 982 333 444', '-25.2890,-57.6512', '[{"id":11,"nombre":"Auriculares Bluetooth","cant":1,"precio":85000}]'::jsonb, 85000, 'Despachado', NULL, 1, 2, false, 'Coordenadas GPS exactas'),
('Andrés Villalba', '+595 971 555 666', 'Av. Eusebio Ayala 4521, Asunción', '[{"id":10,"nombre":"Lavandina 2L","cant":3,"precio":6500},{"id":12,"nombre":"Remera Algodón M","cant":2,"precio":35000}]'::jsonb, 89500, 'Entregado', NULL, 1, 2, false, 'Cliente recurrente');

-- CATÁLOGO — agregar 4 más para completar 10
INSERT INTO catalogo (nombre, descripcion_html, presentaciones, foto_url, categoria, stock, activo) VALUES
('Pan Casero 500g', '<p>Pan artesanal recién horneado</p>', '[{"presentacion":"500g","precio":8000}]'::jsonb, 'https://picsum.photos/seed/pan/400/400', 'Alimentos', 50, true),
('Café Molido 250g', '<p>Café 100% paraguayo molido fino</p>', '[{"presentacion":"250g","precio":25000},{"presentacion":"500g","precio":45000}]'::jsonb, 'https://picsum.photos/seed/cafe/400/400', 'Alimentos', 30, true),
('Cargador USB-C', '<p>Cargador rápido 25W compatible Samsung/iPhone</p>', '[{"presentacion":"25W","precio":45000}]'::jsonb, 'https://picsum.photos/seed/cargador/400/400', 'Tecnología', 20, true),
('Detergente Lavavajillas', '<p>Detergente concentrado 750ml</p>', '[{"presentacion":"750ml","precio":12000}]'::jsonb, 'https://picsum.photos/seed/detergente/400/400', 'Limpieza', 100, true);
```

**ATENCIÓN:** los nombres exactos de columnas pueden variar. Si el INSERT da error de columna inexistente, hacer primero:
```sql
SELECT column_name FROM information_schema.columns WHERE table_name='pedidos';
SELECT column_name FROM information_schema.columns WHERE table_name='catalogo';
```
y ajustar el INSERT.

## 2.3 Crear usuarios de prueba desde el panel
Hacer login en https://iporave-sistema.vercel.app con la cuenta superadmin (iporaveparaguay@gmail.com / ivan12345) y crear desde la UI:
- **vendedor1@test.com** / password: test1234 / rol: vendedor / nombre: Juan Vendedor
- **vendedor2@test.com** / rol: vendedor / nombre: Ana Vendedora
- **delivery1@test.com** / rol: delivery / nombre: Carlos Delivery / vehículo: moto / patente: ABC123
- **delivery2@test.com** / rol: delivery / nombre: Luis Delivery / vehículo: auto / patente: XYZ789
- **dropshipper1@test.com** / rol: dropshipper / nombre: Marta Drop / RUC: 80012345-6
- **empresa1@test.com** / rol: empresa / nombre comercial: Iporãve Test S.A. / RUC: 80098765-4

Esto NO se puede hacer con SQL directo porque requiere crear cuentas en `auth.users` (Supabase Auth).

---

# ⚡ PASO 3 — FIXES MOBILE (45 min)

Todo lo que sigue es **CSS dentro del bloque `<style>` de `public/index.html`**. Para cada fix:
1. `Grep -n "<selector>" public/index.html` para encontrar dónde está
2. `Edit` directo con el código de abajo
3. `node validate.js` al terminar TODOS los fixes (no después de cada uno)
4. Commit + push 1 vez al final

## 3.1 Botón ⋮ a la DERECHA en cards de pedido
**Síntoma actual:** el botón ⋮ está en el medio o pegado al nombre del cliente. Tiene que estar a la derecha del card.

**Fix CSS:** buscar `.order-card` o el contenedor de cada pedido y agregar/modificar:
```css
.order-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.order-card .order-info {
  flex: 1;
  min-width: 0;
}
.order-menu-btn {
  margin-left: auto;
  flex-shrink: 0;
  padding: 10px 12px;
  min-width: 44px;
  min-height: 44px;
}
```

Si los selectores son distintos, ajustar según lo que aparezca en el HTML. Grep para `class="order-` o `class="ord-` para encontrarlos.

## 3.2 Padding izquierdo uniforme en TODAS las secciones con borde amarillo
**Síntoma:** en Balance, Usuarios, Zona/Entrega, Catálogo los nombres/datos quedan pegados al borde izquierdo amarillo. La sección Liquidación ya se ve bien — usar esa medida.

**Fix CSS:** buscar el selector común de "card amarilla" — probablemente `.lcard2` o `.section-card` o similar. Agregar:
```css
.lcard2, .section-card, .data-card {
  padding-left: 16px;
  padding-right: 16px;
}
@media (max-width: 768px) {
  .lcard2, .section-card, .data-card {
    padding-left: 14px;
    padding-right: 14px;
  }
}
```

**Cómo verificar cuál es el selector real:** buscar en index.html
```powershell
Select-String -Path C:\Users\USUARIO\iporave-sistema\public\index.html -Pattern 'class="lcard2|class="section-' | Select-Object -First 5
```

## 3.3 Topbar mobile — título arriba, hamburguesa abajo-izquierda
**Síntoma:** en mobile, título de sección (ej "Pedidos") y botón ☰ se pisan.

**Fix CSS:**
```css
@media (max-width: 768px) {
  .topbar {
    flex-direction: column;
    align-items: stretch;
    padding-bottom: 4px;
  }
  .topbar .section-title {
    text-align: center;
    font-size: 18px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 8px 0 4px 0;
  }
  .topbar .menu-toggle, .topbar .hamburger {
    position: absolute;
    bottom: 4px;
    left: 12px;
    z-index: 10;
  }
  .topbar .actions-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: space-around;
    padding: 8px 12px;
  }
}
```

## 3.4 Campanita mobile — más chica + transparencia al scroll
**Síntoma:** la `#codexNotifBell` tapa info al hacer scroll.

**Fix CSS:**
```css
@media (max-width: 768px) {
  #codexNotifBell {
    width: 44px;
    height: 44px;
    right: 12px;
    transition: opacity 0.3s ease;
  }
  #codexNotifBell.scrolling-down {
    opacity: 0.35;
  }
}
```

**Fix JS — agregar al final del bloque JS principal:**
```javascript
(function(){
  let lastScroll = 0;
  let scrollTimeout = null;
  const bell = document.getElementById('codexNotifBell');
  if (!bell) return;
  window.addEventListener('scroll', function(){
    const now = window.scrollY;
    if (now > lastScroll && now > 80) {
      bell.classList.add('scrolling-down');
    }
    lastScroll = now;
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(function(){
      bell.classList.remove('scrolling-down');
    }, 600);
  }, { passive: true });
})();
```

Buscá una zona del JS donde tengas otros bloques IIFE similares y pegalo ahí. Si no hay, agregarlo al final del último bloque `<script>`.

## 3.5 Validar y commitear todos los fixes mobile juntos
```powershell
cd C:\Users\USUARIO\iporave-sistema
node validate.js
```
Si pasa:
```powershell
git add public/index.html
git commit -m "fix(mobile): ⋮ derecha en cards, padding uniforme amarillo, topbar reorganizado, campanita transparente scroll"
git push origin main
```

---

# ⚡ PASO 4 — TESTER VISUAL (10 min)

```powershell
cd C:\Users\USUARIO\iporave-sistema
python .agentes/tester-visual.py --user iporaveparaguay@gmail.com --pass ivan12345
```

**Esperado:** screenshots en `.agentes/test-screenshots/` + reporte de Gemini Vision.

**Si falla con 401** (token Supabase expiró): re-ejecutar, hace login fresco automáticamente.

**Si genera muchos hallazgos:** ignorar todo lo que NO sea bloqueante para el lanzamiento. Solo arreglar:
- Errores de consola visibles
- Botones que no responden
- Datos que no cargan

---

# ⚡ PASO 5 — SMOKE TEST POST-DEPLOY (5 min)

Vercel auto-deploya en ~60s después de push. Después de PASO 3.5:

1. Esperar 90 segundos
2. Abrir https://iporave-sistema.vercel.app en navegador
3. **Login + ir a Pedidos:** ¿cards se ven con ⋮ a la derecha? ¿el padding del recuadro amarillo es uniforme?
4. **DevTools → toggle device toolbar → iPhone SE (375px):** verificar mobile
5. **Consola del navegador:** que no haya errores en rojo

---

# 📞 REPORTE FINAL AL USUARIO

Cuando termines los 5 pasos, mandarle al usuario UN mensaje conciso en español, máximo 8 líneas:

```
Listo. Ejecuté el aventón completo:
1. Maté 6 orquestadores Python idle. Quedan vivos supervisor + cerebro-monitor.
2. Datos ficticios: agregué 4 pedidos y 4 productos al catálogo. Usuarios de prueba: [pendiente / creados N].
3. Fixes mobile: ⋮ a la derecha, padding uniforme, topbar reorganizado, campanita transparente. Commit XXXXX.
4. Tester visual corrió, hallazgos críticos: [ninguno / lista].
5. Smoke test Vercel OK [o problema encontrado].

¿Seguimos con [siguiente cosa]? ¿O probás vos manualmente primero?
```

**Y PARAR.** No empezar otra tarea hasta que el usuario apruebe.

---

# 🧠 REGLAS QUE TENÉS QUE INTERNALIZAR PARA EL RESTO DE LA SESIÓN

1. **Fix de 1–5 líneas → Edit directo.** Sin Explore, sin agentes.
2. **Fix de 5–50 líneas → 1 Aider focal.** Solo si vas a tocar mucho HTML/JS.
3. **Fix de 50+ líneas o multi-archivo → pedir confirmación al usuario.**
4. **Auditorías solo cuando el usuario las pida explícitamente.**
5. **No relanzar agentes Python rotos.** Si fallan 3 veces, deprecarlos.
6. **No usar `codex-solucionador.py`.** Está roto.
7. **Smoke test post-deploy obligatorio.**
8. **`git add <archivo>` específico, nunca `.` ni `-A`.**
9. **`node validate.js` antes de commit a `index.html`** — siempre.
10. **Reportar conciso y parar.** No iniciar siguiente paso sin orden.

---

# 📁 ARCHIVOS DE REFERENCIA (ya están en `.agentes/`)

- `RELEVO_CLAUDE_2026-05-14.md` — handoff completo (ya lo leíste)
- `TAREA_PRUEBA_LANZAMIENTO.md` — checklist completa de pruebas
- `TAREA_MOBILE_UX_FIXES.md` — detalles de los fixes mobile (más contexto si lo necesitás)
- `PLAYBOOK_SUPERVISOR.md` — reglas permanentes
- `crear-datos-prueba.py` — script de datos (ampliarlo si hace falta)
- `tester-visual.py` — tester con Playwright

---

**FIN DEL MENSAJE. NO ANALIZÁS, EJECUTÁS. EMPEZÁ POR EL PASO 1.**

— Claude sesión anterior, 2026-05-14 16:00 UTC
