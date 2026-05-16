# BUGS UI MOBILE — Reportados por el usuario 2026-05-16
**Fuente:** Revisión manual del usuario en celular — feedback en conversación
**IMPORTANTE:** NO tocar hasta tener capturas de pantalla confirmadas

---

## 🔴 PRIORIDAD 1 — DELIVERY (está en la calle, necesita botones grandes y claros)

### DEL-1 | Kebab vertical (⋮) abre hacia la izquierda — DEBE abrir hacia la DERECHA
- **Afecta:** Todas las páginas del delivery donde aparece el ⋮ kebab
- **Problema:** El dropdown del menú kebab se despliega hacia la izquierda del ícono cuando debería abrirse hacia la derecha (o hacia el centro)
- **Fix CSS:** En el dropdown, cambiar `right:0` → `left:0` o usar `transform: translateX(...)` para centrar
- **Aplica a:** kebab en topbar delivery, kebab en mapa delivery

### DEL-2 | Botón "Actualizar" demasiado grande y mal ubicado — delivery principal
- **Problema:** Hay un botón grande "Actualizar" que molesta en el medio de la pantalla
- **Fix opciones:**
  a) Convertirlo en ícono de ruedita 🔄 más pequeño
  b) Moverlo al lado de las 3 rayitas del menú (topbar)
  c) Al lado del ⋮ kebab izquierdo del menú hamburguesa

### DEL-3 | Falta botón WhatsApp en tarjetas de "Mis Entregas"
- **Actualmente:** Llamar | Mapa | Cambiar Estado
- **Debe ser:** Llamar | WhatsApp | Mapa | Cambiar Estado
- **Estilo acordado:**
  - "Llamar" → transparente (estilo ghost, como el botón "Actualizar")
  - "WhatsApp" → verde fuerte (es el más importante)
  - "Mapa" → puede ir más chico o en posición secundaria
  - "Cambiar Estado" → mantener
- **Alternativa si no entra horizontal:** Sacar los botones FUERA de la tarjeta, ponerlos DEBAJO de ella (no dentro) para que no pierdan tamaño

### DEL-4 | Mapa delivery — filtros de estado innecesarios para delivery
- **Problema:** Le aparecen todos los filtros: Pendiente | Despachado | En Ruta | Entregado
- **El delivery solo necesita ver:** Todos | Despachados (nada más)
- **Fix:** En el filtro de estado, cuando `CU.rol === 'delivery'` mostrar solo esas 2 opciones

### DEL-5 | Mapa delivery — contador de tiempo activo mal ubicado
- **Problema:** El contador "tiempo en línea" aparece en un lugar que ocupa espacio del mapa
- **Fix:** Moverlo arriba en el topbar, chico, junto a "Mis pedidos / Mapa"
- **Debe aparecer SOLO cuando el delivery inició turno** (ya se muestra, pero reubicarlo)

### DEL-6 | Mapa delivery — botones Ruta Óptima + Finalizar Turno desorganizados
- **Problema:** Están desorganizados arriba y no dejan que el mapa suba completo
- **Fix sugerido:**
  - Ruta Óptima → en topbar, más pequeño
  - Finalizar Turno → botón rojo, pegado al borde
  - Dejar que el mapa ocupe el mayor espacio posible

### DEL-7 | Mapa delivery — selector de zona "Paraguay" gigante
- **Problema:** El botón selector de zona es muy grande y ocupa espacio innecesario
- **Fix:** Hacerlo más fino y pequeño, pegado a la línea superior del mapa, que al desplegarse se abra hacia el centro de la pantalla

### DEL-8 | Mapa delivery — filtros de estado ocupan espacio sin sentido
- **Ver DEL-4** — solo necesita "Todos" o "Despachados"
- Quitando esos filtros innecesarios, el mapa gana altura

### DEL-9 | Mapa delivery — pines se superponen SOBRE el menú (bug z-index)
- **Problema:** Cuando se abre cualquier menú/dropdown en el mapa, los pines del mapa (Mapbox) se renderizan encima del menú
- **Fix:** Aumentar z-index del menú/dropdown a mayor que el z-index del canvas de Mapbox
- **EXCEPCIÓN:** El chat IA flotante SÍ puede ir encima de todo — eso está bien

### DEL-10 | Delivery — catálogo tiene botón "Escanear" que no corresponde
- **Problema:** El delivery ve el botón de escanear en el módulo de catálogo
- **Lógica correcta:** El delivery PUEDE VER el catálogo (para consultar precios si alguien le pregunta), pero NO debe poder ESCANEAR ni agregar productos
- **Fix:** Ocultar botón "Escanear" cuando `CU.rol === 'delivery'`

---

## 🟠 PRIORIDAD 2 — GLOBAL (todos los roles)

### GLOB-1 | Kebab ⋮ en topbar — posición y comportamiento
- **Problema:** Los tres puntitos verticales (⋮) están posicionados a la izquierda en algunas páginas
- **Fix:** Moverlos más a la derecha, contra el borde
- **Cuando se abren:** deben abrirse hacia la DERECHA (no hacia la izquierda)
- Las 3 rayitas del menú hamburguesa: están bien, solo achicarlas un poco
- **Sugerencia layout topbar ideal:**
  ```
  [☰ menú] [nombre página]        [🔔 campana] [⋮ kebab]
  ```

