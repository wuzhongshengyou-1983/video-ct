# 分享官 API

视频 CT 内置的裂变增长体系。用户通过分享专属链接邀请新用户，获得现金奖励和等级提升。

## 端点列表

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/api/v1/referrers/me` | JWT | 我的分享官信息 |
| `GET` | `/api/v1/referrers/link` | JWT | 获取分享链接/海报 |
| `GET` | `/api/v1/referrers/records` | JWT | 分享记录列表 |
| `POST` | `/api/v1/referrers/withdraw` | JWT+HMAC | 提现申请 |
| `GET` | `/api/v1/referrers/leaderboard` | 无 | 本月分享榜 |

---

## 分享官等级体系

| 等级 | 图标 | 所需有效推荐数 | 奖励加成 |
|---|---|---|---|
| 铜牌 | 🥉 | 0 | 基础奖励（¥20/人） |
| 银牌 | 🥈 | 11 | 基础奖励 + 5% 额外加成 |
| 金牌 | 🥇 | 31 | 基础奖励 + 10% 额外加成 |
| 钻石 | 💎 | 101 | 基础奖励 + 20% 额外加成 + 专属扶持 |

### 奖励类型

| 类型 | 说明 |
|---|---|
| **现金奖励** | 被推荐人首次付费时，推荐人获得 ¥20 现金奖励 |
| **余额奖励** | 被推荐人每次消费的 15% 以抵扣金的形式进入推荐人账户 |
| **票券奖励** | 达到更高等级时获得免费诊断券 |

---

## 我的分享官信息

```
GET /api/v1/referrers/me
```

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "link_code": "ABCD1234",
    "level": "🥈 银牌",
    "total_valid_referrals": 15,
    "total_rewards_cny": 32000,
    "cash_balance_cny": 20000,
    "deduction_balance_cny": 12000,
    "ticket_balance": 3,
    "next_level_at": 16,
    "next_level_name": "🥇 金牌"
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `link_code` | `string` | 你的专属推荐码（在注册时自动生成） |
| `level` | `string` | 当前等级（含图标） |
| `total_valid_referrals` | `int` | 累计有效推荐数（被推荐人完成首次付费） |
| `total_rewards_cny` | `int` | 累计获得奖励（分） |
| `cash_balance_cny` | `int` | 可提现余额（分） |
| `deduction_balance_cny` | `int` | 抵扣金余额（分）— 可用于购买订阅时抵扣 |
| `ticket_balance` | `int` | 免费诊断券数量 |
| `next_level_at` | `int` | 距离下一等级还需多少有效推荐 |
| `next_level_name` | `string \| null` | 下一等级名称（已达最高为 null） |

---

## 获取分享链接

```
GET /api/v1/referrers/link
```

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "link_code": "ABCD1234",
    "h5_url": "https://video-ct.cn/invite?ref=ABCD1234",
    "qr_code_url": "https://api.qrserver.com/v1/create-qr-code/?data=https://video-ct.cn/invite?ref=ABCD1234",
    "poster_url": "https://api.video-ct.cn/api/v1/referrers/poster.png?code=ABCD1234"
  }
}
```

| 字段 | 说明 |
|---|---|
| `h5_url` | H5 邀请落地页链接 |
| `qr_code_url` | 二维码图片 URL（自动生成） |
| `poster_url` | 邀请海报图片 URL |

### 使用方式

1. 复制 `h5_url` 分享到朋友圈/微信群/私信
2. 保存 `qr_code_url` 图片用于线下推广物料
3. 使用 `poster_url` 作为社交分享卡片图

---

## 分享记录

```
GET /api/v1/referrers/records
```

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "invitee_nickname": "美食爱好者小王",
      "source": "wechat_share",
      "first_paid_at": "2026-05-18T14:30:00Z",
      "reward_amount_cny": 2000,
      "reward_status": "settled",
      "created_at": "2026-05-18T10:00:00Z"
    }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `source` | 来源渠道（`wechat_share` / `qrcode` / `link` 等） |
| `reward_status` | 奖励状态：`pending`（待结算）/ `settled`（已到账） |

---

## 提现申请

```
POST /api/v1/referrers/withdraw
```

::: warning 前置条件
- 必须完成实名认证
- 每次提现金额 >= ¥100（10000 分）
- 需要 HMAC 签名（安全考虑）
:::

### 请求体

```json
{
  "amount_cny": 10000
}
```

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "ok": true,
    "remaining_cny": 10000
  }
}
```

### 错误码

| code | HTTP | 说明 |
|---|---|---|
| `REALNAME_REQUIRED` | 403 | 需要先完成实名认证 |
| `MIN_WITHDRAW` | 400 | 起提金额 100 元 |
| `INSUFFICIENT` | 400 | 余额不足 |

---

## 本月分享榜

```
GET /api/v1/referrers/leaderboard?limit=30
```

无需鉴权。获取本月影响力最大的分享官排行。

### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `limit` | `int` | `30` | 返回上榜人数 |

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "rank": 1,
      "nickname": "美食博主老张",
      "avatar_url": "https://cdn.video-ct.cn/avatars/user_1.jpg",
      "level": "💎 钻石",
      "monthly_referrals": 35,
      "monthly_rewards_cny": 70000
    }
  ]
}
```
