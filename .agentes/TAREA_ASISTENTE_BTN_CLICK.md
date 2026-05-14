# Bug — Botón asistente IA se puede mover pero no abre al hacer click

## Síntoma
`#aiBtn` (botón flotante del asistente IA) se puede arrastrar a cualquier posición,
pero al hacer click no abre el panel del asistente (`#aiPanel`).

## Causa probable
El handler de drag (mousedown/mousemove/mouseup) interfiere con el evento click.
Cuando el usuario hace click sin mover, el drag state no se resetea correctamente
y el click queda suprimido o el panel no se muestra.

## Dónde buscar
- Buscar `#aiBtn` o `aiBtn` en index.html
- Ver función de drag (probablemente `pointerdown`, `pointermove`, `pointerup`)
- Ver función que debería abrir el panel (probablemente `toggleAiPanel()` o similar)

## Fix sugerido
Distinguir drag de click: si el mouse se movió menos de 5px entre mousedown y mouseup,
tratarlo como click (no como drag) y abrir el panel.

```js
// Ejemplo de fix
let _aiDragMoved = false;
aiBtn.addEventListener('pointerdown', e => { _aiDragMoved = false; ... });
aiBtn.addEventListener('pointermove', e => { _aiDragMoved = true; });
aiBtn.addEventListener('pointerup', e => {
  if (!_aiDragMoved) toggleAiPanel(); // fue click, no drag
});
```

## Prioridad: MEDIA — anotar para próxima sesión
