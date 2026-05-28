# CHANGELOG

> 格式：`[版本] YYYY-MM-DD · 说明`  
> 完整方案演进见 `docs/02-方案/`，架构决策见 `docs/01-战略/03-技术架构.md`

---

## [v2.5-prod] 2026-05-28

### 新增
- `POST /api/v1/events/track` — 统一行为事件收集端点（suggestion_feedback / report-view / module-dwell）
- `POST /api/v1/diagnosis/{id}/resubmit` — 复诊入口端点，关联 `revisions` 表
- `ReportActionPlan.vue` 反馈按钮数据流接入 events/track + suggestion_id 关联

### 变更
- 反馈按钮从通用 `/api/v1/feedback` 改为结构化 `/api/v1/events/track`

---

## [v2.5] 2026-05-27

### 新增
- TikHub API 真实视频数据接入（`services/api/app/services/crawler.py`）
- AnySearch 竞品搜索真实化，替换 Mock 数据
- 视频诊断全链路真实化（URL → 元数据 → OCR/ASR → CT 诊断官）
- `DataSourcePanel.vue` — 报告数据血缘图（Phase 1 提前交付）
- 动态因子权重系统 + 信号中心 + 右抽屉组件
- `account_health_snapshots` / `recurring_issues` 表结构（Phase 1 准备）

### 变更
- `diagnoses` 表新增 `account_id` / `diagnosis_sequence` 列（零风险 NULL + DEFAULT）

---

## [v2.4] 2026-05-26

### 新增
- 完整 v3 数据库 schema（52 张表，含信号/维度权重/v3 报告/练习表）
- Alembic 迁移脚本 9 个（含历史基线）
- Docker Compose 17 服务（PG/Redis/Kafka/MinIO/Whisper/PaddleOCR/Celery/Nginx）
- GitHub Actions CI/CD（`ci.yml` + `cd.yml`）
- Playwright E2E 测试（3 spec，覆盖 API 健康 + H5 关键路径 + 支付流程）
- Grafana 3 个仪表板（CEO 总览 / 增长 / 产品健康）
- `packages/shared` — 跨端共享 TS 类型 + 设计令牌 + API 客户端

### 变更
- `apps/open` 升级为 VitePress 文档站，含 API 参考 + SDK 说明

---

## [v2.0] 2026-05-24

### 新增
- 7 层错误处理体系（`app/core/error_handler.py`）
- Checkpoint 持久化机制（诊断任务断点续跑）
- Celery 异步任务队列接入（替换同步处理）
- Kafka 事件总线（`EventBus` 类）
- 8 个 AI Agent 实现：CT 诊断官 / 对标分析师 / 人设观察员 / 商业策略师 / 内容生成手 / 数据预警员 / 顾问助理 / 客户成功管家
- Agent 编排器（`orchestrator.py`）A2A 协同

### 变更
- 诊断流程从同步改为异步（Celery + WebSocket 推送）
- 错误处理从简单 try/except 升级为分级熔断 + 自动修复

---

## [v1.2] 2026-05-22

### 新增
- Vue 3 + Vant H5 重构（替换原生 HTML）
- 16 路由 / 34 页面 / 40+ 组件
- Pinia 状态管理（10 个 store）
- 管理后台 (`apps/admin`) — 用户 / 订单 / 分享官 / 风控 / 看板
- 顾问后台 (`apps/consultant`) — 客户档案 / AI 报告复审 / 月度复盘

### 变更
- 前端工程从单文件迁移到 pnpm Monorepo

---

## [v1.0] 2026-05-19

### 初始版本
- FastAPI 后端骨架（鉴权 / 订阅 / 诊断 / 对标 / 档案 / 人设 / 定位 / 分享官）
- SQLite 单机模式（开发兜底）
- 基础 H5 原型（原生 HTML）
- PRO 99/月 · MAX 499/月 · 单次 19 元定价模型

---

> 下一版本：[v3.0-phase0] — 5 张新表 + MediaCrawler 对标采集 + 账号个人中心页  
> 详见 [`docs/07-进度/00-当前待办.md`](docs/07-进度/00-当前待办.md)
