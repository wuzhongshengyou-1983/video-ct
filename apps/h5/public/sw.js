/* 视频 CT Service Worker — 离线缓存 + 静态资源加速 */
const CACHE_NAME = 'video-ct-v1';

// 预缓存的关键路由（页面壳）
const PRE_CACHE_URLS = [
  '/',
  '/home',
  '/diagnose',
  '/subscribe',
  '/me',
  '/login',
  '/manifest.json',
  '/favicon.ico',
];

// 静态资源类型白名单（Cache First）
const STATIC_EXT = /\.(?:js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/i;

// API 路径前缀（Network First）
const API_PREFIX = '/api/';

// 报告路径（Network First + 成功后缓存）
const REPORT_PATH = /^\/report\//;

/* ---- install: 预缓存页面壳 ---- */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRE_CACHE_URLS).catch((err) => {
        console.warn('[sw] pre-cache partial fail:', err.message);
      });
    })
  );
  self.skipWaiting();
});

/* ---- activate: 清理旧版本缓存 ---- */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    })
  );
  self.clients.claim();
});

/* ---- fetch: 核心策略 ---- */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 只处理 GET 请求
  if (request.method !== 'GET') return;

  // 非同源请求跳过（除了 CDN 静态资源）
  if (url.origin !== self.location.origin) return;

  const pathname = url.pathname;

  // 策略 1：API 请求 / 报告页 → Network First（成功后缓存）
  if (API_PREFIX.includes(pathname) || REPORT_PATH.test(pathname)) {
    event.respondWith(networkFirst(request));
    return;
  }

  // 策略 2：静态资源 → Cache First
  if (STATIC_EXT.test(pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  // 策略 3：HTML 导航请求 → Network First（获取最新壳）
  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  // 默认：Cache First
  event.respondWith(cacheFirst(request));
});

/* ====== 策略实现 ====== */

// Network First: 先网络，失败或超时则读缓存
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetchWithTimeout(request, 8000);
    // 成功响应（200）才缓存
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (_err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    // API 请求无缓存时返回离线提示
    if (API_PREFIX.includes(new URL(request.url).pathname)) {
      return new Response(
        JSON.stringify({ code: 'OFFLINE', message: '当前无网络连接' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      );
    }
    throw _err;
  }
}

// Cache First: 先缓存，缓存无则走网络并缓存
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (_err) {
    // 图片请求无缓存返回占位
    if (/\.(?:png|jpg|jpeg|gif|svg|ico)$/i.test(new URL(request.url).pathname)) {
      return new Response(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>',
        { status: 200, headers: { 'Content-Type': 'image/svg+xml' } }
      );
    }
    throw _err;
  }
}

// 带超时的 fetch
function fetchWithTimeout(request, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => reject(new Error('fetch timeout')), timeoutMs);
    fetch(request)
      .then((res) => {
        clearTimeout(timeoutId);
        resolve(res);
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        reject(err);
      });
  });
}
