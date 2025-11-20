CACHE_NAME = 'signage-v1';  // this can be updated to force service worker update

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.open(CACHE_NAME).then(function(cache) {
            return fetch(event.request).then(function(response) {
                cache.put(event.request, response.clone());
                return response;
            }).catch(function () {
                return caches.match(event.request);
            });
        })
    );
});
