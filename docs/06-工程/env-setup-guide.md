# 环境搭建实战指南

> 补充 `README.md` 快速开始 + `DEPLOY.md` 的中间层  
> 记录实际踩过的坑，让第二个人少走弯路

---

## 前置检查（先跑这几个命令）

```bash
node --version   # 需要 ≥20，推荐 20.x LTS
python3 --version  # 需要 ≥3.11，推荐 3.13
pnpm --version   # 需要 ≥9
docker --version # 需要 Desktop 已启动
```

---

## 方式 A：纯本地（SQLite，零 Docker）

### 1. 克隆 + 安装前端依赖

```bash
git clone https://github.com/wuzhongshengyou-1983/video-ct.git
cd video-ct
pnpm install
```

### 2. 配置环境变量

```bash
cp .env.example .env.local
```

**最少需要填的字段**（其他可先留 PLACEHOLDER）：

```env
JWT_SECRET=<openssl rand -hex 32 生成>
DEEPSEEK_API_KEY=<你的 DeepSeek key>
SILICONFLOW_API_KEY=<你的硅基流动 key>
```

> ⚠️ **坑 1**：`WECHAT_PAY_*` / `DOUYIN_*` 等未填时，对应功能返回 Mock 数据，不影响本地开发。

### 3. 启动后端

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head
python scripts/seed.py             # 写入产品目录 + 对标样例数据

# 启动
uvicorn app.main:app --reload --port 8000
```

> ⚠️ **坑 2**：首次 `alembic upgrade head` 报 `ModuleNotFoundError`，先确认 `.venv` 已激活再运行。

> ⚠️ **坑 3**：`python scripts/seed.py` 若报「产品已存在」可忽略（幂等写入）。

### 4. 启动 H5

```bash
# 新终端，回仓根
pnpm dev:h5    # 等价于 cd apps/h5 && pnpm dev
```

访问 `http://localhost:5173`，API 文档 `http://localhost:8000/docs`

---

## 方式 B：Docker Compose（完整依赖）

```bash
cp .env.example .env.docker
# 修改 .env.docker 中：
#   DATABASE_URL=postgresql://postgres:postgres@db:5432/video_ct
#   REDIS_URL=redis://redis:6379/0

make docker-up   # 启动 PG + Redis + MinIO（首次拉镜像需等几分钟）
make dev         # 同时启动后端 + H5
```

> ⚠️ **坑 4**：`make docker-up` 后后端容器可能因 DB 未就绪而先挂，等 30 秒再 `docker compose logs api` 确认启动成功。

> ⚠️ **坑 5**：MinIO 控制台 `localhost:9001`，账号 `minioadmin` / 密码 `minioadmin123`。首次需在控制台手动创建 bucket `video-ct`，或运行 `make seed` 自动创建。

---

## 凭据管理

真实 Key 存放位置：`~/vault/credentials/fire-eye/`（本地，不入仓，chmod 600）

```bash
ls ~/vault/credentials/fire-eye/
# deepseek.key  siliconflow.key  wechat-pay-cert.pem  ...
```

> ⚠️ **坑 6**：`.env.local` 从不提交 git。已在 `.gitignore` 中列出，但 `git add -A` 时要二次确认 `git status` 无 `.env` 文件出现。

---

## 常见报错速查

| 报错 | 原因 | 解法 |
|------|------|------|
| `Connection refused :8000` | 后端未启动 | `uvicorn app.main:app --reload` |
| `alembic.util.exc.CommandError: Can't locate revision` | alembic 版本表污染 | `alembic stamp head` 后重试 |
| `pnpm install` 报 `ENOENT pnpm-lock.yaml` | 在子目录运行了 | 回仓根运行 |
| H5 页面空白 + 控制台 `VITE_API_BASE_URL undefined` | 未复制 `.env.local` | `cp .env.example .env.local` |
| Docker `Bind for 0.0.0.0:5432 failed` | 本地 PostgreSQL 占用端口 | `brew services stop postgresql` |
| `CTRadiologistAgent` 返回空 | DEEPSEEK_API_KEY 未填 | 填入真实 key 或检查额度 |

---

## 端口分配速查

见 [`docs/06-工程/ports.md`](ports.md)

---

## 多端联调

同时启动所有服务（需 4 个终端）：

```bash
# T1: 后端
cd services/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# T2: H5
pnpm dev:h5      # 5173

# T3: 管理后台
cd apps/admin && pnpm dev  # 5174

# T4: 顾问后台
cd apps/consultant && pnpm dev  # 5175
```

或用 `make dev` 一键启动（需配置 Docker Compose 依赖服务）。
