// =============================================================================
// Video CT · API 健康检查 E2E 测试
// 通过 HTTP 直接调用后端 API，不依赖 H5 前端
// =============================================================================
import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_URL || 'http://localhost:8000';

test.describe('API 健康检查', () => {
  // ─── 1. GET /healthz → 200 ───
  test('GET /healthz → 200', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/healthz`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body).toHaveProperty('status', 'ok');
  });

  // ─── 2. GET /readyz → 200 ───
  test('GET /readyz → 200', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/readyz`);
    // readyz 可能返回 200 或 503（取决于数据库连接）
    expect([200, 503]).toContain(resp.status());
  });

  // ─── 3. GET /docs → 200（Swagger UI） ───
  test('GET /docs → 200（Swagger UI）', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/docs`);
    expect(resp.status()).toBe(200);
    // Swagger HTML 应包含特征字符串
    const html = await resp.text();
    expect(html).toContain('swagger');
  });

  // ─── 4. GET /api/v1/subscriptions/products → 200 + 返回数组 ───
  test('GET /api/v1/subscriptions/products → 200 + 返回数组', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/api/v1/subscriptions/products`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
  });
});
