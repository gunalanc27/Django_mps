const CACHE_NAME = 'gpz-store-image-cache-v1';
const IMAGE_TYPES = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'];

// Cache images from Cloudinary and Media
const isImageRequest = (request) => {
    const url = request.url.toLowerCase();
    return IMAGE_TYPES.some(type => url.endsWith(type)) || 
           url.includes('res.cloudinary.com') || 
           url.includes('/media/');
};

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;

    if (isImageRequest(event.request)) {
        event.respondWith(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.match(event.request).then((response) => {
                    if (response) {
                        // Return from cache, but update cache in background (Stale-While-Revalidate)
                        fetch(event.request).then((networkResponse) => {
                            cache.put(event.request, networkResponse.clone());
                        });
                        return response;
                    }

                    // Not in cache, fetch and put in cache
                    return fetch(event.request).then((networkResponse) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                });
            })
        );
    }
});
