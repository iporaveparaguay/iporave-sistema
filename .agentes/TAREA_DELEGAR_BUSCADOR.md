# Tarea para delegar: intercambiar buscadores en página de Pedidos

## Estado actual
En `public/index.html`, página de Pedidos (`page === 'orders'`):
- **TOP — buscador nuevo bueno** (`#bgWrap`, función `_bgEnsureUI()` línea 2931):
  - Flotante `position:fixed; top:10px; left:50%`
  - Tiene 🔍 lupita en el placeholder ("Buscar pedido…")
  - Tiene dropdown con resultados en vivo (`#bgDropdown`)
  - Búsqueda inteligente — match por cliente, producto, estado
  - **Problema actual:** se posiciona ENCIMA del topbar y tapa los botones "+ Nuevo pedido", "Exportar CSV", "Excel", "PDF"
- **BOTTOM — buscador viejo** (`#fSrch`, línea 3963):
  - Está dentro de la fbar (filter bar), justo abajo de los botones
  - Es un input simple `<input type="text" id="fSrch" placeholder="🔍 Buscar pedido…" onkeyup="filtrar()">`
  - Usa `filtrar()` que filtra la tabla actual (no es búsqueda global)

## Lo que el usuario quiere
1. **Eliminar el viejo `#fSrch`** (input dentro de la fbar) — incluyendo su onkeyup y la lógica `filtrar()` solo si no se usa en otro lado
2. **Mover el nuevo `#bgWrap` a la posición del viejo** (debajo de los botones del topbar, dentro o como sustituto de la fbar)
3. **Conservar el tamaño y la lupita** del nuevo — incluyendo el dropdown
4. La búsqueda inteligente del nuevo debe seguir funcionando (cross-page, mostrar resultados con dropdown)

## Pasos sugeridos
1. En `_bgEnsureUI()` (línea 2931): cambiar el style del `wrap`:
   - Quitar `position:fixed; top:10px; left:50%; transform:translateX(-50%);`
   - Reemplazar por algo que lo deje inline en el flujo normal del DOM, dentro de la fbar
   - Ajustar el width para que se vea bien en la fbar
2. Quitar el media query `@media #bgWrap` (línea 491) que tenía hack mobile, ya no necesario
3. Quitar el bloque `<input id="fSrch">` de la fbar (línea 3963) y la función `filtrar()` si nadie más la llama
4. Verificar que el flujo de la fbar (Buscar..., Todos los estados, Todas las zonas, Todos los proveedores, fechas, botón Limpiar) siga visualmente equilibrado con el bgWrap insertado
5. Insertar el bgWrap dinámicamente dentro de la fbar (o como primer hijo de `.fbar` del módulo Pedidos) en vez de en `<body>`
6. Probar en mobile (max-width 768px) — el bgWrap debería ocupar 100% del ancho

## Archivos a tocar
- `public/index.html` líneas: 491, 2752-2756, 2931-2993, 3963 (alrededor)

## Validación
- `node validate.js` antes de commit
- Smoke test: abrir la página de Pedidos en navegador, verificar que:
  - El buscador con lupita está abajo de los botones (no encima)
  - Funciona la búsqueda con autocomplete dropdown
  - La fbar de filtros queda alineada

## Quién la puede hacer
- Codex / Aider / Antigravity — es trabajo de frontend visual y refactoring localizado, ideal para delegar
- Bajo riesgo porque está aislado a la página de Pedidos
- No toca login, auth, ni endpoints — solo UI
