# Tarea UI — Login mobile: campanita + bandera + título

## Issues a corregir

### 1. Campanita aparece en la pantalla de login (bug)
- La campana de notificaciones aparece arriba a la derecha **antes de loguear**
- No debería aparecer hasta que el usuario esté autenticado
- Fix: ocultar el botón/ícono de campana cuando no hay sesión activa (cuando `CU` es null o cuando la página es 'login')
- Buscar en `updateNavBadges()` o en el render del topbar — agregar condición `if(!CU) return` antes de mostrar la campana

### 2. Bandera de Paraguay en celular — posición y separación
- La bandera 🇵🇾 solo aparece en mobile
- Hay que posicionarla pegada (con separación) a la **"y" de "Iporãve"** (o "py" del nombre)
- Separación requerida: **0.5 cm a 1 cm de margen**, igual a ambos lados (ni pegada ni suelta)
- Verificar en media query mobile (max-width: 768px) — el CSS del topbar o del logo

### 3. Título más grande en mobile
- El título "Iporãve" o nombre del sistema hay que agrandarlo más en pantalla mobile
- Probablemente ajustar `font-size` en el media query correspondiente

## Archivos a tocar
- `public/index.html` — topbar, CSS de login, media queries mobile
- Buscar con grep: `campana`, `#bellBtn`, `#notifBtn`, `🇵🇾`, `bandera`

## Prioridad
MEDIA — es visual, no rompe nada. Hacer en sprint UI después de cerrar seguridad.
