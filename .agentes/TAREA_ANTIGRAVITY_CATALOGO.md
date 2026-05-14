# TAREA PARA ANTIGRAVITY — Catálogo y páginas públicas
**Fecha:** 2026-05-13
**Asignado por:** Claude Code
**Prioridad:** ALTA
**Estado:** Tareas previas completadas — nuevas tareas asignadas

---

## TAREAS PREVIAS — COMPLETADAS

- catalog-filtros-visual [x]
- catalog-precio [x]
- catalog-empty [x]
- catalog-footer [x]
- catalog-mobile-nav [x]
- paginas-meta-tags commiteado en 7f3aa09
- catalog.html commiteado en 8ffa191

---

## NUEVAS TAREAS

### TAREA 4 — Busqueda y ordenamiento en catalogo

Archivo: `public/catalog.html`

1. Agregar input de busqueda encima de los botones de filtro por categoria:
   - `<input type="text" id="catalogSearch" placeholder="Buscar producto...">`
   - Estilo: ancho 100%, border-radius:8px, border:1px solid var(--border), padding:8px 12px, margin-bottom:12px
   - Al escribir: filtrar productos que contengan el texto en nombre o descripcion (JS vanilla, sin API)

2. Agregar select de ordenamiento al lado del input:
   - Opciones: "Mayor precio", "Menor precio", "Nombre A-Z"
   - Al cambiar: reordenar la lista de productos mostrada

3. Verificar que catalog.html abre OK, commit, push

---

### TAREA 5 — Mejorar modal de detalle de producto

Archivo: `public/catalog.html`

Si ya tiene modal: verificar que al hacer click en un producto:
- Se muestra imagen grande
- Precio prominente
- Boton "Agregar al carrito" con feedback visual (texto cambia a "Agregado" por 2 segundos)
- Boton cerrar (X) funcional
- Swipe para cerrar en mobile con JavaScript vanilla

Si NO tiene modal: crear uno simple con esos elementos.

---

### TAREA 6 — Persistencia del carrito en localStorage

Archivo: `public/catalog.html`

- Al agregar al carrito: `localStorage.setItem('iporave_cart', JSON.stringify(carrito))`
- Al cargar la pagina: recuperar carrito de localStorage si existe
- Badge con cantidad de items en el icono del carrito
- Boton "Vaciar carrito" que limpia localStorage y resetea

---

## ORDEN SUGERIDO

1. TAREA 4 (busqueda + ordenamiento) — mas impacto, mas rapido
2. TAREA 6 (localStorage) — independiente de TAREA 5
3. TAREA 5 (modal mejorado) — si ya hay base

---

## REGLAS CRITICAS

- NUNCA tocar public/index.html — zona de Claude Code / Codex
- NUNCA poner </script> dentro de strings JS — siempre: '<scr'+'ipt>'
- Solo trabajar en public/catalog.html y paginas publicas listadas
- NO tocar Worker ni archivos Python
- Commitear cada tarea separado con mensaje descriptivo
- validate.js no aplica para catalog.html (no tiene el formato de index.html)

## COMO REPORTAR AL PIZARRON

```powershell
$body = @{
  agente = 'Antigravity'
  tarea = 'nombre-tarea'
  archivos = 'public/catalog.html'
  estado = 'Finalizado'
  resumen = 'Que se hizo exactamente'
} | ConvertTo-Json -Compress
Invoke-RestMethod -Uri 'https://iporave-api.iporaveparaguay.workers.dev/api/pizarron' -Method Post -ContentType 'application/json' -Body $body
```
