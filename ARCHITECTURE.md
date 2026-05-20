# 系统架构

> 一张图看清四端 + 后端 + AI + 数据流

---

## 1. 全局架构图

```
┌──────────────────────────────────────────────────────────────────────┐
│  四个端                                                                │
├──────────────────────┬───────────────────────────────────────────────┤
│ ① C 端 H5            │ ② 顾问端        │ ③ 运营端     │ ④ 开放端      │
│ apps/h5              │ apps/consultant │ apps/admin   │ apps/docs    │
│ Vue3+Vant            │ Vue3+Antd Pro   │ Vue3+Antd Pro│ VitePress    │
└──────────┬───────────┴────────┬────────┴──────┬───────┴──────┬───────┘
           │                    │               │              │
           └────────────────────┴───────────────┴──────────────┘
                                  │ HTTPS / WSS
                                  ▼
                  ┌───────────────────────────────────────┐
                  │  API 网关（Nginx + FastAPI 路由层）    │
                  │  · 限流 · 鉴权 · 计费 · 跨域           │
                  └───────────────┬───────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  业务服务层（services/api · FastAPI 单体，未来可拆微服务）            │
│                                                                       │
│  routers:                                                             │
│   auth  subscription  diagnosis  benchmark  archive                   │
│   persona  positioning  referrer  task  coupon  event                 │
│   ai  admin  consultant  webhook                                      │
│                                                                       │
│  agents:                                                              │
│   ① CT 诊断官  ② 对标分析师  ③ 人设观察员  ④ 商业策略师               │
│   ⑤ 内容生成手 ⑥ 数据预警员  ⑦ 顾问助理   ⑧ 客户成功管家               │
│                                                                       │
│  services:                                                            │
│   llm_router  embedding  ocr_asr  payment  notification               │
│   crawler  report_renderer  pdf_export  storage                       │
└──────────────────┬──────────────────────────┬───────────────────────┘
                   │                          │
                   ▼                          ▼
       ┌────────────────────┐      ┌────────────────────────┐
       │  数据层             │      │  AI 模型层              │
       │  PostgreSQL（业务） │      │  DeepSeek API           │
       │  Redis（缓存+任务） │      │  硅基流动 API（Qwen/    │
       │  SQLite（开发兜底） │      │   Embedding/Vision）    │
       │  Milvus（向量，可选）│      │  LangGraph（编排）      │
       │  对象存储（视频/PDF）│      │                         │
       └────────────────────┘      └────────────────────────┘
```

## 2. 关键数据流：一次完整诊断

```
H5 用户提交视频链接
   ▼ POST /api/v1/diagnosis/submit
api/diagnosis 路由
   ▼ 入队 + 写 DB
crawler.fetch_video_meta()        ← 拉取视频元数据
   ▼
ocr_asr.extract()                  ← OCR 标题/字幕 + ASR 语音转写
   ▼
agents.ct_radiologist.run()        ← 6 维 18 点位 CT 诊断
   ├─ llm_router → DeepSeek/Qwen
   └─ 生成 JSON 报告
report_renderer.render()           ← Jinja2 模板 → HTML
   ▼ + pdf_export
保存 PDF/HTML 到 storage
   ▼
更新档案 + 触发事件
   ▼ WebSocket
H5 推送"诊断完成"通知 + 展示报告
```

## 3. 鉴权流

- 用户：JWT (HS256, 7 天) · refresh token 30 天
- 顾问/运营：JWT + RBAC（基于 role + scopes）
- 开放端：API Key（HMAC-SHA256 签名）

## 4. 数据库实体（核心表）

详见 `services/api/app/models/` 和 `infra/migrations/`

```
users                  用户主表
user_profiles          扩展信息
subscriptions          订阅
orders                 订单
diagnoses              诊断任务
reports                报告
benchmarks             头部对标库
benchmark_snapshots    每日差距快照
archives               成长档案
archive_snapshots      档案月度快照
personas               人设档案
positionings           商业定位档案
referrer_links         分享归因
referrer_levels        分享官等级
reward_accounts        奖励账户
tasks                  任务系统
coupons                优惠券
events                 活动
audit_logs             审计日志
```

## 5. 部署形态

| 阶段 | 部署 |
|---|---|
| 开发 | 本机 Python venv + pnpm + SQLite（零依赖） |
| 联调 | Docker Compose（PG/Redis/Milvus） |
| 测试 | 单台 ECS（4c8g）+ RDS PostgreSQL |
| 生产 MVP | 2 台 ECS + RDS + OSS |
| 生产规模化 | K8s 集群（详见 `docs/strategy/15_技术栈与API全清单.md`）|
