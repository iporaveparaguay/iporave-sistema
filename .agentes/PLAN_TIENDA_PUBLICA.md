# PLAN ARQUITECTÓNICO — Tienda Pública con Carrito (Iporãve)

**Fecha:** 2026-05-16
**Autor:** Claude (agente supervisor)
**Estado:** Plan — NO IMPLEMENTADO
**Dominio público:** iporaveparaguay.com
**Dominio Shopify interno:** iporaveparaguay.myshopify.com

---

## 0. Resumen ejecutivo

Construir una tienda pública full e-commerce sobre la base actual de `catalog.html` (catálogo público) y `track.html` (tracking público). El objetivo es permitir compras sin login, con carrito persistente, checkout multi-paso, geocoding de zona de envío, integración WhatsApp para confirmación, y auto-registro opcional post-compra. Toda la lógica vive en el worker Cloudflare actual + Supabase como DB.

Principios:
- **Mobile-first** (90% del tráfico esperado es WhatsApp → móvil).
- **Login opcional**: el flujo NUNCA exige cuenta; el registro es upsell post-compra.
- **WhatsApp como confirmación**: el "Pay button" del MVP es enviar un mensaje pre-llenado al vendedor.
- **Reutilizar lo existente**: pedidos siguen pasando por el mismo pipeline interno (Pedidos → Vendedor → Repartidor).

---

## 1. URLs y estructura

### Esquema canónico

| URL | Propósito | Auth |
|---|---|---|
| `iporaveparaguay.com/` | Landing + catálogo destacado | Público |
| `iporaveparaguay.com/tienda` | Catálogo completo con filtros | Público |
| `iporaveparaguay.com/v/{slug-vendedor}` | Sub-tienda de un vendedor (dropshipper) | Público |
| `iporaveparaguay.com/p/{slug-producto}` | Ficha de producto individual (SEO) | Público |
| `iporaveparaguay.com/c/{slug-categoria}` | Listado por categoría | Público |
| `iporaveparaguay.com/buscar?q=...` | Resultados de búsqueda | Público |
| `iporaveparaguay.com/carrito` | Vista de carrito (paso 1 checkout) | Público |
| `iporaveparaguay.com/checkout` | Flujo de checkout (pasos 2–5) | Público |
| `iporaveparaguay.com/seguimiento/{order}` | Tracking público (ya existe) | Público |
| `iporaveparaguay.com/cuenta` | Mi cuenta (pedidos, direcciones, wishlist) | Cliente registrado |
| `iporaveparaguay.com/cuenta/login` | Login cliente (magic link + password opcional) | Público |
| `iporaveparaguay.com/legal/terminos` | Términos y condiciones | Público |
| `iporaveparaguay.com/legal/privacidad` | Política de privacidad | Público |
| `iporaveparaguay.com/legal/devoluciones` | Política de devoluciones | Público |

### Slugs
- **Producto**: `{nombre-kebab}-{id-corto}` ej. `crystal-gloss-hybrid-pro-a3f2`.
- **Vendedor**: `{nombre-kebab}` ej. `isidro`, `iporave-oficial`.
- **Categoría**: `{nombre-kebab}` ej. `pulido-vehicular`.

### Estructura de archivos (frontend)
```
/public
  index.html                  # landing
  tienda.html                 # catálogo (evolución de catalog.html)
  producto.html               # ficha producto (un solo archivo, ruteo por query/path)
  carrito.html                # carrito
  checkout.html               # flujo multi-paso
  cuenta.html                 # mi cuenta cliente público
  /assets
    /css/tienda.css
    /js/tienda.js
    /js/carrito.js
    /js/checkout.js
```

Routing: server-side por worker (regex match en URL) → sirve el HTML correspondiente con datos hidratados en `<script type="application/json" id="ssr-data">`.

---

## 2. Catálogo público mejorado

Base: `catalog.html` actual. Evoluciona a `tienda.html`.

