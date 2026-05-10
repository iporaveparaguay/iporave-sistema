# 📋 TAREA SPRINT 2 — ANTIGRAVITY
# Director: Claude Code

## TU TAREA: Filtros catálogo + detalle producto en catalog.html

### Archivo: public/catalog.html (ya existe)

### Qué agregar:
1. **Filtro por precio** — slider o inputs min/max
2. **Ordenar por** — precio menor, precio mayor, nombre A-Z
3. **Modal de detalle** — al hacer clic en una card muestra foto grande, descripción completa, precio, botón pedir
4. **Contador de resultados** mejorado con "X productos encontrados"

### Lo que ya existe en catalog.html:
- Grid de productos con foto, nombre, precio, categoría
- Búsqueda por texto
- Filtro por categoría (select)
- Modal de pedido con formulario WhatsApp
- Endpoint: https://iporave-api.iporaveparaguay.workers.dev/api/catalog-public

### Reglas:
- Solo tocar public/catalog.html
- NO tocar index.html bajo ningún concepto
- Vanilla JS/CSS, sin frameworks
- Mobile-first, dark mode

### Reportar al terminar:
```
curl -X POST http://localhost:1880/reporte -H "Content-Type: application/json" -d "{\"agente\":\"Antigravity\",\"tarea\":\"SPRINT2-C_filtros_catalogo\",\"archivos\":\"public/catalog.html\",\"resumen\":\"[describir qué hiciste]\",\"estado\":\"Finalizado\"}"
```
