# 测试说明

## 目录结构

```
tests/
└── e2e/        Playwright E2E 测试（前端 + API 集成）

services/api/tests/   后端单元 / 集成测试（pytest）
```

> 两个 tests 目录是故意的：E2E 属于全栈范畴放仓根，后端单测属于 api 服务内部。

---

## 运行方式

### E2E 测试（需后端 + H5 先启动）

```bash
# 全量
pnpm test:e2e

# 仅 API 健康检查（无需 H5）
npx playwright test api-health --config tests/e2e/playwright.config.ts

# 仅支付流程
npx playwright test payment-flow --config tests/e2e/playwright.config.ts

# 查看报告
npx playwright show-report playwright-report/
```

### 后端单测

```bash
cd services/api
source .venv/bin/activate
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 覆盖现状

见 [`docs/07-进度/07-测试覆盖现状.md`](../docs/07-进度/07-测试覆盖现状.md)

当前高风险空白：CT 诊断 Agent、Celery 任务状态机、WebSocket 推送。