### Filtros (sidebar izquierdo desktop / drawer móvil)
- **Categoría** (checkboxes multi-select).
- **Precio** (slider min/max con histograma de distribución).
- **Rating** (estrellas mínimo: 1, 2, 3, 4).
- **Stock** (toggle "Solo disponibles").
- **Vendedor** (multi-select).
- **Etiquetas** (chips: "Oferta", "Nuevo", "Más vendido").

### Búsqueda
- **Autocompletado** debounce 200ms.
- Top 5 productos + top 3 categorías sugeridas.
- Tracking de búsquedas fallidas (tabla `busquedas_sin_resultado`) para SEO/inventario.

### Sort
- Relevancia (default — score IA + ventas + rating).
- Precio asc / desc.
- Novedades (created_at desc).
- Mejor valorado (rating desc + cantidad reviews).
- Más vendidos (cantidad pedidos último mes).

### Vista
- Toggle **Grid** (default móvil) / **Lista** (default desktop).
- Grid: 2 col móvil, 3 col tablet, 4 col desktop, 5 col XL.

### Paginación
- **Infinite scroll** con IntersectionObserver, batch 24 productos.
- Botón "Cargar más" como fallback accesible.
- URL sincronizada con query `?p=2` para compartir.

### Productos relacionados
- En ficha producto: 6 sugerencias ("También te puede interesar").
- Algoritmo: misma categoría + rango precio ±30% + ordenado por co-ocurrencia en pedidos.

### Recomendaciones IA (Vertex AI)
- Endpoint `/api/tienda/recomendar` recibe historial de vistas + carrito actual.
- Modelo: text embeddings de descripciones → similaridad coseno.
- Fallback si Vertex falla: trending de la semana.

### Wishlist
- Icono corazón en cada card.
- Anónimo: localStorage `wishlist_anon`.
- Registrado: tabla `wishlists` (user_id, producto_id).
- Sync al hacer login: merge anon + DB.

---

## 3. Carrito persistente

### Storage
| Estado | Storage | TTL |
|---|---|---|
| No registrado | localStorage `carrito_iporave_v1` | 30 días |
| Registrado | Tabla `carritos` + localStorage como cache | 90 días |

### Sync rules
- Login: merge local + DB → última cantidad gana, mantener todos los items.
- Logout: vaciar localStorage.
- Cambio de dispositivo (registrado): pull DB al cargar.

### Estructura del item
```json
{
  "producto_id": "uuid",
  "variante_id": "uuid|null",
  "cantidad": 2,
  "precio_unit": 75000,
  "precio_unit_oferta": 65000,
  "vendedor_id": "uuid",
  "agregado_at": "2026-05-16T..."
}
```

### UI
- Mini-cart drawer al agregar (Rappi-style, slide right).
- Página `/carrito` con tabla editable.
- Sumatoria sticky abajo en móvil: subtotal + envío estimado + total.
- Botones: "Vaciar", "Seguir comprando", "Ir al checkout".
- Edición cantidad: stepper +/− inline.
- Quita item: swipe-to-delete móvil + botón × desktop.
- Aplicar cupón: input con validación en vivo.

### Validaciones al checkout
- Re-confirmar stock contra DB (puede haber cambiado).
- Re-confirmar precio (alertar si cambió, no auto-actualizar).
- Mostrar items sin stock con CTA "Quitar" / "Avisarme cuando llegue".

---

## 4. Checkout flow (5 pasos)

Componente único `checkout.html` con state machine. Stepper visible arriba.

### Paso 1 — Carrito
- Revisión final, edición cantidades.
- Aplicación de cupón.
- CTA: "Continuar".

### Paso 2 — Datos del cliente
- Si logueado: prellenado, opción "Editar".
- Si no logueado: formulario simple.
  - Nombre completo (required).
  - Teléfono WhatsApp (required, validación +595).
  - Email (opcional pero recomendado para tracking).
