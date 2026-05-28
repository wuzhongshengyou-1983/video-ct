# 视频 CT · Video CT

> **像影像科医生一样诊断短视频** —— AI 月度体检 + 头部对标 + 终身成长档案 + 顾问陪跑

PRO 99/月 · MAX 499/月 · 每月免费 3 次扫描 · 单次 19 元

---

## 这是什么

`video-ct` 是一个完整的 SaaS + 陪跑业务的代码实现，包含：

- **C 端 H5**（`apps/h5`）— 普通博主自助：注册、付费、提交视频、看 CT 报告、对标头部、分享官
- **管理后台**（`apps/admin`）— 运营/客服/财务/CEO 用：用户、订单、活动、分享官、风控、看板
- **顾问后台**（`apps/consultant`）— MAX 顾问用：客户档案、AI 报告复审、月度复盘、人设打磨
- **开放端**（`apps/open`）— 开发者文档站 + 加盟商后台
- **后端 API**（`services/api`）— FastAPI 主服务：鉴权、订阅、诊断、对标、档案、人设、商业定位、分享官、AI Agent 编排
- **19 篇战略文档**（`docs/01-战略/`）— 完整商业方案（总纲/竞品/技术/产品/用户旅程/路线图/商业模式/指标风险/人设定位/AI 进化/增长飞轮/四端对齐/API 全清单 + 数据采集 4 篇）

---

## 快速开始（本地一键启动）

### 前置依赖
- Node.js ≥ 20（推荐用 nvm/fnm）
- pnpm ≥ 9（`npm i -g pnpm`）
- Python ≥ 3.11（推荐 3.13）
- Docker Desktop

### 方式 A：纯本地（无 Docker，SQLite 模式）

```bash
# 1. 复制环境变量
cp .env.example .env.local
# 编辑 .env.local，填入你的 DEEPSEEK_API_KEY 等

# 2. 安装前端依赖
pnpm install

# 3. 启动后端（端口 8000，默认 SQLite）
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed.py      # 初始化产品目录 + 对标库样例
uvicorn app.main:app --reload --port 8000

# 4. 另开终端，启动 H5（端口 5173）
cd apps/h5 && pnpm dev

# 5. 浏览器打开 http://localhost:5173
```

### 方式 B：Docker Compose 一键全套

```bash
cp .env.example .env.docker
make docker-up   # postgres + redis + minio + 后端 API（端口 8000）

# 另开终端启动前端
pnpm install
make dev-h5      # H5（端口 5173）
```

启动后访问：
- H5 主页: http://localhost:5173
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/healthz
- MinIO 控制台: http://localhost:9001（minioadmin / minioadmin123）

### 常用命令

```bash
make help        # 查看所有可用命令
make lint        # 全仓 Lint（Ruff + ESLint）
make test        # 全仓测试（pytest + pnpm test）
make seed        # 初始化种子数据
make docker-up   # 启动 Docker 依赖
make docker-down # 停止 Docker 依赖
```

---

## 仓库结构

```
video-ct/
├── README.md / ARCHITECTURE.md / DEPLOY.md / CONTRIBUTING.md / CHANGELOG.md
├── .env.example                        # 环境变量示例
├── docker-compose.yml                  # 一键起依赖服务
├── Makefile                            # 常用命令封装
├── pnpm-workspace.yaml                 # pnpm 多包工作区
│
├── apps/                               # 前端展示层（按优先级）
│   ├── h5/                             #   ① 核心·C端H5（Vue3 + Vant）
│   ├── miniprogram/                    #   ② 微信小程序（预留·Q3）
│   ├── admin/                          #   ③ 运营管理后台（Vue3 + Ant Design Vue Pro）
│   ├── consultant/                     #   ④ 顾问后台（Vue3 + Ant Design Vue Pro）
│   └── open/                           #   ⑤ 开放端文档站（VitePress）
│
├── services/                           # 后端服务层
│   ├── api/                            #   主业务 API（FastAPI 单体）
│   │   └── app/services/fire_eye/      #   ↳ 数据采集六族子包（v3）
│   └── worker/                         #   Celery Worker（预留·v3启用）
│
├── packages/                           # 共享能力层
│   └── shared/src/
│       ├── types/                      #   ① 基础 TS 类型
│       ├── constants/                  #   ② 业务常量
│       ├── tokens/                     #   ③ 设计令牌
│       ├── validators/                 #   ④ 共享校验规则
│       ├── api-client/                 #   ⑤ 四端统一请求客户端
│       └── utils/                      #   ⑥ 工具函数
│
├── infra/                              # 基础设施层
│   ├── docker/                         #   各服务 Dockerfile
│   ├── k8s/                            #   K8s 配置（预留·M6启用）
│   ├── migrations/                     #   数据库初始化 SQL
│   └── monitoring/                     #   Prometheus + Grafana
│
├── tests/                              # 测试层（统一入口）
│   └── e2e/                            #   Playwright E2E（后端单测在 services/api/tests/）
│
├── scripts/                            # 运维脚本层（按职责）
│   ├── db/                             #   数据库·backup / restore
│   ├── data/                           #   采集·种子·对标刷新
│   └── deploy/                         #   部署·上线·回滚
│
├── docs/                               # 项目内部文档
│   ├── 01-战略/ ~ 08-交接/             #   8 大分类（共 ~65 篇）
│   └── 99-归档/                        #   退役文档区
│
└── .github/workflows/                  # GitHub Actions CI/CD
```

