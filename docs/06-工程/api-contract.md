# API 合约 · 内部端点对照表

> 面向前端联调 · 更新于 2026-05-28  
> 外部 OpenAPI 规范：`apps/open/public/api-spec.yaml`  
> 全部端点前缀：`/api/v1/`（ws 为 `/ws/`）

---

## 鉴权说明

- **登录态**：`Authorization: Bearer <jwt_token>` (7 天有效，refresh 30 天)
- **管理员/顾问**：额外校验 `role` scope
- **无需登录**：`/auth/*`、`/subscriptions/products`、`/healthz`

---

## 鉴权 · auth

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| POST | `/auth/otp/send` | 发送手机验证码（阿里云短信） | ❌ |
| POST | `/auth/otp/verify` | 验证 OTP → 返回 JWT | ❌ |
| POST | `/auth/wechat/login` | 微信小程序登录 | ❌ |
| GET | `/auth/wechat/callback` | 微信网页授权回调 | ❌ |
| GET | `/auth/me` | 获取当前用户信息 | ✅ |

---

## 用户 · users

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| PUT | `/users/me/profile` | 修改昵称 / 头像等 | ✅ |
| POST | `/users/avatar` | 上传头像（multipart） | ✅ |

---

## 订阅与支付 · subscriptions

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| GET | `/subscriptions/products` | 产品列表（PRO/MAX/单次） | ❌ |
| POST | `/subscriptions/orders` | 创建订单 → 返回支付参数 | ✅ |
| GET | `/subscriptions/my` | 当前有效订阅 | ✅ |
| GET | `/subscriptions/orders` | 订单历史 | ✅ |
| GET | `/subscriptions/orders/{order_no}/pay-params` | 微信支付参数 | ✅ |
| GET | `/subscriptions/orders/{order_no}/status` | 订单状态查询 | ✅ |
| POST | `/subscriptions/orders/{order_no}/mock-pay` | 本地测试 Mock 支付 | ✅ |
| POST | `/subscriptions/cancel` | 取消续费 | ✅ |

---

## 诊断 · diagnosis

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| POST | `/diagnosis/submit` | 提交视频 URL → 触发诊断任务 | ✅ |
| GET | `/diagnosis/` | 诊断历史列表 | ✅ |
| GET | `/diagnosis/{id}` | 单条诊断详情 | ✅ |
| GET | `/diagnosis/{id}/report` | CT 报告（JSON） | ✅ |
| POST | `/diagnosis/{id}/report/feedback` | 报告反馈（已废弃，改用 events/track） | ✅ |
| POST | `/diagnosis/{id}/resubmit` | 复诊（复用上次视频 URL） | ✅ |

> WebSocket 实时进度：`/ws/diagnosis/{id}` — 诊断运行时推送进度事件

---

## 对标 · benchmark

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| GET | `/benchmark/tracks` | 可选赛道列表 | ✅ |
| GET | `/benchmark/top10/{track}` | 赛道 Top10 头部博主 | ✅ |
| POST | `/benchmark/gap` | 计算用户与头部差距 | ✅ |

---

## 成长档案 · archive

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| GET | `/archive/me` | 用户档案（含月度快照列表） | ✅ |
| GET | `/archive/me/curve` | 成长曲线数据（用于折线图） | ✅ |

---

## 人设 · persona

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| POST | `/persona/scan` | 触发 IPP 人设诊断 | ✅ |
| GET | `/persona/me` | 当前人设档案 | ✅ |
| GET | `/persona/archetypes` | 人设原型参考库 | ✅ |

---

## 商业定位 · positioning

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| POST | `/positioning/scan` | 触发 BPS 商业定位扫描 | ✅ |
| GET | `/positioning/me` | 当前商业定位档案 | ✅ |

---

## 分享官 · referrer

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| GET | `/referrer/me` | 当前分享官信息 + 等级 | ✅ |
| GET | `/referrer/link` | 获取专属分享链接 | ✅ |
| GET | `/referrer/records` | 分享收益记录 | ✅ |
| POST | `/referrer/withdraw` | 申请提现 | ✅ |
| GET | `/referrer/leaderboard` | 分享官排行榜 | ✅ |

---

## AI 能力 · ai

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| POST | `/ai/content/generate` | 生成钩子/标题/封面文案 | ✅ |
| GET | `/ai/agents` | 已注册 Agent 列表 | ✅ Admin |

---

## 行为事件 · events

| 方法 | 路径 | 说明 | Body 关键字段 |
|------|------|------|--------------|
| POST | `/events/track` | 统一行为事件收集 | `event_type`, `diagnosis_id`(可选), `suggestion_id`(可选), `payload` |

**event_type 枚举**：`suggestion_feedback` / `report-view` / `module-dwell` / `suggestion-copy`

---

## 分析 · analytics

| 方法 | 路径 | 说明 | 登录要求 |
|------|------|------|---------|
| POST | `/analytics/events` | 前端埋点上报（批量） | ✅ |

---

## 微信 · wechat

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/wechat/js-sdk-sign` | JS-SDK 签名（H5 分享用） |
| GET | `/wechat/oauth-url` | 获取微信网页授权 URL |

---

## Webhook · webhook

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/webhooks/wechat/pay` | 微信支付回调（幂等处理） |

---

## 管理后台 · admin（需 admin role）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/dashboard` | 运营看板数据 |
| GET | `/admin/users` | 用户列表 |
| GET | `/admin/orders` | 订单列表 |
| GET | `/admin/diagnoses` | 诊断任务列表 |

---

## WebSocket

| 路径 | 说明 |
|------|------|
| `/ws/diagnosis/{id}` | 诊断实时进度推送（pending → running → done/failed） |

---

## 健康检查

| 路径 | 说明 |
|------|------|
| `GET /healthz` | 存活检查（无依赖，始终 200） |
| `GET /readyz` | 就绪检查（含 DB / Redis 连通性） |
| `GET /metrics` | Prometheus 指标端点 |