- Checkbox "Acepto términos y privacidad".
- CTA: "Continuar".

### Paso 3 — Dirección de envío
- Geocoding Mapbox: input "dirección" con autocompletado restringido a Paraguay.
- Mapa interactivo: pin arrastrable para ajustar.
- Detección automática de zona → cálculo costo envío.
- Campos:
  - Dirección (geocoded).
  - Referencia/landmark (texto libre).
  - Tipo lugar (casa / depto / oficina).
  - Instrucciones repartidor (opcional).
- Si la zona no tiene cobertura: alerta + sugerir "retiro en tienda" o "consultar por WhatsApp".
- CTA: "Continuar".

### Paso 4 — Método de pago
Opciones MVP:
- **Contra entrega** (efectivo o POS si vendedor tiene).
- **Transferencia bancaria** (mostrar datos cuenta).
- **Tigo Money / Personal Pay** (mostrar número, monto, referencia).
- *(Fase 3: Stripe / Bancard online).*

UI: cards seleccionables con icono + descripción + tiempo estimado de confirmación.

CTA: "Revisar pedido".

### Paso 5 — Confirmación
- Resumen completo: items, dirección, método pago, totales.
- Total final destacado.
- Tiempo estimado de entrega (zona + horario).
- Checkbox "Quiero recibir actualizaciones por WhatsApp".
- CTA: **"Confirmar pedido"** (botón verde grande).

**Al confirmar:**
1. POST `/api/tienda/checkout` → crea pedido en DB.
2. Worker envía notificación WhatsApp al vendedor (asignación según zona o vendedor del producto).
3. Worker envía mensaje WhatsApp al cliente con link de tracking.
4. Si cliente puso email: envío de email confirmación.
5. Redirect a `/seguimiento/{order}` con animación de éxito.
6. Modal post-checkout: "¿Querés crear una cuenta para ver tu historial?" (ver §5).

---

## 5. Auto-registro opcional

Filosofía: NUNCA bloquear la compra detrás de un registro.

### Trigger
- Tras éxito en checkout (paso 5).
- Tras consultar tracking 2+ veces del mismo pedido.

### Modal "¿Crear cuenta?"
- Texto: "Tu pedido ya está en camino. ¿Querés crear una cuenta para seguir todos tus pedidos y comprar más rápido la próxima vez?"
- 2 botones:
  - **"Sí, crear cuenta"** → genera magic link al email proporcionado.
  - **"No, gracias"** → cierra modal. Igual recibe link de tracking por WhatsApp.

### Flujo magic link
1. Worker genera token UUID + expiración 24h, guarda en `magic_links`.
2. Email con link `iporaveparaguay.com/cuenta/activar?token=...`.
3. Cliente hace click → worker valida token → crea registro en `clientes_publicos` → setea cookie session → redirect `/cuenta`.
4. En `/cuenta`: pedido recién hecho ya está vinculado por teléfono.

### Vinculación retroactiva
- Al crear cuenta, buscar todos los pedidos previos con mismo teléfono/email → vincular.

---

## 6. Schema de DB (Supabase)

