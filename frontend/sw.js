const CACHE_NAME = 'torrent-player-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  'https://cdn.jsdelivr.net/npm/video.js@8.21.0/dist/video-js.min.css',
  'https://cdn.jsdelivr.net/npm/video.js@8.21.0/dist/video.min.js',
  'https://cdn.jsdelivr.net/npm/hls.js@1.5.20/dist/hls.min.js',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // API calls: network first, then cache
  if (e.request.url.includes('/api/')) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }
  // Static assets: cache first
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request))
  );
});
