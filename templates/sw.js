const CACHE_NAME = "cresm-cache-v1";
const urlsToCache = [
    "/",
    "/home",
    "/static/styles.css",
    "/static/icones/Cresm_logo192.png",
    "/static/icones/Cresm_logo512.png"
];

// Instala o Service Worker e adiciona ao cache
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

// Intercepta requisições e serve do cache quando disponível
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

// Atualiza cache quando houver nova versão
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name))
            );
        })
    );
});