```sql
-- 6.1 Carritos persistentes
CREATE TABLE carritos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES clientes_publicos(id) ON DELETE CASCADE,
  session_id text, -- para anónimos (cookie)
  items_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  cupon_codigo text,
  subtotal numeric(12,2),
  descuento numeric(12,2) DEFAULT 0,
  envio_estimado numeric(12,2),
  total numeric(12,2),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  expires_at timestamptz DEFAULT (now() + interval '90 days'),
  CHECK (user_id IS NOT NULL OR session_id IS NOT NULL)
);
CREATE INDEX idx_carritos_user ON carritos(user_id);
CREATE INDEX idx_carritos_session ON carritos(session_id);
CREATE INDEX idx_carritos_expires ON carritos(expires_at);

-- 6.2 Cupones
CREATE TABLE cupones (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  codigo text UNIQUE NOT NULL,
  descripcion text,
  descuento_pct numeric(5,2), -- 0-100
  descuento_fijo numeric(12,2),
  monto_minimo numeric(12,2) DEFAULT 0,
  fecha_inicio timestamptz NOT NULL,
  fecha_fin timestamptz NOT NULL,
  usos_max integer, -- null = ilimitado
  usos_actuales integer DEFAULT 0,
  por_usuario_max integer DEFAULT 1,
  activo boolean DEFAULT true,
  aplica_a text DEFAULT 'todo', -- 'todo' | 'categoria' | 'producto' | 'vendedor'
  aplica_ids uuid[],
  created_at timestamptz DEFAULT now(),
  created_by uuid,
  CHECK (descuento_pct IS NOT NULL OR descuento_fijo IS NOT NULL)
);
CREATE INDEX idx_cupones_codigo ON cupones(codigo) WHERE activo = true;

-- 6.3 Uso de cupones
CREATE TABLE cupones_usos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cupon_id uuid REFERENCES cupones(id),
  cliente_id uuid REFERENCES clientes_publicos(id),
  pedido_id uuid REFERENCES pedidos(id),
  descuento_aplicado numeric(12,2),
  usado_at timestamptz DEFAULT now()
);

-- 6.4 Clientes públicos (no son usuarios del sistema interno)
CREATE TABLE clientes_publicos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre text NOT NULL,
  telefono text NOT NULL,
  email text,
  direccion_principal jsonb, -- {calle, ref, lat, lng, zona}
  direcciones jsonb DEFAULT '[]'::jsonb, -- array de direcciones guardadas
  password_hash text, -- opcional, si quiere login con contraseña
  email_verificado boolean DEFAULT false,
  telefono_verificado boolean DEFAULT false,
  preferencias jsonb DEFAULT '{}'::jsonb,
  meta jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  ultimo_login_at timestamptz,
  UNIQUE (telefono)
);
CREATE INDEX idx_clientes_publicos_email ON clientes_publicos(email);
CREATE INDEX idx_clientes_publicos_telefono ON clientes_publicos(telefono);

-- 6.5 Magic links (auth sin password)
CREATE TABLE magic_links (
  token text PRIMARY KEY,
  cliente_id uuid,
  email text NOT NULL,
  proposito text DEFAULT 'login', -- 'login' | 'activacion' | 'reset'
  usado boolean DEFAULT false,
  expira_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX idx_magic_links_email ON magic_links(email);

-- 6.6 Wishlists
CREATE TABLE wishlists (
  cliente_id uuid REFERENCES clientes_publicos(id) ON DELETE CASCADE,
  producto_id uuid REFERENCES productos(id) ON DELETE CASCADE,
  agregado_at timestamptz DEFAULT now(),
  PRIMARY KEY (cliente_id, producto_id)
);

-- 6.7 Analytics — vistas de producto
CREATE TABLE productos_views (
  id bigserial PRIMARY KEY,
  producto_id uuid NOT NULL,
  cliente_id uuid,
  session_id text,
  ip_hash text, -- hashed para no guardar IP cruda
  user_agent text,
  referrer text,
  utm_source text,
  utm_campaign text,
  duracion_seg integer,
  viewed_at timestamptz DEFAULT now()
);
CREATE INDEX idx_productos_views_producto ON productos_views(producto_id);
CREATE INDEX idx_productos_views_fecha ON productos_views(viewed_at);

-- 6.8 Carritos abandonados (vista materializada)
CREATE MATERIALIZED VIEW carritos_abandonados AS
SELECT c.*, cp.telefono, cp.email
FROM carritos c
LEFT JOIN clientes_publicos cp ON cp.id = c.user_id
WHERE c.updated_at < now() - interval '2 hours'
  AND c.updated_at > now() - interval '7 days'
  AND jsonb_array_length(c.items_json) > 0
  AND NOT EXISTS (
    SELECT 1 FROM pedidos p
    WHERE p.cliente_id = c.user_id
      AND p.created_at > c.updated_at
  );

-- 6.9 Sesiones (cookie-based para anónimos)
CREATE TABLE sesiones_publicas (
  id text PRIMARY KEY,
  cliente_id uuid,
  data jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  expires_at timestamptz DEFAULT (now() + interval '30 days')
);

-- 6.10 Búsquedas sin resultado (para SEO/inventario)
CREATE TABLE busquedas_sin_resultado (
  id bigserial PRIMARY KEY,
  query text NOT NULL,
  cantidad integer DEFAULT 1,
  ultima_vez timestamptz DEFAULT now()
);
CREATE UNIQUE INDEX idx_busquedas_query ON busquedas_sin_resultado(lower(query));
```

