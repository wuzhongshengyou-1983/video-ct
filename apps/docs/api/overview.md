# API 概览

## 基础信息

| 项目 | 值 |
|---|---|
| **基础 URL** | `https://api.video-ct.cn` |
| **API 前缀** | `/api/v1` |
| **数据格式** | JSON（请求和响应均为 `application/json`） |
| **字符编码** | UTF-8 |
| **时间格式** | ISO-8601（`2026-05-20T10:30:00Z`） |

## 通用响应格式

所有 API 响应均遵循统一的 `ApiResponse<T>` 包裹格式：

```json
{
  "code": "OK",
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | `string` | 状态码。`OK` 表示成功，其他值表示异常 |
| `message` | `string` | 人类可读的状态描述 |
| `data` | `T \| null` | 业务数据。异常时可能为 `null` |

错误响应：

```json
{
  "code": "ERROR_CODE",
  "message": "人类可读的错误描述",
  "trace_id": "abc123...",
  "details": {}
}
```

## 端点分类

### 鉴权 (Auth) — `/api/v1/auth`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `POST` | `/auth/otp/send` | 无 | 发送手机验证码 |
| `POST` | `/auth/otp/verify` | 无 | 验证码登录/注册 |
| `POST` | `/auth/wechat/login` | 无 | 微信登录 |
| `GET` | `/auth/me` | JWT | 获取当前用户完整信息 |

### 用户 (Users) — `/api/v1/users`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `PUT` | `/users/me/profile` | JWT | 更新个人资料 |

### 诊断 (Diagnosis) — `/api/v1/diagnoses`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `POST` | `/diagnoses/submit` | JWT | 提交视频诊断任务 |
| `GET` | `/diagnoses` | JWT | 诊断历史列表 |
| `GET` | `/diagnoses/{id}` | JWT | 诊断详情 |
| `GET` | `/diagnoses/{id}/report` | JWT | 诊断报告 |
| `POST` | `/diagnoses/{id}/report/feedback` | JWT | 报告反馈评分 |

### 对标 (Benchmark) — `/api/v1/benchmarks`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/benchmarks/tracks` | JWT/API Key | 所有对标赛道 |
| `GET` | `/benchmarks/top10/{track}` | JWT/API Key | 赛道 Top 10 博主 |
| `POST` | `/benchmarks/gap` | JWT | 计算对标差距 |

### 成长档案 (Archive) — `/api/v1/archives`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/archives/me` | JWT | 我的档案 |
| `GET` | `/archives/me/curve` | JWT | 成长曲线 |

### 人设 (Persona) — `/api/v1/personas`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `POST` | `/personas/scan` | JWT | 人设扫描 |
| `GET` | `/personas/me` | JWT | 我的人设档案 |
| `GET` | `/personas/archetypes` | 无 | 所有人设原型列表 |

### 商业定位 (Positioning) — `/api/v1/positionings`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `POST` | `/positionings/scan` | JWT | 商业定位扫描 |
| `GET` | `/positionings/me` | JWT | 我的定位档案 |

### 分享官 (Referrer) — `/api/v1/referrers`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/referrers/me` | JWT | 我的分享官信息 |
| `GET` | `/referrers/link` | JWT | 获取分享链接 |
| `GET` | `/referrers/records` | JWT | 分享记录列表 |
| `POST` | `/referrers/withdraw` | JWT+HMAC | 提现申请 |
| `GET` | `/referrers/leaderboard` | 无 | 本月分享榜 |

### 订阅 (Subscription) — `/api/v1/subscriptions`

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/subscriptions/products` | 无 | 产品列表 |
| `POST` | `/subscriptions/orders` | JWT | 创建订单 |
| `POST` | `/subscriptions/orders/{order_no}/mock-pay` | JWT | 模拟支付（仅开发） |
| `GET` | `/subscriptions/my` | JWT | 我的订阅 |
| `GET` | `/subscriptions/orders` | JWT | 我的订单 |

### AI (AI) — `/api/v1/ai`

Agent 级别的 AI 能力接口（内容生成、智能问答等），详情见后端代码注释。

### 管理 (Admin) — `/api/v1/admin`

管理员接口（用户管理、数据看板、审计日志等），仅限 `admin` 角色访问。

### Webhook — `/api/v1/webhooks`

支付回调、事件通知等 Webhook 端点。

## 分页

需要列表的端点支持以下分页参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `page` | `int` | `1` | 页码（从 1 开始） |
| `size` | `int` | `20` | 每页条数 |

分页响应格式：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "items": [...],
    "total": 156,
    "page": 1,
    "size": 20
  }
}
```

## 限流

| 等级 | 频率限制 |
|---|---|
| 免费用户 | 30 次/分钟 |
| Pro 用户 | 100 次/分钟 |
| Max 用户 | 1000 次/分钟 |
| API Key | 按关联用户的等级 |

超限返回 HTTP 429 + `RATE_LIMITED` 错误码。

## OpenAPI 规范文件

完整的 OpenAPI 3.0 规范文件（YAML 格式）可在 [`/api-spec.yaml`](/api-spec.yaml) 下载，
可直接导入 Postman、Swagger UI 等工具使用。
