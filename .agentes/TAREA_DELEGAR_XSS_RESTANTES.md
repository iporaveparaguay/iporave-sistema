# Tarea para delegar: XSS restantes en frontend (no críticos)

## Contexto
Hoy se aplicaron 7 fixes XSS críticos en `public/index.html` (chat, renderTable, dlvCard, track-public, catálogo público, autocomplete, chat send). Quedan estos pendientes — son **menos urgentes** porque están en superficies con menos exposición.

## Lista de XSS pendientes

### MEDIUM — Reseñas con fotos URL injection
- **Archivo:** `public/index.html` líneas 7917-7922
- **Problema:** `c.fotos` se inyecta como `<img src="..." onclick="window.open('...')">`. Si la URL contiene una comilla simple, rompe el atributo del onclick. Si es `javascript:void()`, ejecuta JS.
- **Fix:** validar prefijo `https://` antes de insertar; escapar comilla simple.

### MEDIUM — Imágenes de perfil
- **Archivo:** `public/index.html` líneas 2447, 7831, 7844, 7855, 7867
- **Problema:** `<img src="'+url+'" ...>` donde `url` viene de Supabase Storage. Si la URL no es http(s), o tiene comillas, hay XSS.
- **Fix:** agregar helper `safeUrl(u)` y usarlo:
  ```js
  function safeUrl(u){return /^https?:\/\//i.test(u||'')?u:'';}
  ```
  Reemplazar cada `'<img src="'+url+'">` por `'<img src="'+safeUrl(url)+'">`.

### MEDIUM — showAlert y pushNotif
- **Archivo:** `public/index.html` líneas 803, 814
- **Problema:** inyectan `msg` como HTML. Muchos call sites pasan `error.message` de Supabase que puede contener `<>`.
- **Fix:** cambiar `el.innerHTML = msg` por `el.textContent = msg` en estas dos funciones.

### MEDIUM — Scanner catálogo
- **Archivo:** `public/index.html` línea 6524
- **Problema:** el código que viene del scanner QR/barcode se inyecta en `onclick="...PAGES.catalogo('+codigo+')"`. Una comilla simple en `codigo` rompe el atributo.
- **Fix:** `escHtml(codigo)` + escapar comilla simple en el onclick (reemplazar por `&#39;`).

### LOW — w.document.write en páginas de impresión
- **Archivo:** `public/index.html` líneas 5018, 5345, 7491, 8045, 8129
- **Problema:** páginas de impresión (guía, boleta, ticket, PDF liquidación) inyectan datos del pedido sin escape. La ventana de impresión tiene acceso a `window.opener` → puede manipular la app principal vía XSS.
- **Fix:** agregar `<base target="_blank">` en la ventana de impresión + escapar datos con `escHtml()` antes de inyectar.

## Pattern para fix rápido
```js
// MAL
el.innerHTML = '<div>' + dato + '</div>';
// BIEN
el.innerHTML = '<div>' + escHtml(dato||'') + '</div>';
// MEJOR si no necesita HTML
el.textContent = dato;
```

`escHtml` ya existe en `public/index.html` línea ~7657. Solo hay que aplicarlo.

## Validación
- `node validate.js` antes de cada commit
- Smoke test: cargar la página afectada en navegador, probar con datos normales (no romper UX)

## Quién la puede hacer
- Codex / Aider / Antigravity — trabajo de buscar/reemplazar con un patrón claro
- Bajo riesgo, no toca lógica de negocio ni auth

## Por qué NO son críticos como los de hoy
- Los 7 que fixeé hoy permitían XSS en superficies de alto tráfico (chat tiempo real, tabla principal de pedidos, tracking público sin auth).
- Estos son en superficies de menor exposición: reseñas, impresión, scanner.
- Igual conviene cerrarlos antes de exponer la tienda pública.
