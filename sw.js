var CACHE = "potret-sekitar-v2";
var INTI = ["./", "index.html", "logo-potret.png", "manifest.webmanifest", "icon-192.png", "icon-512.png"];
self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(INTI); }).then(function(){ return self.skipWaiting(); }));
});
self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.map(function(k){ if(k !== CACHE) return caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener("fetch", function(e){
  if(e.request.method !== "GET") return;
  var url = e.request.url;
  if(url.indexOf("berita.json") >= 0 || url.indexOf("agenda.json") >= 0){
    /* data berita: utamakan jaringan, cadangan cache */
    e.respondWith(fetch(e.request).then(function(r){
      var salin = r.clone();
      caches.open(CACHE).then(function(c){ c.put(e.request, salin); });
      return r;
    }).catch(function(){ return caches.match(e.request); }));
    return;
  }
  e.respondWith(caches.match(e.request).then(function(hit){
    return hit || fetch(e.request).then(function(r){
      var salin = r.clone();
      caches.open(CACHE).then(function(c){ c.put(e.request, salin); });
      return r;
    });
  }));
});
