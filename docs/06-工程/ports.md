# 端口 & 健康检查

> 最后更新: 2026-05-25 · 守护脚本: `scripts/port-guard.sh` · 健康检查: `scripts/healthcheck.sh`

## 项目端口

| 端口 | 服务 | 技术栈 | 启动命令 | 对外 |
|------|------|--------|----------|------|
| **8000** | API 后端 | Python FastAPI + Uvicorn | `make dev-api` | 是 |
| **5173** | H5 前端 | Vue 3 + Vite | `make dev-h5` | 是 |
| **5174** | Admin 管理后台 | Vue 3 + Vite | `make dev-admin` | 是 |
| **5175** | Consultant 顾问端 | Vue 3 + Vite | `make dev-consultant` | 是 |

## 基础设施端口

| 端口 | 服务 | 启动方式 | 对外 |
|------|------|----------|------|
| **6379** | Redis 缓存 | `brew services start redis` | 否 |
| **5432** | PostgreSQL 数据库 | `brew services start postgresql@16` | 否 |

## 健康检查

```
make health           # 全量三层检查（system + llm + module）
make health-system    # 仅系统层（DB/Redis/端口/DNS/外网）
make health-llm       # 仅大模型层（SiliconFlow/DeepSeek 鉴权连通）
make health-module    # 仅业务模块（API 端点/H5 页面）
make health-fix       # 检查并自动修复失败项
```

每个失败项都附带精确的修复命令。层次分类：
- **system** — 端口监听 / 进程存活 / DNS / 外网
- **llm** — 大模型 API 鉴权和网络连通
- **module** — HTTP 端点响应 / JSON 有效性

## 端口冲突处理

```
# 查看全景
make ports

# 启动时自动检测冲突（已内置在所有 make dev-* 中）
make dev          # 启动前自动检查 8000 + 5173，冲突自动清理旧进程

# 手动检查
bash scripts/port-guard.sh 8000 "API" check   # 仅检查
bash scripts/port-guard.sh 8000 "API" auto    # 自动接管（杀旧开发进程）
bash scripts/port-guard.sh 8000 "API" kill    # 强制释放
```

## 规则

1. **所有 dev-* 启动前必须通过 port-guard 检测** — 已内置
2. **端口不可挪用** — 每个端口绑定唯一服务
3. **新增端口必须先更新此文档 + port-guard.sh 的 port_label**
4. **禁止用 `lsof -ti :PORT | xargs kill -9` 裸调** — 统一用 `make kill` 或 `port-guard.sh`
