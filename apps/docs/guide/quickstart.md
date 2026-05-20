# 快速开始

本指南将帮助你在 5 分钟内完成首次 API 调用并获取你的第一份视频诊断报告。

## 前置条件

- 一个有效的手机号（用于接收验证码）
- 一个短视频链接（支持抖音、快手、B站、小红书、视频号）
- 基本的 HTTP 请求工具（curl / Postman / 任意编程语言均可）

## 第一步：注册并登录

### 1.1 发送验证码

```bash
curl -X POST "https://api.video-ct.cn/api/v1/auth/otp/send" \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'
```

响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "sent": true,
    "dev_code": "123456"
  }
}
```

::: tip 开发模式
开发环境 `/api/v1/auth/otp/send` 的响应中会包含 `dev_code` 字段，
你可以直接使用该验证码，无需等待短信到达。
生产环境该字段会被移除。
:::

### 1.2 验证码登录

```bash
curl -X POST "https://api.video-ct.cn/api/v1/auth/otp/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "13800138000",
    "code": "123456"
  }'
```

响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_id": 1,
    "nickname": "新用户",
    "role": "user",
    "is_new_user": true
  }
}
```

**保存 `access_token`**，后续请求都需要携带它。

::: warning 分享官推荐码
如果你是通过其他用户的分享链接注册的，可以在 `verify` 请求中带上 `referrer_code` 参数。
:::

## 第二步：完善博主信息

```bash
curl -X PUT "https://api.video-ct.cn/api/v1/users/me/profile" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "track": "美食",
    "platform_main": "抖音",
    "follower_count": 50000,
    "bio": "热爱美食的90后，分享每一餐的温暖"
  }'
```

## 第三步：提交第一个视频诊断

```bash
curl -X POST "https://api.video-ct.cn/api/v1/diagnoses/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "video_url": "https://v.douyin.com/xxxxx/",
    "diagnosis_type": "ct_basic",
    "track": "美食"
  }'
```

响应：

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "video_url": "https://v.douyin.com/xxxxx/",
    "video_platform": "douyin",
    "status": "pending",
    "diagnosis_type": "ct_basic",
    "progress_pct": 0,
    "created_at": "2026-05-20T10:30:00Z",
    "completed_at": null
  }
}
```

## 第四步：查看诊断报告

诊断完成后，通过诊断 ID 获取报告：

```bash
curl "https://api.video-ct.cn/api/v1/diagnoses/1/report" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

报告中包含：

| 字段 | 说明 |
|---|---|
| `overall_score` | 综合评分（0-100） |
| `grade` | 评级（S/A/B/C/D） |
| `dimensions` | 六维逐项诊断（含评分/优点/发现/建议） |
| `findings` | 时间轴定位的具体问题点 |
| `benchmark_gap` | 与赛道头部的差距量化 |

## 第五步：查看对标差距

```bash
curl "https://api.video-ct.cn/api/v1/benchmarks/top10/美食" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

你会获得同赛道 Top 10 博主的公开数据，帮助你定位自己的差距和提升空间。

## 下一步

- [鉴权说明](/guide/authentication) — JWT、API Key、HMAC 签名的完整说明
- [诊断 API](/api/diagnosis) — 所有诊断相关端点详解
- [SDK 指南](/sdk/js) — 使用 JS/Python SDK 快速集成
