---
# Tarea — Botón scroll-to-top (#codexScrollTopBtn) — mejorar visibilidad

## Estado actual (2026-05-14)
- Fondo cambiado a `var(--bg2)` (negro/oscuro en dark mode) — commit 845e38a
- Posición: `bottom:130px` para no solaparse con el botón del asistente IA
- Funciona correctamente, scroll detecta el contenedor correcto

## Problema reportado
- El botón es negro y el borde también es oscuro → no se nota bien
- El usuario quiere que se pueda identificar visualmente como "botón para subir"
- Se ve pero no "resalta" como debería

## Opciones propuestas por el usuario
A) Efecto 3D: borde más blanco/gris claro para dar profundidad
B) Color un poco más claro que el fondo (gris medio)
C) Borde `border: 1px solid rgba(255,255,255,0.25)` o similar

## Fix sugerido
```css
#codexScrollTopBtn {
  background: var(--bg2);
  border: 1px solid rgba(255,255,255,0.20);  /* borde sutil blanco */
  box-shadow: 0 2px 8px rgba(0,0,0,.4), inset 0 1px 0 rgba(255,255,255,.08);
  color: var(--text);
}
```
Esto da efecto 3D sutil sin cambiar el color base.

Alternativa: cambiar a gris medio (`#374151`) o usar `var(--bg3)` si existe.

## Dónde está el código
- Buscar `#codexScrollTopBtn` en index.html
- CSS aprox en la zona de `.dark-mode` o sección de botones del dashboard

## Prioridad: BAJA — no urgente
