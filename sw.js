/* BB Graphic System service worker.

   NETWORK-FIRST for everything we serve, so a new build always wins. A
   cache-first worker is how a team ends up staring at a board that moved on
   hours ago and swearing the app is broken.

   THE RULE THIS WORKER EXISTS TO KEEP: never cache the database. Supabase
   responses are the live state of the team's work. A stale board is worse than
   no board, because somebody ticks a post that was already approved. Only the
   shell is cached, and only as a fallback for having no signal.
*/
const CACHE = 'bb-graphic-v1';
const SHELL = ['./', './manifest.json', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;  /* never touch third-party */
  /* Belt and braces: the database is same-origin to nobody, but if it ever is,
     it must still never be cached. */
  if (url.pathname.indexOf('/rest/v1/') > -1 || url.pathname.indexOf('/auth/v1/') > -1) return;
  e.respondWith(
    fetch(req)
      .then(res => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      })
      .catch(() => caches.match(req).then(hit => hit || caches.match('./')))
  );
});

/* ── BB PUSH (hub build 2026-09-04) ──────────────────────────────────────────
   Receives a push from the bb-push edge function and shows it. A tap opens
   the app at the URL the alert carried, focusing an open window if there is
   one rather than stacking a second copy. Nothing here touches the cache
   rules above. */
self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { body: event.data ? event.data.text() : '' }; }
  var title = data.title || 'Business Booster';
  var opts = {
    body: data.body || 'Open the app to see what changed.',
    icon: './icon-192.png',
    badge: './icon-192.png',
    tag: data.tag || 'bb-alert',
    renotify: true,
    data: { url: data.url || './' }
  };
  event.waitUntil(self.registration.showNotification(title, opts));
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var target = (event.notification.data && event.notification.data.url) || './';
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) {
      if ('focus' in list[i]) { list[i].navigate && list[i].navigate(target); return list[i].focus(); }
    }
    return clients.openWindow(target);
  }));
});