### RLS
- `carritos`: cliente solo ve los suyos; service role bypass.
- `clientes_publicos`: cliente solo ve su propia fila; admin ve todos.
- `wishlists`: idem.
- `productos_views`: solo escritura desde worker; lectura admin.

---

## 7. Endpoints del worker

Prefijo: `/api/tienda/...` y `/api/clientes/...`.

| Método | Path | Propósito | Auth |
|---|---|---|---|
| GET | `/api/tienda/productos` | Listado con filtros, sort, paginación | Público |
| GET | `/api/tienda/producto/:slug` | Detalle producto + relacionados | Público |
| GET | `/api/tienda/categorias` | Árbol de categorías con contadores | Público |
| GET | `/api/tienda/vendedor/:slug` | Sub-tienda de un vendedor | Público |
| GET | `/api/tienda/buscar?q=...` | Búsqueda con autocompletado | Público |
| POST | `/api/tienda/recomendar` | Recomendaciones IA Vertex | Público |
| GET | `/api/tienda/carrito` | Carrito actual (cookie/session) | Público |
| POST | `/api/tienda/carrito/agregar` | Agregar item | Público |
| PATCH | `/api/tienda/carrito/item/:id` | Editar cantidad | Público |
| DELETE | `/api/tienda/carrito/item/:id` | Quitar item | Público |
| DELETE | `/api/tienda/carrito` | Vaciar | Público |
| POST | `/api/tienda/carrito/cupon` | Aplicar/quitar cupón | Público |
| POST | `/api/tienda/cupon/validar` | Validar cupón sin aplicar | Público |
| POST | `/api/tienda/envio/calcular` | Calcular costo envío por zona | Público |
| POST | `/api/tienda/checkout` | Crear pedido | Público |
| GET | `/api/tienda/track/:order` | Tracking público pedido | Público |
| POST | `/api/clientes/registrar` | Auto-registro post-checkout | Público |
| POST | `/api/clientes/magic-link` | Solicitar magic link | Público |
| GET | `/api/clientes/magic-link/validar` | Validar token, crear sesión | Público |
| POST | `/api/clientes/logout` | Cerrar sesión | Cliente |
| GET | `/api/clientes/me` | Datos del cliente actual | Cliente |
| PATCH | `/api/clientes/me` | Actualizar perfil | Cliente |
| GET | `/api/clientes/me/pedidos` | Historial pedidos | Cliente |
| GET | `/api/clientes/me/wishlist` | Wishlist | Cliente |
| POST | `/api/clientes/me/wishlist/:productoId` | Toggle wishlist | Cliente |
| POST | `/api/tienda/analytics/view` | Registrar view producto (beacon) | Público |

### Rate limits
- Público: 60 req/min por IP.
- Búsqueda: 30 req/min por IP.
- Checkout: 5 req/min por IP (anti-fraude).
- Magic link: 3 req/hora por email.