---

## 核心能力一图速览

| 模块 | 状态 | 文件位置 |
|---|---|---|
| 用户注册/登录（手机号 OTP + 微信） | ✅ MVP | `services/api/app/api/auth.py` |
| PRO/MAX 订阅 + 单次付费 | ✅ MVP | `services/api/app/api/subscription.py` |
| 视频 CT 诊断（6 维 18 点位） | ✅ MVP | `services/api/app/services/diagnosis.py` |
| 头部对标看板 | ✅ MVP | `services/api/app/api/benchmark.py` |
| 终身成长档案 | ✅ MVP | `services/api/app/api/archive.py` |
| 人设 IPP 诊断 | ✅ MVP | `services/api/app/api/persona.py` |
| 商业定位 BPS 扫描 | ✅ MVP | `services/api/app/api/positioning.py` |
| 品牌分享官（4 级 + 二级裂变） | ✅ MVP | `services/api/app/api/referrer.py` |
| AI Agent 编排（8 大 Agent） | ✅ MVP | `services/api/app/agents/` |
| 微信支付 | ⚠ Mock | `services/api/app/services/payment.py` |
| 抖音/快手数据采集 | ⚠ Mock | `services/api/app/services/crawler.py` |

> ✅ = 真实可运行；⚠ Mock = 接口结构完整，需要真实凭证后切真实实现

---

## 战略文档

完整 19 篇战略 → `docs/01-战略/`

| # | 主题 |
|---|---|
| 00 | 总览 README |
| 01 | 总纲（北极星指标、产品哲学、三年愿景） |
| 02 | 竞品与定位（6 大独家壁垒） |
| 03 | 技术架构 |
| 04 | 技能系统（12 项 AI 技能 + 顾问梯队） |
| 05 | 自动化与智能化 |
| 06 | 产品方案（PRO/MAX 完整权益清单） |
| 07 | 用户旅程 |
| 08 | 实施路线图（0–365 天） |
| 09 | 商业模式（LTV/CAC 算账 + 三大收入引擎） |
| 10 | 指标与风险 |
| 11 | 人设与商业定位（IPP + BPS 双引擎） |
| 12 | AI 智能进化引擎（8 大 Agent + 4 大飞轮） |
| 13 | 增长与运营飞轮（分享官 + 11 套组合拳） |
| 14 | 四端对齐与同步开发 |
| 15 | 技术栈与 API 全清单 |
| 16 | 数据采集模块化架构 |
| 17 | 采集层总体方案与实施路线 |
| 18 | 分析过程与产出规划 |
| 19 | 数据采集 → 智能分析 → 历史结合 |

---

## 技术栈一图

```
前端：Vue 3 + TypeScript + Vite + Pinia + Vant（C 端）/ Ant Design Vue Pro（B 端）
后端：Python 3.11+ + FastAPI + SQLAlchemy 2 + Alembic + Pydantic v2
任务：Celery + Redis（异步）+ APScheduler（定时）
数据：PostgreSQL（业务）+ ClickHouse（分析）+ Redis（缓存）+ Milvus（向量）
AI：  DeepSeek + 硅基流动（多模型路由）+ LangGraph（Agent 编排）
存储：阿里云 OSS（生产）+ 本地磁盘（开发）
部署：Docker + Docker Compose（开发）→ Kubernetes（M6+ 生产）
```

详见 `docs/01-战略/15-技术栈与API全清单.md`

---

## 贡献指南

见 `CONTRIBUTING.md`

## 5 窗口开发计划

| 窗口 | 主题 | 状态 |
|------|------|------|
| 窗口 1 | 项目骨架初始化（Monorepo + API + H5 + Admin + Consultant + Docs） | Done |
| 窗口 2 | 核心业务 API（鉴权/订阅/诊断/对标/档案/人设/定位/分享官/AI Agent） | Done |
| 窗口 3 | 前端页面开发（H5 16 路由 + Admin + Consultant + Docs） | Done |
| 窗口 4 | Docker 化 + CI/CD + 环境完整性 | Done |
| 窗口 5 | 端到端测试 + CI 强化 + Pre-commit 闸门 | Done |

### 窗口 5 交付物
- `tests/e2e/` — Playwright E2E 测试骨架（H5 关键路径 + API 健康检查）
- `.github/workflows/ci.yml` — 新增 test-backend / test-e2e job
- `.husky/pre-commit` — lint-staged 闸门（检查暂存 .ts/.vue）
- `package.json` — lint-staged 配置 + `test:e2e` 脚本
- `docker-compose.yml` — 全部服务含 healthcheck

### 运行测试

```bash
# 后端单元测试
cd services/api && pip install -r requirements.txt && pytest tests/ -v

# E2E 测试（需要后端 + H5 已启动）
pnpm test:e2e                    # 或: npx playwright test --config tests/e2e/playwright.config.ts

# 仅 API 健康检查
npx playwright test --config tests/e2e/playwright.config.ts api-health

# 仅 H5 关键路径
npx playwright test --config tests/e2e/playwright.config.ts h5-critical-path

# 查看 E2E 报告
npx playwright show-report playwright-report/
```

## 许可证

MIT — 见 `LICENSE`

## 联系

- 问题反馈：GitHub Issues
- 商务合作：见战略文档 09 章
