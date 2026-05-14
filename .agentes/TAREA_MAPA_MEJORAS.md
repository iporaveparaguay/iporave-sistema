# Tarea — Mejoras visuales del mapa y pines de prioridad

## 1. Botones del mapa — más profesionales

Los botones actuales en el panel del mapa son muy "dibujitos"/cartoon.
Hay que rediseñarlos para que queden limpios y profesionales como los
del menú ⋮ de pedidos.

### Botón GPS rojo (esquina inferior derecha)
- Identificar qué hace exactamente
- Si es para centrar en la ubicación actual, cambiar ícono a 📍 o usar
  ícono SVG de GPS (como el de Google Maps)
- Cambiar el color rojo por algo más apropiado al contexto

### Botón de información (ℹ️ en círculo)
- Está descentrado respecto al botón de arriba — queda corrido al costado
- Opciones:
  A) Achicamos el botón de arriba y los ponemos en paralelo (lado a lado)
  B) Movemos el botón ℹ️ más hacia abajo y más a la derecha para separarlo
- Elegir la opción que quede más limpia visualmente

### Estilo general de botones del mapa
- Usar el mismo estilo que `.order-menu-btn` o los botones del sistema:
  `background:var(--bg2); border:1px solid var(--border2); color:var(--text)`
- Bordes redondeados consistentes con el resto del sistema
- Sombra sutil `box-shadow:var(--shadow)`

## 2. Uniformar botones en TODAS las secciones

El usuario quiere que los botones de acción en todas las secciones queden
con el mismo estilo limpio del menú ⋮ de pedidos.

Secciones a revisar:
- Mapa (descrito arriba)
- Panel de usuarios (botones de editar/eliminar usuario)
- Catálogo (botones de producto)
- Perfil (botones de editar campos)
- Dashboard (botones de acciones rápidas)

Criterio:
- Si hay 1-2 botones: dejarlos visibles pero con el mismo estilo visual
- Si hay 3+ botones: usar menú ⋮ con dropdown
- Todos deben tener área táctil mínima 44px (ya en pedidos)
- Colores consistentes: primario=naranja, secundario=neutro

## 3. Pines de prioridad — animación + notificación

### Animación del pin
Cuando un pedido tiene prioridad alta, el pin en el mapa debe:
- **Sacudirse** (shake animation) en loop
- **Emitir ondas de sonar** (pulso expansivo tipo radar/ping)

CSS sugerido:
```css
@keyframes pin-shake {
  0%,100%{transform:translateX(0)}
  25%{transform:translateX(-3px) rotate(-3deg)}
  75%{transform:translateX(3px) rotate(3deg)}
}
@keyframes pin-sonar {
  0%{box-shadow:0 0 0 0 rgba(239,68,68,.6)}
  100%{box-shadow:0 0 0 24px rgba(239,68,68,0)}
}
.pin-priority{
  animation:pin-shake 0.5s infinite, pin-sonar 1.5s infinite;
}
```

### Notificación al Delivery
Cuando un pedido se marca como prioridad, enviar push notification al
delivery asignado con el texto: "⚡ Pedido #X marcado como PRIORIDAD"

Verificar si ya hay algo similar en el sistema (puede estar en notif-entrega.js
del worker o en la lógica de tiempo real de Supabase).

## 4. Detalles adicionales del mapa (anotados 2026-05-14)

### Botón "Navegar" con fondo rojo
- Actualmente el botón "Navegar" tiene fondo rojo — confunde con "error" o "eliminar"
- Cambiar a color neutro o azul de navegación

### Pin/alfiler del pedido
- El puntito/alfiler que marca la ubicación necesita un borde blanco para que se distinga mejor
- Agregar `border: 2px solid white` o similar al elemento del pin

### Nombres de pedidos/clientes en el mapa
- Cuando el pedido está "en camino", el nombre del cliente se ve en negro oscuro con letras blancas
- No se lee bien — mejorar contraste
- No hace falta que sean grandes, pero que se noten claramente
- Sugerencia: fondo semitransparente oscuro con texto blanco bien contrastado, o usar `text-shadow`

### Botones ⋮ en mobile — área táctil
- En TODAS las secciones (excepto mapa), hacer botones ⋮ donde haya 3+ acciones
- El botón ⋮ debe ser cómodo de apretar en mobile: padding lateral generoso, min 44px
- No que sobresalga visualmente, pero sí fácil de tocar con el dedo

## Prioridad general: MEDIA
## Orden sugerido: primero botones mapa → luego pines → luego uniformar resto
