# 鉴权说明

视频 CT API 同时支持三种鉴权方式，适用于不同的使用场景。

## 鉴权方式概览

| 方式 | 适用场景 | 获取方式 |
|---|---|---|
| **JWT** | C 端用户 / H5 应用 | 手机验证码登录后获取 |
| **API Key** | 开放端开发者 / 第三方集成 | 开发者中心手动生成 |
| **HMAC 签名** | 服务端到服务端调用 | 使用 API Secret 签名（高级安全场景） |

---

## 方式一：JWT（用户端）

### 获取 Token

通过手机号验证码登录获取：

```
POST /api/v1/auth/otp/verify
```

响应中包含 `access_token`，有效期 7 天。

### 使用 Token

在所有需要鉴权的请求中携带 `Authorization` 头：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Token 结构

```json
{
  "sub": "1",
  "exp": 1716299999,
  "iat": 1715695200,
  "iss": "视频 CT API",
  "role": "user"
}
```

| 字段 | 说明 |
|---|---|
| `sub` | 用户 ID（字符串格式） |
| `exp` | 过期时间（Unix timestamp） |
| `iat` | 签发时间 |
| `iss` | 签发者 |
| `role` | 用户角色（user / consultant / admin） |

### Token 刷新

目前 JWT 有效期为 7 天。过期后需要重新登录获取新 Token。
（Refresh Token 功能已在路线图中，预计 Q3 上线。）

---

## 方式二：API Key（开放端）

### 生成 API Key

1. 登录 [视频 CT](https://video-ct.cn)
2. 进入「开发者中心」
3. 点击「生成 API Key」
4. 保存生成的 Key（仅显示一次）

### 使用 API Key

在请求头中携带：

```http
X-API-Key: vct_sk_xxxxxxxxxxxxxxxxxxxx
```

API Key 适用于开放端端点，具体端点的鉴权要求见 [API 概览](/api/overview)。

::: warning API Key 限制
- API Key 有调用频率限制（Pro: 100/min, Max: 1000/min）
- API Key 不能用于用户端端点（如提交诊断、查看我的报告）
- 每个账号最多生成 5 个 API Key
:::

### API Key 权限范围

| 端点分类 | JWT | API Key |
|---|---|---|
| 用户个人信息 | 可访问 | 不可访问 |
| 诊断提交/查看 | 可访问 | 不可访问 |
| 订阅/支付 | 可访问 | 不可访问 |
| 对标 Top10 查询 | 可访问 | 可访问 |
| 公开数据查询 | 可访问 | 可访问 |

---

## 方式三：HMAC 签名（服务端到服务端）

适用于银行级安全要求的场景（大额交易、自动提现等）。

### 签名算法

```python
import hmac
import hashlib
import time

def sign_request(method: str, path: str, body: str, secret: str) -> dict:
    timestamp = str(int(time.time()))
    message = f"{method}\n{path}\n{timestamp}\n{body}"
    signature = hmac.new(
        secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return {
        "X-Timestamp": timestamp,
        "X-Signature": signature,
    }
```

```typescript
import { createHmac } from 'node:crypto'

function signRequest(
  method: string,
  path: string,
  body: string,
  secret: string,
): { 'X-Timestamp': string; 'X-Signature': string } {
  const timestamp = String(Math.floor(Date.now() / 1000))
  const message = `${method}\n${path}\n${timestamp}\n${body}`
  const signature = createHmac('sha256', secret).update(message).digest('hex')
  return { 'X-Timestamp': timestamp, 'X-Signature': signature }
}
```

### 使用示例

```bash
curl -X POST "https://api.video-ct.cn/api/v1/referrers/withdraw" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Timestamp: 1715695200" \
  -H "X-Signature: a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{"amount_cny": 10000}'
```

### 签名验证规则

- 时间戳与服务器时间偏差不得超过 5 分钟（防重放攻击）
- 签名使用 HMAC-SHA256
- Secret 为用户的 API Secret（与 API Key 一起在开发者中心生成）

---

## 错误码

| HTTP 状态码 | code | 说明 |
|---|---|---|
| 401 | `UNAUTHORIZED` | 未提供有效鉴权信息 |
| 401 | `TOKEN_EXPIRED` | JWT 已过期 |
| 403 | `FORBIDDEN` | 权限不足（如 API Key 访问用户端点） |
| 429 | `RATE_LIMITED` | 调用频率超限 |

## 安全最佳实践

1. **永远不要在客户端代码中硬编码 API Key 或 Secret**
2. **API Key 应作为环境变量注入**
3. **生产环境必须使用 HTTPS**
4. **高安全场景使用 HMAC 签名 + 短时效时间戳**
5. **定期轮换 API Key（建议每 90 天）**
