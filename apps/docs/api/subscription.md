# 订阅 API

管理用户订阅、产品浏览、订单创建和支付。

## 端点列表

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `GET` | `/api/v1/subscriptions/products` | 无 | 产品列表 |
| `POST` | `/api/v1/subscriptions/orders` | JWT | 创建订单 |
| `POST` | `/api/v1/subscriptions/orders/{order_no}/mock-pay` | JWT | 模拟支付（仅开发） |
| `GET` | `/api/v1/subscriptions/my` | JWT | 我的订阅 |
| `GET` | `/api/v1/subscriptions/orders` | JWT | 我的订单 |

---

## 产品列表

```
GET /api/v1/subscriptions/products
```

获取所有可购买的产品（订阅 + 单次诊断）。

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "sku": "pro_monthly",
      "name": "Pro 月卡",
      "tier": "pro",
      "billing_cycle": "monthly",
      "price_cny": 9900,
      "description": "每月20次诊断 + 对标查询 + 人设扫描",
      "features": [
        "每月 20 次诊断",
        "全维度对标查询",
        "人设扫描",
        "商业定位分析",
        "PDF 报告导出"
      ]
    },
    {
      "sku": "max_monthly",
      "name": "Max 月卡",
      "tier": "max",
      "billing_cycle": "monthly",
      "price_cny": 49900,
      "description": "无限诊断 + 全功能开放 + 顾问陪跑",
      "features": [
        "每月 100 次诊断",
        "全功能无限制",
        "顾问人工复核",
        "专属陪跑服务",
        "优先技术支持"
      ]
    },
    {
      "sku": "ct_basic",
      "name": "单次 CT 诊断",
      "tier": "free",
      "billing_cycle": "once",
      "price_cny": 1900,
      "description": "单次基础 CT 诊断",
      "features": [
        "6 维诊断",
        "基准评分",
        "文字报告"
      ]
    }
  ]
}
```

::: tip 价格单位
所有 `price_cny` 字段单位为**分**（1 元 = 100 分）。
前端显示时使用 `formatCny()` 函数转换，例如 `9900` 分 = `¥99.00`。
:::

### 产品 SKU 说明

| SKU | 名称 | 价格（元） | 计费周期 |
|---|---|---|---|
| `pro_monthly` | Pro 月卡 | ¥99 | 月度 |
| `pro_quarterly` | Pro 季卡 | ¥249 | 季度 |
| `pro_yearly` | Pro 年卡 | ¥899 | 年度 |
| `max_monthly` | Max 月卡 | ¥499 | 月度 |
| `max_quarterly` | Max 季卡 | ¥1,199 | 季度 |
| `max_yearly` | Max 年卡 | ¥4,499 | 年度 |
| `ct_basic` | 单次 CT 诊断 | ¥19 | 一次性 |
| `ct_full` | 单次全维度诊断 | ¥49 | 一次性 |

---

## 创建订单

```
POST /api/v1/subscriptions/orders
```

### 请求体

```json
{
  "sku": "pro_monthly",
  "coupon_code": "WELCOME20",
  "use_deduction": false,
  "referrer_code": "ABCD1234"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `sku` | `string` | 是 | 产品 SKU（如 `pro_monthly`） |
| `coupon_code` | `string` | 否 | 优惠券码 |
| `use_deduction` | `bool` | 否 | 是否使用余额抵扣，默认 `false` |
| `referrer_code` | `string` | 否 | 分享官推荐码 |

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "order_no": "VCT20260520103000001",
    "sku": "pro_monthly",
    "total_cny": 9900,
    "deduction_cny": 0,
    "paid_cny": 9900,
    "payment_status": "pending",
    "pay_url": "weixin://wxpay/bizpayurl?pr=xxxxx",
    "created_at": "2026-05-20T10:30:00Z"
  }
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `total_cny` | `int` | 订单总额（分） |
| `deduction_cny` | `int` | 余额抵扣金额（分） |
| `paid_cny` | `int` | 实付金额（分） = total - deduction |
| `payment_status` | `string` | `pending` / `paid` / `cancelled` / `refunded` |
| `pay_url` | `string \| null` | 微信支付链接（二维码/调起支付） |

---

## 模拟支付

```
POST /api/v1/subscriptions/orders/{order_no}/mock-pay
```

::: danger 仅开发模式
此端点仅存在于开发环境中，生产环境将被移除。
用于模拟完成支付以测试订阅流程。
:::

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "ok": true,
    "order_no": "VCT20260520103000001"
  }
}
```

---

## 我的订阅

```
GET /api/v1/subscriptions/my
```

获取当前用户的有效订阅。

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "sku": "pro_monthly",
    "tier": "pro",
    "status": "active",
    "started_at": "2026-05-20T10:30:00Z",
    "expires_at": "2026-06-20T10:30:00Z",
    "auto_renew": false
  }
}
```

如无有效订阅，`data` 为 `null`。

| 字段 | 说明 |
|---|---|
| `status` | `active` / `expired` / `cancelled` |
| `auto_renew` | 是否自动续费 |

---

## 我的订单

```
GET /api/v1/subscriptions/orders
```

获取当前用户的历史订单（最近 50 条）。

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "id": 1,
      "order_no": "VCT20260520103000001",
      "sku": "pro_monthly",
      "total_cny": 9900,
      "deduction_cny": 0,
      "paid_cny": 9900,
      "payment_status": "paid",
      "pay_url": null,
      "created_at": "2026-05-20T10:30:00Z"
    }
  ]
}
```