### Idempotencia
- `/checkout` con header `Idempotency-Key` (UUID generado en frontend al iniciar paso 5).

---

## 8. SEO y meta tags

### Open Graph (cada ficha producto)
```html
<meta property="og:type" content="product">
<meta property="og:title" content="{producto.nombre} | Iporãve">
<meta property="og:description" content="{producto.descripcion_corta}">
<meta property="og:image" content="{producto.imagen_og_1200x630}">
<meta property="og:url" content="https://iporaveparaguay.com/p/{slug}">
<meta property="product:price:amount" content="{precio}">
<meta property="product:price:currency" content="PYG">
<meta property="product:availability" content="{in stock | out of stock}">
```

### Twitter Card
```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@iporaveparaguay">
<meta name="twitter:title" content="...">
<meta name="twitter:description" content="...">
<meta name="twitter:image" content="...">
```

### Schema.org Product (JSON-LD)
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "...",
  "image": ["..."],
  "description": "...",
  "sku": "...",
  "brand": {"@type": "Brand", "name": "..."},
  "offers": {
    "@type": "Offer",
    "url": "...",
    "priceCurrency": "PYG",
    "price": "...",
    "availability": "https://schema.org/InStock",
    "seller": {"@type": "Organization", "name": "Iporãve"}
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "...",
    "reviewCount": "..."
  }
}
</script>
```

### Sitemap.xml dinámico
- Worker route `GET /sitemap.xml` → genera al vuelo desde DB.
- Incluye: home, /tienda, todas las categorías, todos los productos activos, todas las sub-tiendas vendedores.
- Cache 1 hora.

### robots.txt
```
User-agent: *
Allow: /
Disallow: /carrito
Disallow: /checkout
Disallow: /cuenta
Disallow: /api/
Sitemap: https://iporaveparaguay.com/sitemap.xml
```

### Canonical
- Cada ficha producto: `<link rel="canonical" href="https://iporaveparaguay.com/p/{slug}">`
- Evitar duplicados por filtros: canonical apunta a URL sin query params en `/tienda`.

---

## 9. Performance

### Imágenes
- **Cloudflare Image Resizing**: `cdn-cgi/image/width=400,quality=80,format=auto/{url}`.
- 3 tamaños responsivos: 200w (thumb), 600w (card), 1200w (zoom).
- `<picture>` con AVIF + WebP + JPG fallback.
- Lazy load real con IntersectionObserver (no solo `loading="lazy"` que es laxo).
- Placeholder: blur hash o color dominante extraído al subir.

### Virtualización
- Grid con >100 productos: usar virtualización (solo renderizar visibles + buffer).
- Librería: `virtual-scroller` o implementación custom con IntersectionObserver.

### Service Worker
- Cache estratégico:
  - **App shell** (CSS, JS, fuentes): cache-first, versionado.
  - **Imágenes productos**: stale-while-revalidate, max 7 días.
  - **API productos**: network-first con fallback cache 5 min.
  - **API carrito/checkout**: network-only (nunca cachear).
- Offline page: mostrar wishlist + último carrito + mensaje "Sin conexión".

### Code splitting
- HTML por página (no SPA).
- JS por módulo: `tienda.js`, `carrito.js`, `checkout.js`, `cuenta.js` cargados solo donde se usan.
- CSS crítico inline (`<style>` en `<head>`), resto async con `media="print" onload="this.media='all'"`.

### Fuentes
- Self-host (Inter + Geist Sans).
- `font-display: swap`.
- Preload de variable font único.

### Métricas objetivo (Core Web Vitals)
- LCP < 2.0s en 4G móvil.
- CLS < 0.05.
- INP < 200ms.
- TBT < 200ms.

---

## 10. Analytics

### Eventos a trackear (propio + GA4)
- `page_view` (URL, referrer, utm)
- `view_item_list` (categoría, filtros aplicados)
- `view_item` (producto_id, precio)
- `select_item` (click en card)
- `add_to_cart` (producto, cantidad, valor)
- `remove_from_cart`
- `view_cart`
- `begin_checkout`
- `add_shipping_info`
- `add_payment_info`
- `purchase` (order_id, valor, items, cupon)
- `search` (query, resultados)
- `search_no_results` (query)
- `wishlist_add`
- `share` (red social, producto)

### Dashboard interno
- En el admin existente, agregar tab "Tienda Pública":
  - Visitas/día, semana, mes (gráfica).
  - Top 10 productos más vistos.
  - Top 10 más comprados.
  - Tasa de conversión (view_item → purchase).
  - Carritos abandonados (cantidad, valor total).
  - Funnel: catálogo → ficha → carrito → checkout paso 2 → 3 → 4 → 5 → confirmado.
  - Cupones más usados.
  - Búsquedas sin resultado top 20.

### Implementación
- Eventos client-side → `POST /api/tienda/analytics/event` (beacon API, no-block).
- Worker bufferea y escribe a tabla `analytics_eventos` cada 30s en batch.
- Vistas materializadas refrescadas cada 5 min para dashboard.

---

## 11. Integraciones futuras

### Meta Pixel (ya instalado: `1863034214304562`)
- Disparar eventos en mismos puntos que GA4.
- Eventos clave: `ViewContent`, `AddToCart`, `InitiateCheckout`, `Purchase`.
- Conversions API server-side desde worker (más fiable que client por ad blockers).

### Google Analytics 4
- gtag.js con `send_page_view: false` (control manual).
- Server-side via Measurement Protocol para purchase (doble redundancia).

### Microsoft Clarity
- Heatmaps + grabaciones sesión.
- Gratis ilimitado.
- Script en `<head>` con sample rate 50% (suficiente para detectar problemas UX).

### WhatsApp Business API
- Ya integrado para notificaciones outbound.
- Fase 2: webhook inbound para clientes que respondan al mensaje de confirmación (responder automáticamente con tracking).

### Mercado Pago / Bancard (Fase 3)
- Checkout Pro de MercadoPago (redirect).
- Bancard VPOS para tarjetas locales paraguayas.
- Webhook de confirmación → actualiza pedido a "pagado".

---

## 12. Modelos visuales / inspiración

| Referencia | Qué tomar |
|---|---|
| **Shopify Dawn theme** | Estructura limpia, accesibilidad, mobile-first |
| **Tiendanube** | UX latam, métodos de pago locales, formas de envío |
| **Mercado Libre — ficha producto** | Galería de imágenes, sticky CTA, info envío clara |
| **Amazon** | Cross-sell ("Frequently bought together"), reviews |
| **Rappi catalog** | Cards densas, filtros chips, mini-cart drawer |
| **Apple Store** | Tipografía, espacio en blanco, foco en producto |
| **Nuuly / Outdoor Voices** | Branding cálido, fotos lifestyle |

### Sistema visual
- Reutilizar tokens del admin actual.
- Paleta: verde Iporãve principal + acento dorado.
- Tipo: Geist Sans (cuerpo) + Geist Mono (precios/SKU).
- Border radius 12px (cards), 8px (inputs), 999px (chips).
- Sombras suaves multicapa (no flat ni glassmorph excesivo).

---

## 13. MVP vs futuro — Roadmap

### Fase 1 — MVP (2-3 semanas)
**Goal:** primer pedido público end-to-end.
- [ ] Estructura URL + routing en worker.
- [ ] `tienda.html` con catálogo + filtros básicos (categoría, precio, stock).
- [ ] Búsqueda simple (sin autocomplete).
- [ ] `producto.html` ficha + galería + CTA agregar al carrito.
- [ ] Carrito localStorage (sin sync DB).
- [ ] Checkout 5 pasos sin método pago online (solo contra entrega + transferencia).
- [ ] Confirmación WhatsApp → vendedor + cliente.
- [ ] `seguimiento/{order}` ya existe (track.html).
- [ ] SEO básico: meta tags, sitemap, Schema.org Product.
- [ ] Open Graph para compartir.
- [ ] Mobile-first responsive.

### Fase 2 — Cuentas y retención (2 semanas)
- [ ] Tablas `clientes_publicos`, `magic_links`, `carritos`, `wishlists`.
- [ ] Endpoints `/api/clientes/...`.
- [ ] Modal post-checkout "crear cuenta".
- [ ] `/cuenta` con pedidos + direcciones + wishlist.
- [ ] Carrito persistente DB.
- [ ] Sistema cupones + endpoint validar.
- [ ] Email transaccional (confirmación + magic link). Resend o SES.
- [ ] Recuperación de carrito abandonado por WhatsApp/email (cron 24h).

### Fase 3 — Pagos online y escala (3 semanas)
- [ ] Integración Bancard VPOS (Paraguay) + Mercado Pago.
- [ ] Webhook confirmación pago → cambio estado pedido.
- [ ] Reviews y rating (post-entrega, link por WA).
- [ ] Recomendaciones IA Vertex.
- [ ] Búsqueda con autocomplete + búsquedas sin resultado tracked.
- [ ] Productos relacionados.
- [ ] Sub-tiendas por vendedor (`/v/{slug}`).
- [ ] Dashboard analytics tienda en admin.
- [ ] Meta Pixel Conversions API.
- [ ] Microsoft Clarity instalado.

### Fase 4 — Crecimiento (continuo)
- [ ] Programa de referidos.
- [ ] Combos / kits de productos.
- [ ] Suscripciones (productos consumibles recurrentes).
- [ ] App móvil PWA con notificaciones push (ya tenemos VAPID).
- [ ] Internacionalización (es-PY → es-AR si se exporta).
- [ ] Comparador de productos.

---

## 14. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Pedidos fraudulentos sin login | Rate limit, verificación WhatsApp del teléfono antes de confirmar pedido grande |
| Stock vendido 2 veces | Bloqueo optimista de stock en checkout paso 5, transacción atómica |
| Carga lenta con catálogo grande | Virtualización, paginación, CDN, ImageResizing |
| SEO no indexa por SPA | NO usar SPA — server-side rendering simple (HTML hidratado) |
| Bugs en checkout pierden ventas | Logging exhaustivo + recuperación de carrito por WhatsApp |
| Cupones abusados | Límite por usuario, expiración, validación server-side estricta |
| Datos personales filtrados | RLS estricto, no exponer email/teléfono en endpoints públicos |
| WhatsApp Business API caída | Fallback a `wa.me/...` con mensaje pre-llenado |

---

## 15. Checklist legal/compliance

- [ ] Términos y condiciones redactados (revisar con abogado local PY).
- [ ] Política de privacidad (Ley 6534/20 protección de datos PY).
- [ ] Política de devoluciones y cambios.
- [ ] Política de cookies + banner consentimiento.
- [ ] Logo SET (Subsecretaría Estado Tributación) si aplica facturación.
- [ ] Datos de la empresa visibles en footer (RUC, dirección, contacto).

---

## 16. Próximos pasos sugeridos

1. **Validación del plan** con el usuario (este documento).
2. **Priorización Fase 1** — confirmar alcance MVP.
3. **División de tareas entre agentes**:
   - **Antigravity**: frontend `tienda.html`, `producto.html`, `carrito.html`, `checkout.html`.
   - **Codex**: endpoints worker `/api/tienda/...`, schema SQL.
   - **Claude (supervisor)**: revisión seguridad, integración WhatsApp, monitoreo.
4. **Wireframes** de las 5 pantallas clave antes de codear.
5. **Datos de prueba**: poblar DB con 30+ productos, 3 vendedores, 5 categorías.

---

**FIN DEL DOCUMENTO**
