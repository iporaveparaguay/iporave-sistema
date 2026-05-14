# Tarea — Fixes UX mobile (anotados 2026-05-14)

## IMPORTANTE: Solo aplica en CELULAR. En web se ve bien.

---

## 1. Pedidos — botones y nombres

- Botón ⋮ tiene que estar bien a la DERECHA, no en el medio
- Dejar espacio entre el nombre del cliente y el botón para que no se tapen
- Los nombres no deben quedar tan juntos/apretados
- **Datos ficticios**: llenar TODOS los campos de los pedidos de prueba (teléfono, dirección, todo) para que se vea como queda con datos reales

---

## 2. Campanita (codexNotifBell) — comportamiento en scroll

- Moverla más a la derecha, fija en esquina
- Hacerla un poquito más chica en mobile (no mucho)
- **Efecto transparencia en scroll hacia abajo**: opacity baja (~0.3) mientras el usuario scrollea hacia abajo → cuando vuelve hacia arriba vuelve a opacity 1 (sólida)
- Tiene que seguir siendo visible (no desaparecer del todo) para que salte la notif

---

## 3. Topbar en mobile — sección Pedidos (aplica a TODAS las secciones)

Situación actual: título de sección y botón ☰ (desplegar menú) están juntos en el medio y se pisan.

Fix propuesto:
- **Título de sección** (ej: "PEDIDOS" — probarlo en mayúsculas) → arriba
- **Botón ☰ de desplegar menú** → abajo, a la IZQUIERDA, contra la línea de separación que divide el área de botones de acción de lo que viene abajo
- El botón ☰ tiene que tener una pequeña separación del borde izquierdo (no pegado, pero cerca)
- Los botones de acción (Nuevo pedido, Exportar CSV, Exportar PDF, etc.) → espaciarlos mejor a lo largo del ancho, no todos apilados juntos
- Dejar espacio suficiente para poder tocarlos cómodamente

---

## 4. Balance — padding izquierdo

- La fecha y los datos están muy pegados a la línea amarilla del recuadro, a la izquierda
- Mover toda la información un poco hacia la derecha con padding/margin
- La medida de separación tiene que ser igual a la que usa la sección Liquidación (ya tiene buena separación)

---

## 5. Usuarios — padding izquierdo

- El nombre de usuario está pegado contra la línea amarilla del borde izquierdo del recuadro
- Aplicar la misma separación que tiene Liquidación (esa sección se ve bien)
- Regla general: TODA la info dentro de un recuadro amarillo debe tener la misma separación del borde que Liquidación

---

## 6. Zona y Entrega — botones y nombres

- Los botones grandes hay que quitarlos → reemplazar por ⋮ con dropdown
- Botón ⋮ bien a la izquierda con separación del borde (igual que en pedidos/usuarios)
- Nombres de lugares (Central, etc.) → misma separación de la línea amarilla que Liquidación

---

## 7. Catálogo — botones superiores

- Actualmente los botones superiores están en vertical → se ve horrible en mobile
- Aplicar el mismo patrón de TODAS las secciones:
  - Título de sección arriba
  - Botón ☰ abajo a la izquierda contra el separador
  - Botones de acción espaciados horizontalmente
- El nombre de lo que se está viendo debe tener espacio para mostrarse bien

---

## 8. Mapa — botones superiores

- Los botones de arriba están desorganizados
- El usuario quiere revisar esto junto con las secciones "de mapas para abajo" en una sesión aparte

---

## Regla general para TODOS los recuadros con borde amarillo

La separación interna (padding-left) debe ser igual a la que tiene la sección **Liquidación**.
Si se tiene duda de cuánto es: medir visualmente en Liquidación y aplicar esa medida a:
- Balance
- Usuarios
- Zona y Entrega
- Catálogo
- Cualquier otra sección con recuadro amarillo

---

## Prioridad: ALTA — antes del lanzamiento (2026-05-15)
## Solo mobile — no tocar la versión web
