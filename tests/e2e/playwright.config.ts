// =============================================================================
// Video CT · Playwright E2E 配置
// =============================================================================
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  // CI 重试 2 次，本地不重试
  retries: process.env.CI ? 2 : 0,
  // 并行 worker
  workers: process.env.CI ? 2 : undefined,
  // 报告
  reporter: [
    ['list'],
    ['html', { outputFolder: '../../playwright-report', open: 'never' }],
  ],
  // 失败时截图
  use: {
    baseURL: process.env.H5_URL || 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
  // 全局超时
  globalTimeout: process.env.CI ? 300_000 : undefined,

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 本地开发时启用 webServer 自动启动（CI 通过 docker compose 启动）
  webServer: process.env.CI
    ? undefined
    : [
        {
          command: 'uvicorn app.main:app --host 0.0.0.0 --port 8000',
          url: 'http://localhost:8000/healthz',
          reuseExistingServer: true,
          cwd: '../../services/api',
          timeout: 30_000,
        },
        {
          command: 'npx vite --port 5173 --strictPort',
          url: 'http://localhost:5173',
          reuseExistingServer: true,
          cwd: '../../apps/h5',
          timeout: 30_000,
        },
      ],

  // 输出目录
  outputDir: '../../test-results',
});
