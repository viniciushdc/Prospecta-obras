// Service worker: app sempre busca a versão nova (rede primeiro); cache só como reserva offline.
const CACHE = 'prospecta-v16';
const SHELL = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png', './apple-touch-icon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  const netFirst = e.request.mode === 'navigate'
    || url.pathname.endsWith('/')
    || url.pathname.endsWith('index.html')
    || url.pathname.endsWith('leads.json')
    || url.pathname.endsWith('sw.js');
  if (netFirst) {
    // rede primeiro: sempre tenta o mais novo; cache como reserva (offline)
    e.respondWith(fetch(e.request).then(r => { const cp = r.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); return r; }).catch(() => caches.match(e.request)));
  } else {
    // ícones/manifest: cache primeiro (mudam pouco)
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
