/**
 * 视频 CT 轻量埋点 SDK（自研，零第三方依赖，不采集隐私）
 *
 * 设计原则：
 * - 开发环境 console.log 输出
 * - 生产环境 POST /api/v1/analytics/events（批量，10条/30秒）
 * - 网络失败时存 localStorage，下次成功时补发
 * - 不采集明文手机号/身份证/银行卡等隐私
 */

interface TrackEvent {
  event: string;
  properties?: Record<string, unknown>;
  user_id?: number;
  timestamp: number;
}

type TrackEventName =
  // 页面浏览
  | 'page_view:home'
  | 'page_view:login'
  | 'page_view:diagnose_submit'
  | 'page_view:diagnose_detail'
  | 'page_view:report'
  | 'page_view:archive'
  | 'page_view:persona'
  | 'page_view:positioning'
  | 'page_view:subscribe'
  | 'page_view:referrer'
  | 'page_view:leaderboard'
  | 'page_view:me'
  | 'page_view:profile'
  | 'page_view:order_detail'
  // 点击行为
  | 'click:submit_diagnosis'
  | 'click:persona'
  | 'click:referrer'
  | 'click:share_report'
  | 'click:feedback'
  | 'click:copy_link'
  | 'click:subscribe_cta'
  // 转化行为
  | 'conversion:register'
  | 'conversion:login'
  | 'conversion:diagnose_submitted'
  | 'conversion:order_created'
  | 'conversion:payment_success'
  | 'conversion:share_link';

const STORAGE_KEY = 'vct_track_queue';
const FLUSH_INTERVAL_MS = 30_000; // 30 秒
const MAX_BATCH_SIZE = 10;
const SENSITIVE_KEYS = /phone|id_card|bank_card|password|secret|ssn|身份证|银行卡|密码/i;

let queue: TrackEvent[] = [];
let flushTimer: number | null = null;
let flushing = false;

// ---- 初始化：加载上次未发送的队列 ----
function loadQueue(): void {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        queue = parsed;
      }
    }
  } catch {
    queue = [];
  }
}

function saveQueue(): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  } catch {
    // localStorage 满或不可用，丢弃最旧事件
    if (queue.length > 0) {
      queue.shift();
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
      } catch {
        queue = [];
      }
    }
  }
}

// ---- 隐私过滤 ----
function sanitizeProps(props?: Record<string, unknown>): Record<string, unknown> | undefined {
  if (!props) return undefined;
  const safe: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(props)) {
    if (SENSITIVE_KEYS.test(key)) continue;
    if (typeof value === 'string' && SENSITIVE_KEYS.test(value)) continue;
    safe[key] = value;
  }
  return Object.keys(safe).length > 0 ? safe : undefined;
}

// ---- 事件入队 ----
function enqueue(event: TrackEvent): void {
  queue.push(event);
  // 超出最大队列长度时裁剪
  while (queue.length > 200) {
    queue.shift();
  }
  saveQueue();

  // 队列达到批量阈值立即发送
  if (queue.length >= MAX_BATCH_SIZE) {
    flushTrackQueue();
  }

  // 重置定时器
  if (flushTimer !== null) clearTimeout(flushTimer);
  flushTimer = window.setTimeout(flushTrackQueue, FLUSH_INTERVAL_MS);
}

// ---- 开发环境输出 ----
function devLog(event: TrackEvent): void {
  const emoji =
    event.event.startsWith('page_view') ? '📄' :
    event.event.startsWith('click') ? '👆' :
    event.event.startsWith('conversion') ? '💰' : '📊';
  console.log(
    `%c[Tracker] ${emoji} ${event.event}`,
    'color: #f59e0b; font-weight: bold;',
    event.properties || ''
  );
}

// ---- 获取当前 user_id ----
function getUserId(): number | undefined {
  try {
    const token = localStorage.getItem('vct_token');
    if (!token) return undefined;
    // JWT payload 在中段
    const parts = token.split('.');
    if (parts.length !== 3) return undefined;
    const payload = JSON.parse(atob(parts[1]));
    return payload.sub ? Number(payload.sub) : undefined;
  } catch {
    return undefined;
  }
}

// ---- 发送批量事件 ----
async function flushTrackQueue(): Promise<void> {
  if (flushing || queue.length === 0) return;
  flushing = true;

  // 开发环境直接输出
  if (import.meta.env.DEV) {
    while (queue.length > 0) {
      const ev = queue.shift()!;
      devLog(ev);
    }
    saveQueue();
    flushing = false;
    return;
  }

  const batch = queue.splice(0, MAX_BATCH_SIZE);
  const baseURL = import.meta.env.VITE_API_BASE_URL || '';

  try {
    // navigator.sendBeacon 优先（不阻塞页面卸载）
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify({ events: batch })], { type: 'application/json' });
      const sent = navigator.sendBeacon(`${baseURL}/api/v1/analytics/events`, blob);
      if (!sent) throw new Error('sendBeacon failed');
    } else {
      await fetch(`${baseURL}/api/v1/analytics/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: batch }),
        keepalive: true,
      });
    }
    // 成功发送，持久化剩余队列
    saveQueue();
  } catch {
    // 网络失败，回退到队列头部
    queue.unshift(...batch);
    saveQueue();
  } finally {
    flushing = false;
  }
}

// ---- 公开 API ----

/** 页面浏览 */
export function trackPageView(pageName: string): void {
  enqueue({
    event: `page_view:${pageName}`,
    user_id: getUserId(),
    timestamp: Date.now(),
    properties: {
      url: location.pathname,
      referrer: document.referrer || undefined,
    },
  });
}

/** 点击行为 */
export function trackClick(element: string, context?: Record<string, unknown>): void {
  enqueue({
    event: `click:${element}`,
    user_id: getUserId(),
    timestamp: Date.now(),
    properties: sanitizeProps(context),
  });
}

/** 转化行为（付费/注册/分享等） */
export function trackConversion(action: string, value?: Record<string, unknown>): void {
  enqueue({
    event: `conversion:${action}`,
    user_id: getUserId(),
    timestamp: Date.now(),
    properties: sanitizeProps(value),
  });
}

/** 手动发送队列 */
export { flushTrackQueue };

/** 页面卸载时发送（注册在 window beforeunload） */
export function setupUnloadFlush(): void {
  window.addEventListener('beforeunload', () => {
    if (queue.length === 0) return;
    const batch = queue.splice(0, queue.length);
    const baseURL = import.meta.env.VITE_API_BASE_URL || '';
    // 卸载时只用 sendBeacon
    if (navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify({ events: batch })], { type: 'application/json' });
      navigator.sendBeacon(`${baseURL}/api/v1/analytics/events`, blob);
    }
  });
}

// 初始化
loadQueue();
setupUnloadFlush();
