# 火眼金睛（video-ct）交接材料清单

> 整理日期：2026-05-28
> 用途：接收方（元东方）在本地运行、评估、接手该项目所需的全部材料

---

## 一、GitHub 仓库（必须 · 最优先）

### 1.1 仓库访问权限（二选一）

**方式 A · 加 Collaborator（推荐）**

1. 打开仓库页面：`https://github.com/wuzhongshengyou-1983/video-ct`
2. 点击顶部 **Settings**
3. 左侧菜单点击 **Collaborators**
4. 点击 **Add people**，搜索并添加：`metafo333-hue`
5. 选择权限：`Write`（可读写）或 `Admin`（可管理）
6. 点击 **Add wuzhongshengyou-1983 to this repository**，对方收到邮件后接受邀请即可

**方式 B · 打包发送**

- 在项目根目录执行：
  ```bash
  git archive --format=zip HEAD -o video-ct-20260528.zip
  ```
- 将生成的 zip 文件发送给我

---

### 1.2 仓库设置确认（请在 GitHub 上检查）

- [ ] **分支保护**：确认 `main` 分支的保护规则，告知是否允许我直接推送，或需要走 PR 流程
- [ ] **Actions 权限**：Settings → Actions → General，确认 Workflow 权限为 `Read and write`
- [ ] **Secrets 配置**：Settings → Secrets and variables → Actions，列出当前已配置的 Secret 名称清单（**不需要给值**，只需要名称列表，方便我在本地配对应的 `.env`）

  常见 Secret 名称示例（请对照确认是否存在）：
  ```
  SILICONFLOW_API_KEY
  DEEPSEEK_API_KEY
  WECHAT_APP_ID
  WECHAT_APP_SECRET
  WECHAT_MCH_ID
  WECHAT_API_KEY
  ALIYUN_ACCESS_KEY_ID
  ALIYUN_ACCESS_KEY_SECRET
  POSTGRES_PASSWORD
  JWT_SECRET_KEY
  MINIO_SECRET_KEY
  SERVER_SSH_KEY（部署用）
  SERVER_HOST
  ```

- [ ] **Environments 配置**（如有）：Settings → Environments，告知是否有 `production` / `staging` 等环境配置，以及对应的保护规则

---

### 1.3 部署工作流（GitHub Actions）

- [ ] 告知 CI/CD 当前状态：最近一次 Actions 运行是否通过？
- [ ] 部署触发方式：push to main？打 tag（`v*`）？手动触发？
- [ ] 服务器 IP 是否已配置在 Actions Secrets 中（`SERVER_HOST`）？

---

## 二、服务器访问（必须 · 生产环境）

腾讯云服务器 IP：`150.158.20.173`

- [ ] SSH 私钥（`.pem` 文件）或重置 SSH 公钥后发送
- [ ] 服务器登录用户名（文档显示为 `ubuntu`，请确认）
- [ ] 服务器 root 或 sudo 密码（如有）

---

## 三、生产环境配置（必须 · 跑完整功能）

- [ ] **`.env.prod` 完整文件**（或脱敏后的模板，标注哪些字段需要替换）

`.env.prod` 中至少应包含以下内容：

| 变量类别 | 包含字段 |
|---------|---------|
| 数据库 | PostgreSQL 连接串（host/port/db/user/password）|
| Redis | Redis 连接地址 |
| JWT | JWT 密钥（HS256）|
| 微信登录 | `WECHAT_APP_ID`、`WECHAT_APP_SECRET` |
| 微信支付 | `WECHAT_MCH_ID`、`WECHAT_API_KEY`、支付证书 |
| AI 服务 | `SILICONFLOW_API_KEY`、`DEEPSEEK_API_KEY` |
| 阿里云短信 | `ALIYUN_ACCESS_KEY_ID`、`ALIYUN_ACCESS_KEY_SECRET`、`SMS_SIGN_NAME`、`SMS_TEMPLATE_CODE` |
| 对象存储 MinIO | `MINIO_ENDPOINT`、`MINIO_ACCESS_KEY`、`MINIO_SECRET_KEY` |
| CORS | 允许的前端域名列表 |
| Sentry（如有）| `SENTRY_DSN` |

---

## 四、第三方平台账号信息（按需）

| 平台 | 所需内容 |
|------|---------|
| **微信开放平台** | AppID + AppSecret（登录用）|
| **微信支付** | 商户号（MchID）+ API 密钥 + 证书文件（`.p12` 或 `.pem`）|
| **阿里云** | AccessKey + 短信签名 + 模板编号 |
| **SiliconFlow** | API Key |
| **DeepSeek** | API Key |

---

## 五、数据库（建议提供）

- [ ] **PostgreSQL dump 文件**（`pg_dump` 导出的 `.sql` 或 `.dump`）
  - 包含：建表结构 + 必要的种子数据（如配置项、默认权重、样本对标数据等）
  - 如涉及用户隐私数据可脱敏后导出

---

## 六、域名 openo.vip（上线必须）

- [ ] 域名注册商账号 / 转让域名控制权，或
- [ ] 在 DNS 服务商处将以下解析指向新服务器 IP：
  - `@`（根域名）→ A 记录
  - `www` → A 记录或 CNAME
- [ ] SSL 证书（`.crt` + `.key`），或告知证书颁发商以便续签

---

## 七、其他（有则给）

- [ ] **Grafana 监控配置**（`infra/grafana/` 目录下的 dashboard JSON，如未在仓库中）
- [ ] **Langfuse**：如已有 Langfuse 账号/自部署，提供连接信息
- [ ] **微信小程序配置**（如已有小程序端）：AppID + 发布权限
- [ ] 项目相关文档补充（如有未包含在此次文档包中的内容）

---

## 优先级说明

| 优先级 | 材料 | 说明 |
|--------|------|------|
| 🔴 必须 | 代码仓库 + `.env.prod` | 缺任意一项无法在本地运行 |
| 🔴 必须 | AI API Key（SiliconFlow/DeepSeek）| 缺少则核心诊断功能无法运行 |
| 🟡 重要 | 服务器 SSH | 查看生产运行状态、部署所需 |
| 🟡 重要 | 微信登录/支付配置 | 缺少则用户系统、支付闭环无法验证 |
| 🟢 建议 | 数据库 dump | 有种子数据可直接看到完整页面 |
| 🟢 建议 | 域名/SSL | 本地跑不需要，上线必须 |

---

> 如以上材料涉及安全敏感内容，建议通过加密渠道传输（微信文件传输助手仅限私聊）。
