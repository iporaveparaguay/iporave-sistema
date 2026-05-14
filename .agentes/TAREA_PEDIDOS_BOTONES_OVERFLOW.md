# Tarea — Diseño de botones de pedido (refinamiento visual)

## Estado actual (2026-05-14)
Se implementó menú desplegable ⋮ (dropdown). Resuelve el problema de botones apilados.
Commit: 533854a

## Próximo refinamiento visual (pendiente — BAJA PRIORIDAD)

El usuario quiere que los botones dentro del dropdown (y en general la sección ACCIONES) queden:

### Criterios de diseño
- **Eliminar**: botón redondo pequeño en una esquina, que no ocupe tanto espacio
- **Botones pequeños** (IVA, imprimir, GPS/navegar): todos del mismo tamaño exacto
- **Botones grandes** (Ver, Editar): agruparlos juntos arriba o abajo del dropdown
- **Separación**: un poquito de espacio entre grupos, no demasiado
- **Agrupación por color**: negros con negros, coloreados con coloreados (o alternar negro-color-negro)
- **Look profesional y limpio**

### Botón GPS rojo (botón confuso)
- Es el botón de "Navegar" (abre GPS para ir al domicilio del cliente)
- Necesita mejor ícono o etiqueta más clara
- Dentro del dropdown ya está como "Navegar" — revisar si así queda claro

### Dónde está el código
- CSS: buscar `.order-dropdown`, `.order-menu-btn` en index.html
- JS: buscar `_toggleOrderMenu`, `renderTable` (sección de acciones del pedido)
- Líneas aproximadas: CSS ~508-514, JS renderizado ~4067-4100

## Prioridad: BAJA — hacer cuando haya tiempo, no es urgente
