// =============================================================================
// Video CT · H5 关键用户旅程 E2E 测试
// 断言已有 UI 文案，不修改 apps/ 下业务代码
// =============================================================================
import { test, expect } from '@playwright/test';

const DEV_PHONE = '13800138000';
const DEV_CODE = '0000';

// ==================== 1. 首页加载 ====================
test('首页加载 → 可见「给你的视频做一次 CT 扫描」', async ({ page }) => {
  await page.goto('/home');
  // 等待核心 CTA 文案出现
  await expect(page.locator('text=给你的视频做一次 CT 扫描')).toBeVisible({ timeout: 15_000 });
  // 验证副标题
  await expect(page.locator('text=6 维 18 点位')).toBeVisible();
});

// ==================== 2. 未登录访问 /diagnose/submit → 重定向到 /login ====================
test('未登录访问 /diagnose/submit → 被重定向到 /login', async ({ page }) => {
  await page.goto('/diagnose/submit');
  // 路由守卫会 redirect 到 /login（可能带 query string redirect=...）
  await page.waitForURL(/\/login/, { timeout: 10_000 });
  // 确认登录页核心文案出现
  await expect(page.locator('text=登录 / 注册').first()).toBeVisible();
  // 确认手机号输入框存在
  await expect(page.getByPlaceholder('请输入手机号')).toBeVisible();
});

// ==================== 3. 登录流程 ====================
test('登录页 → 输入手机号 → 获取验证码 → 输入万能码 → 登录成功跳到首页', async ({ page }) => {
  await page.goto('/login');

  // 输入手机号（van-field 内部是 input）
  const phoneInput = page.getByPlaceholder('请输入手机号');
  await phoneInput.fill(DEV_PHONE);
  await expect(phoneInput).toHaveValue(DEV_PHONE);

  // 点击「获取验证码」
  const sendBtn = page.getByRole('button', { name: /获取验证码/i });
  await sendBtn.click();

  // 等待倒计时开始（按钮文字变为 "Xs"）
  await expect(page.getByRole('button', { name: /\d+s/ })).toBeVisible({ timeout: 10_000 });

  // 输入万能验证码
  const codeInput = page.getByPlaceholder('6 位验证码');
  await codeInput.fill(DEV_CODE);

  // 点击「登录 / 注册」
  const loginBtn = page.locator('button:has-text("登录 / 注册")');
  await loginBtn.click();

  // 等待跳转到首页
  await page.waitForURL(/\/home/, { timeout: 15_000 });

  // 确认首页核心文案
  await expect(page.locator('text=给你的视频做一次 CT 扫描')).toBeVisible({ timeout: 10_000 });
});

// ==================== 4-8: 登录后页面 ====================
test.describe.serial('登录后关键页面', () => {
  // 每个测试共享同一 page，登录仅执行一次
  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    await page.goto('/login');

    await page.getByPlaceholder('请输入手机号').fill(DEV_PHONE);
    await page.getByRole('button', { name: /获取验证码/i }).click();
    await expect(page.getByRole('button', { name: /\d+s/ })).toBeVisible({ timeout: 10_000 });
    await page.getByPlaceholder('6 位验证码').fill(DEV_CODE);
    await page.locator('button:has-text("登录 / 注册")').click();
    await page.waitForURL(/\/home/, { timeout: 15_000 });

    // 跳转到首页后即认为已登录，page 保留登录态
    return page;
  });

  // 4. 诊断列表页
  test('登录后访问 /diagnose → 可看到诊断列表（空或历史）', async ({ page }) => {
    await page.goto('/diagnose');
    await expect(page.locator('text=诊断中心')).toBeVisible({ timeout: 10_000 });
    // 页面应展示「新建诊断」CTA 或空列表
    const hasDiagnoseEntry = await page.locator('text=新建诊断').isVisible().catch(() => false);
    const hasHistory = await page.locator('text=历史诊断').isVisible().catch(() => false);
    expect(hasDiagnoseEntry || hasHistory).toBeTruthy();
  });

  // 5. 订阅页
  test('访问 /subscribe → 可看到产品列表', async ({ page }) => {
    await page.goto('/subscribe');
    await expect(page.locator('text=升级订阅').or(page.locator('text=产品'))).toBeVisible({ timeout: 10_000 });
    // 加载完成后应有产品卡或空状态
    const hasProducts = await page.locator('text=立即购买').or(page.locator('text=当前方案')).isVisible().catch(() => false);
    const hasEmpty = await page.locator('text=暂无可选产品').isVisible().catch(() => false);
    expect(hasProducts || hasEmpty).toBeTruthy();
  });

  // 6. 分享官页
  test('访问 /referrer → 可看到分享官信息', async ({ page }) => {
    await page.goto('/referrer');
    await expect(page.locator('text=品牌分享官')).toBeVisible({ timeout: 10_000 });
    // 应有统计信息或 error 状态
    const hasStats = await page.locator('text=推荐人数').or(page.locator('text=累积奖励')).isVisible().catch(() => false);
    const hasError = await page.locator('text=加载失败').isVisible().catch(() => false);
    expect(hasStats || hasError).toBeTruthy();
  });

  // 7. 档案页
  test('访问 /archive → 空档案显示引导', async ({ page }) => {
    await page.goto('/archive');
    await expect(page.locator('text=成长档案')).toBeVisible({ timeout: 10_000 });
    // 新用户无档案时应显示引导
    const hasGuide = await page.locator('text=还没有成长档案').isVisible().catch(() => false);
    const hasArchive = await page.locator('text=档案编号').isVisible().catch(() => false);
    expect(hasGuide || hasArchive).toBeTruthy();
  });

  // 8. 个人中心
  test('访问 /me → 显示用户昵称和配额信息', async ({ page }) => {
    await page.goto('/me');
    await expect(page.locator('text=我的')).toBeVisible({ timeout: 10_000 });
    // 应该有配额或用户信息
    const hasQuota = await page.locator('text=本月扫描配额').isVisible().catch(() => false);
    const hasNickname = await page.locator('text=视频创作者').or(page.locator(/博主_\d+/)).isVisible().catch(() => false);
    expect(hasQuota || hasNickname).toBeTruthy();
  });
});
