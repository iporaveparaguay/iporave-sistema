# 📋 TAREA PARTE 1 — ANTIGRAVITY
# Director: Claude Code | Aprobación requerida antes de Parte 2

---

## TU ROL EN ESTA PARTE
Crear el **catálogo público** — visible sin login, en un archivo completamente separado.

---

## QUÉ TENÉS QUE HACER

### Nuevo archivo: `public/catalog.html`

Página pública independiente. NO tocar `index.html` bajo ningún concepto.

### Funcionalidad requerida

1. **Grid de productos** del catálogo
   - Solo productos con `publicar_tienda = true`
   - Mostrar: foto, nombre, precio, descripcion
   - Si no hay foto → mostrar placeholder con ícono 📦

2. **Barra de búsqueda** simple por nombre

3. **Botón "Hacer pedido"** en cada producto
   - Al hacer clic → abre modal con formulario básico:
     - Nombre del comprador (texto)
     - WhatsApp (número)
     - Dirección de entrega (texto)
     - Cantidad (número, mínimo 1)
   - Al enviar → abre WhatsApp con mensaje pre-armado al número de la empresa

4. **Header** con logo de Iporãve y nombre "Iporãve Connect"

5. **Sin auth** — completamente público, sin Supabase Auth

### Fuente de datos
Los productos se obtienen del Worker público:
```javascript
fetch('https://iporave-api.iporaveparaguay.workers.dev/api/catalog-public')
```
Si ese endpoint no existe todavía → cargar desde Supabase directamente (anon key):
- URL Supabase: obtenerla del Worker con `fetch('/api/config')` NO — usar la clave pública
- Supabase URL: `https://hrpnqbmknmgdaaokjelb.supabase.co`
- Anon key: obtenerla con `fetch('https://iporave-api.iporaveparaguay.workers.dev/api/config')`
  y usar `data.supabase_anon_key`

### Diseño
- Fondo oscuro, estilo similar a index.html (dark mode)
- Mobile-first — tiene que verse bien en celular
- Sin frameworks externos — vanilla JS/CSS
- Paleta: usar las mismas variables CSS que index.html si las importás, o definir tu propio dark theme

---

## ARCHIVOS ASIGNADOS

| Archivo | Acción |
|---|---|
| `public/catalog.html` | Crear nuevo — toda la lógica acá |
| `public/catalog.css` | Opcional — si querés separar estilos |

---

## ❌ PROHIBIDO — NO TOCAR

- `public/index.html` — bajo ningún concepto
- `public/sw.js` — el service worker existente
- Archivos del worker (`iporave-worker/`)
- No crear endpoints nuevos en el worker — usar lo que ya existe

---

## CÓMO REPORTAR cuando terminás

```bash
curl -X POST http://localhost:1880/reporte \
  -H "Content-Type: application/json" \
  -d "{\"agente\":\"Antigravity\",\"tarea\":\"PARTE1_catalogo_publico\",\"archivos\":\"public/catalog.html\",\"resumen\":\"Catálogo público sin login con grid productos, búsqueda y formulario de pedido por WhatsApp\",\"estado\":\"Finalizado\"}"
```

Después esperá confirmación VALIDADO. No avances hasta que Claude Code apruebe la Parte 1 completa.
