/* Service Worker: يجعل الموقع تطبيقاً قابلاً للتثبيت، يعمل بلا إنترنت، ويعرض الإشعارات */
const CACHE = 'cem-shell-v8';
const SHELL = ['/', 'index.html', 'site-origin.js', 'favicon-192.png', 'favicon-48.png', 'manifest.webmanifest'];

self.addEventListener('install', (e)=>{
  e.waitUntil(caches.open(CACHE).then(c=> Promise.all(SHELL.map(u=> c.add(u).catch(()=>{})))).then(()=> self.skipWaiting()));
});
self.addEventListener('activate', (e)=>{
  e.waitUntil(caches.keys().then(keys=> Promise.all(keys.filter(k=> k !== CACHE).map(k=> caches.delete(k)))).then(()=> self.clients.claim()));
});
self.addEventListener('fetch', (e)=>{
  const req = e.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  if(url.origin !== location.origin) return;           // لا نتدخل في Firebase ولا الخطوط ولا المنصات
  if(url.pathname === '/admin' || url.pathname.endsWith('admin.html')) return;   // لوحة الإدارة دائماً من الشبكة
  if(url.pathname.startsWith('/n/') || url.pathname === '/sitemap-news.xml') return; // صفحات الأخبار تُجلب حيّة دائماً
  if(req.mode === 'navigate'){                          // الصفحات: الشبكة أولاً ثم النسخة المخزنة
    e.respondWith(fetch(req).then(res=>{
      if(res.ok && (url.pathname === '/' || url.pathname.endsWith('/index.html'))){ const copy = res.clone(); caches.open(CACHE).then(c=> c.put('index.html', copy)); }
      return res;
    }).catch(()=> caches.match('index.html')));
    return;
  }
  e.respondWith(caches.match(req).then(hit=> hit || fetch(req).then(res=>{
    if(res.ok){ const copy = res.clone(); caches.open(CACHE).then(c=> c.put(req, copy)); }
    return res;
  })));
});
// النقر على إشعار: افتح التطبيق على القسم المطلوب
self.addEventListener('notificationclick', (e)=>{
  e.notification.close();
  const hash = (e.notification.data && e.notification.data.hash) || '#home';
  e.waitUntil(self.clients.matchAll({ type:'window', includeUncontrolled:true }).then(list=>{
    for(const c of list){ if('focus' in c){ c.focus(); c.postMessage({ type:'nav', hash }); return; } }
    return self.clients.openWindow('/' + hash);
  }));
});
