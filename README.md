# 视频 CT · Video CT

> **像影像科医生一样诊断短视频** —— AI 月度体检 + 头部对标 + 终身成长档案 + 顾问陪跑

PRO 99/月 · MAX 499/月 · 每月免费 3 次扫描 · 单次 19 元

---

## 这是什么

`video-ct` 是一个完整的 SaaS + 陪跑业务的代码实现，包含：

- **C 端 H5**（`apps/h5`）— 普通博主自助：注册、付费、提交视频、看 CT 报告、对标头部、分享官
- **管理后台**（`apps/admin`）— 运营/客服/财务/CEO 用：用户、订单、活动、分享官、风控、看板
- **顾问后台**（`apps/consultant`）— MAX 顾问用：客户档案、AI 报告复审、月度复盘、人设打磨
- **开放端**（`apps/docs`）— 开发者文档站 + 加盟商后台
- **后端 API**（`services/api`）— FastAPI 主服务：鉴权、订阅、诊断、对标、档案、人设、商业定位、分享官、AI Agent 编排
- **15 章战略文档**（`docs/strategy/`）— 完整商业方案（总纲/竞品/技术/产品/用户旅程/路线图/商业模式/指标风险/人设定位/AI 进化/增长飞轮/四端对齐/API 全清单）

---

## 快速开始（本地一键启动）

### 前置依赖
- Node.js ≥ 20（推荐用 nvm/fnm）
- pnpm ≥ 9（`npm i -g pnpm`）
- Python ≥ 3.11（推荐 3.13）
- Docker Desktop（可选，用于 PG/Redis/Kafka；不装也能用 SQLite 跑通）

### 30 秒拉起

```bash
# 1. 复制环境变量
cp .env.example .env.local
# 编辑 .env.local，填入你的 DEEPSEEK_API_KEY 等

# 2. 安装前端依赖
pnpm install

# 3. 启动后端（端口 8000）
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head        # 跑数据库迁移
python scripts/seed.py      # 初始化基础数据
uvicorn app.main:app --reload --port 8000

# 4. 另开终端，启动 H5（端口 5173）
cd apps/h5 && pnpm dev

# 5. 浏览器打开 http://localhost:5173
```

### Docker Compose 一键起全套（可选）

```bash
docker-compose up -d   # postgres + redis + kafka + minio + milvus
make dev               # 启动后端 + 4 端前端
```

---

## 仓库结构

```
video-ct/
├── README.md / ARCHITECTURE.md / DEPLOY.md / CONTRIBUTING.md
├── .env.example                  # 环境变量示例
├── docker-compose.yml            # 一键起依赖服务
├── Makefile                      # 常用命令封装
├── pnpm-workspace.yaml           # pnpm 多包工作区
├── apps/
│   ├── h5/                       # ① C 端 H5（Vue3 + Vant）
│   ├── admin/                    # ③ 运营管理后台（Vue3 + Ant Design Vue Pro）
│   ├── consultant/               # ② 顾问后台（Vue3 + Ant Design Vue Pro）
│   └── docs/                     # ④ 开发者文档站（VitePress）
├── services/
│   └── api/                      # FastAPI 单体（含全部业务路由 + AI Agent）
├── packages/
│   └── shared/                   # 跨端共享：TS 类型、设计令牌、API 客户端
├── infra/
│   ├── docker/                   # 各服务 Dockerfile
│   └── migrations/               # Alembic 数据库迁移
├── docs/
│   ├── strategy/                 # 15 章战略文档
│   ├── api/                      # API 接口文档
│   └── deploy/                   # 部署/运维
├── scripts/                      # 数据 seed、压测、迁移脚本
└── .github/workflows/            # GitHub Actions CI/CD
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

完整 15 章战略 → `docs/strategy/`

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

详见 `docs/strategy/15_技术栈与API全清单.md`

---

## 贡献指南

见 `CONTRIBUTING.md`

## 许可证

MIT — 见 `LICENSE`

## 联系

- 问题反馈：GitHub Issues
- 商务合作：见战略文档 09 章
