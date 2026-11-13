// Service worker minimo: la app se puede abrir sin conexion con el ultimo barrido descargado.
const CACHE = "elquiosco-v2";
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/favicon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  // Red primero (para tener siempre las noticias nuevas); si no hay conexion, lo guardado.
  e.respondWith(
    fetch(e.request).then(r => {
      const copy = r.clone();
      const key = url.pathname.endsWith("portadas.json") ? new Request(url.origin + url.pathname) : e.request;
      caches.open(CACHE).then(c => c.put(key, copy));
      return r;
    }).catch(() => caches.match(url.pathname.endsWith("portadas.json") ? url.origin + url.pathname : e.request))
  );
});
