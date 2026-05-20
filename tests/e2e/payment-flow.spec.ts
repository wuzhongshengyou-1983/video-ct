// =============================================================================
// Video CT · 支付链路 E2E 测试
// 下单 → 获取支付参数 → 模拟支付回调 → 验证订阅激活
// =============================================================================
import { test, expect } from '@playwright/test';

const API_BASE = process.env.API_URL || 'http://localhost:8000';
const DEV_PHONE = '13800138000';
const DEV_CODE = '0000';

// 全局 token
let authToken = '';
let userId = 0;

// ==================== 0. 前置：登录获取 token ====================
test.describe.serial('支付全链路', () => {

  test.beforeAll(async ({ request }) => {
    // 发送验证码
    const otpResp = await request.post(`${API_BASE}/api/v1/auth/otp/send`, {
      data: { phone: DEV_PHONE },
    });
    expect(otpResp.ok()).toBeTruthy();

    // 登录
    const loginResp = await request.post(`${API_BASE}/api/v1/auth/login`, {
      data: { phone: DEV_PHONE, code: DEV_CODE },
    });
    expect(loginResp.ok()).toBeTruthy();
    const loginData = await loginResp.json();
    authToken = loginData.access_token || loginData.data?.access_token || '';
    userId = loginData.user_id || loginData.data?.user_id || 0;
    expect(authToken).toBeTruthy();
    expect(userId).toBeGreaterThan(0);
  });

  // ─── 1. 产品列表 ───
  test('GET /api/v1/subscriptions/products → 返回产品列表（含 PRO）', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/api/v1/subscriptions/products`);
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(Array.isArray(body)).toBe(true);
    expect(body.length).toBeGreaterThan(0);
    // 必须有 pro 产品
    const proProduct = body.find((p: any) => p.tier === 'pro');
    expect(proProduct).toBeDefined();
    expect(proProduct.price_cny).toBeGreaterThan(0);
  });

  // ─── 2. 创建订单 → 返回支付参数 ───
  let orderNo = '';
  let payParams: any = null;

  test('POST /api/v1/subscriptions/orders → 创建订单 + 返回支付参数', async ({ request }) => {
    const resp = await request.post(`${API_BASE}/api/v1/subscriptions/orders`, {
      headers: { Authorization: `Bearer ${authToken}` },
      data: { sku: 'PRO_MONTHLY_V1', use_deduction: false },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.order_no).toBeTruthy();
    expect(body.payment_status).toBe('pending');
    orderNo = body.order_no;

    // 必须有支付参数
    payParams = body.pay_params;
    expect(payParams).toBeDefined();
    expect(payParams.order_no).toBe(orderNo);
    // mock 模式或真实支付参数
    expect(payParams.mock !== undefined).toBeTruthy();
    if (!payParams.mock) {
      expect(payParams.appId).toBeTruthy();
      expect(payParams.package).toContain('prepay_id=');
      expect(payParams.paySign).toBeTruthy();
    }
  });

  // ─── 3. 获取支付参数（补拉接口） ───
  test('GET /api/v1/subscriptions/orders/{order_no}/pay-params → 返回支付参数', async ({ request }) => {
    const resp = await request.get(
      `${API_BASE}/api/v1/subscriptions/orders/${orderNo}/pay-params`,
      { headers: { Authorization: `Bearer ${authToken}` } },
    );
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.order_no).toBe(orderNo);
    expect(body.mock !== undefined).toBeTruthy();
    if (!body.mock) {
      expect(body.app_id).toBeTruthy();
      expect(body.package).toContain('prepay_id=');
    }
  });

  // ─── 4. 查询支付状态（待支付） ───
  test('GET /api/v1/subscriptions/orders/{order_no}/status → 返回 pending', async ({ request }) => {
    const resp = await request.get(
      `${API_BASE}/api/v1/subscriptions/orders/${orderNo}/status`,
      { headers: { Authorization: `Bearer ${authToken}` } },
    );
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.order_no).toBe(orderNo);
    expect(body.payment_status).toBe('pending');
  });

  // ─── 5. 模拟支付回调 ───
  test('POST /api/v1/webhooks/wechat/pay → 模拟回调 + 激活订阅', async ({ request }) => {
    // 构造微信回调 body（mock 模式）
    const callbackBody = {
      id: `evt_mock_${Date.now()}`,
      create_time: new Date().toISOString(),
      resource_type: 'encrypt-resource',
      event_type: 'TRANSACTION.SUCCESS',
      summary: '支付成功',
      resource: {
        ciphertext: JSON.stringify({
          out_trade_no: orderNo,
          transaction_id: `txn_mock_${orderNo}`,
          trade_state: 'SUCCESS',
          amount: { total: 9900, currency: 'CNY' },
          payer: { openid: `mock_openid_${userId}` },
          success_time: new Date().toISOString(),
        }),
        nonce: 'mock_nonce_123456',
        associated_data: 'mock_ad',
      },
    };

    const resp = await request.post(`${API_BASE}/api/v1/webhooks/wechat/pay`, {
      headers: {
        'Content-Type': 'application/json',
        'Wechatpay-Signature': 'mock_sig',
        'Wechatpay-Nonce': 'mock_nonce',
        'Wechatpay-Timestamp': String(Math.floor(Date.now() / 1000)),
        'Wechatpay-Serial': 'mock_serial',
      },
      data: callbackBody,
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    // 微信回调成功应答必须返回 SUCCESS
    expect(body.code).toBe('SUCCESS');
  });

  // ─── 6. 验证订阅已激活 ───
  test('GET /api/v1/subscriptions/orders/{order_no}/status → 返回 paid', async ({ request }) => {
    const resp = await request.get(
      `${API_BASE}/api/v1/subscriptions/orders/${orderNo}/status`,
      { headers: { Authorization: `Bearer ${authToken}` } },
    );
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.payment_status).toBe('paid');
    expect(body.paid_at).toBeTruthy();
  });

  // ─── 7. 验证订阅信息 ───
  test('GET /api/v1/subscriptions/my → 返回有效订阅', async ({ request }) => {
    const resp = await request.get(`${API_BASE}/api/v1/subscriptions/my`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body).toBeTruthy();
    expect(body.tier).toBe('pro');
    expect(body.status).toBe('active');
    expect(body.expires_at).toBeTruthy();
    // 验证 expires_at 是未来时间
    const expiresAt = new Date(body.expires_at);
    expect(expiresAt.getTime()).toBeGreaterThan(Date.now());
  });

  // ─── 8. 取消订阅 ───
  test('POST /api/v1/subscriptions/cancel → 成功取消', async ({ request }) => {
    const resp = await request.post(`${API_BASE}/api/v1/subscriptions/cancel`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.ok).toBe(true);
    expect(body.expires_at).toBeTruthy();
  });

  // ─── 9. 重复回调幂等（已支付订单再次回调） ───
  test('POST /api/v1/webhooks/wechat/pay → 重复回调返回 SUCCESS（幂等）', async ({ request }) => {
    const callbackBody = {
      id: `evt_mock_dup_${Date.now()}`,
      resource: { ciphertext: JSON.stringify({ out_trade_no: orderNo }) },
    };
    const resp = await request.post(`${API_BASE}/api/v1/webhooks/wechat/pay`, {
      headers: {
        'Content-Type': 'application/json',
        'Wechatpay-Signature': 'mock_dup_sig',
        'Wechatpay-Nonce': 'mock_dup_nonce',
        'Wechatpay-Timestamp': String(Math.floor(Date.now() / 1000)),
        'Wechatpay-Serial': 'mock_dup_serial',
      },
      data: callbackBody,
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.code).toBe('SUCCESS');
  });
});
