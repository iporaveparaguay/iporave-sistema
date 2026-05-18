// Iporãve Service Worker — offline robusto para delivery en la calle
// Estrategias:
//  - App shell (HTML/CSS/JS/iconos): CacheFirst con revalidación
//  - APIs (/api/): NetworkFirst con fallback a caché y respuesta offline
//  - Supabase / Anthropic / Mapbox tiles: bypass salvo tiles ya cacheados
//  - Push y notificationclick preservados
//  - Background Sync: dispara mensaje a clientes para drenar cola offline

const CACHE_VERSION = 'v40';
const CACHE_STATIC = 'iporave-static-' + CACHE_VERSION;
const CACHE_API = 'iporave-api-cache-v1';
const CACHE_TILES = 'iporave-tiles-v1';
const BASE = self.location.pathname.replace('/sw.js', '');

const APP_SHELL = [
  BASE + '/',
  BASE + '/index.html',
  BASE + '/manifest.json',
  BASE + '/icon-192.png',
  BASE + '/icon-512.png'
];

// Install — pre-cache app shell granular (FIX 12: no fallar todo si uno falla)
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_STATIC).then(cache =>
      Promise.allSettled(APP_SHELL.map(url =>
        cache.add(url).catch(e => console.warn('SW pre-cache fail:', url, e && e.message))
      ))
    )
  );
  self.skipWaiting();
});

// Activate — limpiar caches antiguos
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k.startsWith('iporave-') &&
                       k !== CACHE_STATIC &&
                       k !== CACHE_API &&
                       k !== CACHE_TILES)
          .map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

// Push — notificación al delivery
self.addEventListener('push', event => {
  let data = { title: '📦 Iporãve', body: 'Nueva notificación', url: '/pedidos' };
  try { data = Object.assign(data, event.data.json()); } catch (_) {}
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      data: { url: data.url },
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(clients.openWindow(url));
});

// Mensajes desde el cliente
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

// Background Sync — notificar a los clientes para que drenen su cola offline
self.addEventListener('sync', event => {
  if (event.tag === 'sync-orders' || event.tag === 'iporave-sync') {
    event.waitUntil(_notifyClientsToSync());
  }
});

async function _notifyClientsToSync() {
  const all = await self.clients.matchAll({ includeUncontrolled: true });
  all.forEach(c => c.postMessage({ type: 'SYNC_OFFLINE_QUEUE' }));
}

// Fetch — estrategias por tipo de recurso
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Bypass: Supabase / Anthropic (necesitan auth real-time)
  if (url.hostname.includes('supabase.co')) return;
  if (url.hostname.includes('anthropic')) return;

  // Mapbox tiles — CacheFirst para mapa offline en la calle
  if (url.hostname.includes('mapbox.com') ||
      url.hostname.includes('tile.openstreetmap') ||
      url.pathname.includes('/tiles/')) {
    event.respondWith(_cacheFirst(req, CACHE_TILES));
    return;
  }

  // APIs propias: NetworkFirst con fallback a caché y respuesta offline JSON
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(_networkFirstApi(req));
    return;
  }

  // Navegación / HTML / app shell — NetworkFirst con timeout 3s
  // (evita servir HTML viejo post-deploy; fixes urgentes llegan al primer load)
  if (req.mode === 'navigate' ||
      req.destination === 'document' ||
      url.pathname.endsWith('.html') ||
      url.pathname === BASE + '/' ||
      url.pathname === '/') {
    event.respondWith(_networkFirstHtml(req, CACHE_STATIC, BASE + '/index.html'));
    return;
  }

  // Resto (CSS/JS/imágenes/fuentes): stale-while-revalidate
  event.respondWith(_staleWhileRevalidate(req, CACHE_STATIC, null));
});

async function _cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  if (cached) return cached;
  try {
    const resp = await fetch(req);
    if (resp && resp.status === 200) cache.put(req, resp.clone());
    return resp;
  } catch (_) {
    return cached || new Response('', { status: 504 });
  }
}

async function _networkFirstApi(req) {
  try {
    const resp = await fetch(req);
    if (resp && resp.ok) {
      const clone = resp.clone();
      caches.open(CACHE_API).then(c => c.put(req, clone)).catch(() => {});
    }
    return resp;
  } catch (_) {
    const cached = await caches.match(req);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ error: 'offline', cached: false, queued: true }),
      { status: 503, headers: { 'Content-Type': 'application/json' } }
    );
  }
}

async function _networkFirstHtml(req, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  try {
    const networkPromise = fetch(req);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('timeout')), 3000));
    const resp = await Promise.race([networkPromise, timeoutPromise]);
    if (resp && resp.ok) {
      cache.put(req, resp.clone()).catch(() => {});
      return resp;
    }
  } catch (_) {
    // network failed o timeout — caer a caché
  }
  const cached = await cache.match(req);
  if (cached) return cached;
  if (fallbackUrl) {
    const fb = await caches.match(fallbackUrl);
    if (fb) return fb;
  }
  return new Response('Sin conexión', { status: 503 });
}

async function _staleWhileRevalidate(req, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fetchPromise = fetch(req).then(resp => {
    if (resp && resp.status === 200) cache.put(req, resp.clone()).catch(() => {});
    return resp;
  }).catch(() => {
    if (fallbackUrl) return caches.match(fallbackUrl);
    return cached;
  });
  return cached || fetchPromise;
}
