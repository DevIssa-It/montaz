/* montaz service worker — minimal, network-first.
   Exists mainly so the app is installable as a PWA; it never serves stale
   API responses (API traffic bypasses the worker entirely). Static assets
   fall back to the cache only when the local server is unreachable. */
const CACHE = "montaz-static-v1"

self.addEventListener("install", () => self.skipWaiting())

self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()))

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url)
  if (event.request.method !== "GET" || !url.origin.startsWith("http")) return
  if (url.pathname.startsWith("/api/")) return // always live

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok && url.origin === self.location.origin) {
          const copy = response.clone()
          event.waitUntil(
            caches.open(CACHE).then((cache) => cache.put(event.request, copy))
          )
        }
        return response
      })
      .catch(() => caches.match(event.request))
  )
})