### GLOB-2 | Buscador de pedidos aparece abajo del todo
- **Problema:** El buscador de pedidos aparece al pie de la pantalla, donde no tiene sentido
- **Fix:** Quitar de abajo. Reemplazar por ícono de lupa 🔍 en la sección de pedidos (en topbar o filtros)
- El usuario entiende que 🔍 = buscar pedidos sin que haga falta texto grande

### GLOB-3 | Tutorial muy grande en mobile
- **Problema:** El tooltip/panel del tutorial ocupa demasiado espacio en mobile
- **Fix:** Achicar tamaño en mobile, usar texto más corto
- Además: al estar el tutorial abajo, tapa los botones de la topbar que están arriba del scroll

### GLOB-4 | Mapa — pines tipo alfiler (alfiler rojito tipo Google Maps)
- **Pedido por el usuario:**
  - Cambiar pins actuales a forma de alfiler (teardrop / drop pin) tipo Google Maps
  - **Para delivery:** Pin rojito con la flechita (ya lo tiene, pero mejorarlo)
  - El nombre del cliente arriba del pin, visible sin zoom
  - **Para los demás usuarios:** Pueden tener formas/colores diferentes
- **Motivo:** Con el pin actual hay que hacer mucho zoom para ver el punto exacto. El alfiler tiene la punta = ubicación exacta

### GLOB-5 | Mapa admin/vendedor — botones más chicos que delivery
- **Para admin, superadmin, vendedor, proveedor:** los botones del mapa pueden ser más pequeños y organizados
- **Razón:** Ellos mayormente usan PC. En el celular es para controlar, no para trabajar en la calle
- **Delivery sí necesita botones grandes** — él trabaja en la moto

---

## 🤖 ASISTENTE IA — Problemas específicos

### IA-1 | Asistente "piensa en voz alta" — no sirve para delivery
- **Problema:** El asistente escribe su razonamiento antes de la respuesta (chain-of-thought visible)
- **Fix en worker `/api/asistente-agentic`:** El modelo debe responder solo la respuesta final, sin razonamiento previo
- **Para delivery especialmente:** Solo la respuesta concisa, sin explicaciones largas

### IA-2 | Falta respuesta por AUDIO para delivery
- **Pedido:** El delivery puede mandar un audio → el asistente responde en audio (TTS)
- **Flujo ideal:**
  1. Delivery aprieta botón de micrófono → graba → manda
  2. STT convierte a texto → va al asistente
  3. Respuesta → TTS → se reproduce automáticamente
- **Groq tiene Whisper (STT)** — ya está en el sistema para otra cosa
- **TTS:** Puede ser ElevenLabs, OpenAI TTS, o Groq TTS
- **Estado:** No implementado — feature futura pero urgente para delivery

### IA-3 | Audio del asistente se corta al mover el celular
- **Problema:** El audio del asistente se interrumpe si el usuario mueve el teléfono o hace algo
- **Causa probable:** `AudioContext` o `Web Speech API` que se pausa en mobile cuando el evento `blur`/`visibilitychange` ocurre
- **Fix:** Manejar los eventos de interrupción y reanudar el audio

### IA-4 | Asistente repite información redundante
- **Problema:** La respuesta repite ideas o usa demasiadas palabras
- **Fix en el prompt del worker:** Instruir al modelo a ser CONCISO — máximo 2-3 oraciones para respuestas de delivery

---

## 📋 RESUMEN DE QUÉ DELEGAR Y A QUIÉN

| Tarea | Complejidad | Delegar a |
|-------|-------------|-----------|
| Kebab dropdown direction | CSS simple | Antigravity |
| Botón actualizar → ícono chico | HTML/CSS | Antigravity |
| Botón WhatsApp en delivery | HTML + JS | Antigravity |
| Filtros delivery solo "Despachados" | JS condición | Claude |
| Contador tiempo reubicado | HTML/CSS | Antigravity |
| Selector zona más fino | CSS | Antigravity |
| Pines alfiler (teardrop) | SVG + Mapbox | Claude |
| Z-index pines vs menú | CSS z-index | Antigravity |
| Ocultar scanner para delivery | JS condición | Claude |
| Buscador a lupa | HTML/CSS/JS | Antigravity |
| Tutorial más chico mobile | CSS | Antigravity |
| Asistente sin chain-of-thought | Prompt worker | Claude |
| STT → TTS delivery | Worker + JS | Claude (largo plazo) |
| Audio no se corta | JS AudioContext | Claude |

---

## ⚠️ REGLAS PARA QUIEN HAGA LOS CAMBIOS

1. **NO cambiar el diseño general** — solo reorganizar y achicar lo que sobra
2. **Delivery siempre prioridad** — sus botones TIENEN que quedar grandes y claros
3. **Mapa ocupa el mayor espacio posible** — todo lo que no sea mapa debe ser compacto
4. **El chat IA flotante puede ir encima de todo** — tiene el z-index más alto
5. **Capturas del usuario** son la referencia final — esperar antes de hacer cambios
6. **Antigravity** hace CSS/HTML. **Claude** hace lógica JS/worker

---

**Fecha:** 2026-05-16  
**Estado:** PENDIENTE — esperar capturas del usuario antes de implementar
