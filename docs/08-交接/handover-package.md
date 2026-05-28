# 火眼金睛 + video-ct 项目交接包

> 发送方：wuzhongshengyou → 接收方：元东方（metafo333-hue）
> 日期：2026-05-28

---

## 你收到的东西

本压缩包包含以下文件，请勿外传：

| 文件 | 用途 |
|------|------|
| `本文件.md` | 完整交接说明 |
| `lzb.pem` | 服务器 SSH 私钥 |
| `env-video-ct-prod.txt` | video-ct 生产环境变量 |
| `env-fire-eye.txt` | 火眼金睛环境变量 |

---

## 一、GitHub 仓库（接受邀请后可直接 clone）

| 项目 | 地址 | 说明 |
|------|------|------|
| **video-ct** | `https://github.com/wuzhongshengyou-1983/video-ct` | 完整 SaaS 平台（FastAPI + Vue3 H5 + Admin + 15章战略文档）|
| **fire-eye** | `https://github.com/wuzhongshengyou-1983/fire-eye` | 火眼金睛 AI 视频诊断引擎 |

两个仓库已邀请你为 Collaborator（Write 权限），请查收 GitHub 邮件并接受邀请。

---

## 二、服务器

### 连接方式

```bash
# 1. 把 lzb.pem 放到 ~/.ssh/
cp lzb.pem ~/.ssh/
chmod 600 ~/.ssh/lzb.pem

# 2. 登入
ssh -i ~/.ssh/lzb.pem ubuntu@150.158.20.173
```

| 项目 | 值 |
|------|-----|
| IP | `150.158.20.173` |
| 用户 | `ubuntu` |
| 系统 | Ubuntu 22.04 |
| Docker | 已安装 |
| sudo | 免密码 |
| 域名 | openo.vip（待 DNS 配置）|

### 你的公钥已加入

无需微信扫码，直接用你自己的 SSH 密钥登录（已加好）：

```bash
ssh ubuntu@150.158.20.173
```

---

## 三、服务器上部署 video-ct

video-ct 是完整 SaaS 平台，包含 H5 前端 + Admin 后台 + Consultant 顾问端 + API + AI Agent 编排。

```bash
ssh ubuntu@150.158.20.173

# 1. 克隆仓库
git clone https://github.com/wuzhongshengyou-1983/video-ct.git
cd video-ct

# 2. 把 env-video-ct-prod.txt 的内容复制到 .env.prod
nano .env.prod

# 3. 需要你手动补的值：
#    - JWT_SECRET：运行 openssl rand -hex 32 生成
#    - DATABASE_URL：替掉 <db-password> 为你设的密码
#    - 微信/阿里云相关（暂不影响核心功能，后续补）

# 4. Docker Compose 一键启动
sudo docker compose up -d

# 5. 验证
curl http://localhost:8000/healthz
# 应返回 {"status":"ok"}

# 6. 初始化种子数据
cd services/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed.py
```

启动后访问：`http://150.158.20.173:8000/docs`（API 文档）

---

## 四、服务器上部署 fire-eye（火眼金睛）

火眼金睛是 AI 视频诊断引擎，Python 项目，负责视频提取和 AI 诊断。

```bash
ssh ubuntu@150.158.20.173

cd ~
git clone https://github.com/wuzhongshengyou-1983/fire-eye.git
cd fire-eye

# 把 env-fire-eye.txt 的内容复制到 config/.env
mkdir -p config
nano config/.env

# 启动模型代理（后台，端口 7070）
cd proxy
python3 proxy.py &

# 启动视频提取器 + Web 前端
cd ../tools/video-extractor
python3 server.py &
```

---

## 五、本地开发（自己电脑）

```bash
# 火眼金睛
git clone https://github.com/wuzhongshengyou-1983/fire-eye.git
cd fire-eye
# 复制 env-fire-eye.txt → config/.env
cd proxy && python3 proxy.py
cd ../tools/video-extractor && python3 server.py

# video-ct
git clone https://github.com/wuzhongshengyou-1983/video-ct.git
cd video-ct
# 复制 env-video-ct-prod.txt → .env.prod
# 方式 A：纯本地 SQLite
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed.py
uvicorn app.main:app --reload --port 8000

# 方式 B：Docker Compose
sudo docker compose up -d
```

---

## 六、API Key 汇总

| 服务 | Key | 项目 |
|------|-----|------|
| DeepSeek | `sk-2b25c82e21e54828baaf67f73114136f` | 两个都用 |
| SiliconFlow | `sk-upalmkuwerzznhfshioxaplsqqonuluuxfckjdhoawushinv` | 两个都用 |
| TikHub | `jc1cWtoyxwiyqTOQLb6wnSjQbzKfaqlTzAuIs0ixb+ycqmWaGnCGR3edOw==` | fire-eye |

---

## 七、项目结构速览

### video-ct（完整 SaaS）
```
apps/h5/          ← C 端 H5（Vue3 + Vant）
apps/admin/       ← 管理后台（Vue3 + Ant Design Vue Pro）
apps/consultant/  ← 顾问后台
services/api/     ← FastAPI 后端（鉴权/订阅/诊断/对标/AI Agent）
packages/shared/  ← 跨端共享类型和客户端
infra/            ← Dockerfile + 数据库迁移
docs/01-战略/    ← 19 篇完整商业战略文档
```

### fire-eye（诊断引擎）
```
engine/           ← AI 诊断流水线核心
proxy/            ← 多模型智能路由代理
tools/video-extractor/ ← 视频提取 + Web 界面
pipelines/        ← bash 视频自动生产流水线
hooks/            ← 18 道自动化防线
data/             ← 种子视频数据
```

---

## 八、你启动后需要验证什么

- [ ] SSH 能登入服务器
- [ ] `git clone` 两个仓库
- [ ] video-ct：`curl localhost:8000/healthz` 返回 ok
- [ ] fire-eye：`python3 proxy.py` 启动无报错
- [ ] 浏览器打开 H5 页面能看到界面

---

## 九、待补项（不影响核心功能跑起来）

| 事项 | 优先级 | 说明 |
|------|--------|------|
| 微信 AppID/Secret | 🟡 | 用户登录离不开，但不影响诊断功能 |
| 域名 DNS 指向 `150.158.20.173` | 🟡 | 上线需要 |
| SSL 证书 | 🟡 | HTTPS 需要 |
| 服务器快照备份 | 🟢 | 出问题可瞬间恢复 |
| 微信支付配置 | 🟢 | 目前在代码中是 Mock 状态 |
| 阿里云短信/OSS | 🟢 | 注册登录备用 |

---

> 有问题随时微信沟通。核心代码拿到就能跑，缺啥随时找我。
