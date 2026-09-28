// Conflux public event site service worker (VS22): caches the installable
// shell (stylesheets/icon/manifest) plus previously-visited event pages, so
// a returning visitor with no network still sees the last real content
// they loaded instead of the browser's offline error page. Deliberately
// simple: this is a server-rendered site, not a SPA, so there is no client
// data to reconcile -- only HTTP responses to cache and replay.
const CACHE = "conflux-shell-v2";
const SHELL = [
  "/static/tokens.css",
  "/static/components.css",
  "/static/presentation.css",
  "/static/manifest.webmanifest",
  "/static/icon.svg",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Event pages: network-first (content changes constantly -- agenda,
  // projects, announcements), falling back to the last cached copy when
  // the network is unavailable.
  if (url.pathname.startsWith("/e/")) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const policy = response.headers.get("Cache-Control") || "";
          if (!response.ok || /\bno-store\b/i.test(policy)) {
            event.waitUntil(
              caches.open(CACHE).then((cache) => cache.delete(request)),
            );
            return response;
          }
          const copy = response.clone();
          event.waitUntil(
            caches.open(CACHE).then((cache) => cache.put(request, copy)),
          );
          return response;
        })
        .catch(() =>
          caches.match(request).then((cached) => cached || Response.error()),
        ),
    );
    return;
  }

  // Shell assets: cache-first, since the cache name itself is the version.
  if (SHELL.some((path) => url.pathname === path)) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request)),
    );
  }
});
