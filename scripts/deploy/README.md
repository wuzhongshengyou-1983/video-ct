# scripts/deploy/ — 部署 & 上线脚本

> 职责：生产环境部署、版本切换、回滚

## 计划脚本

| 脚本 | 说明 |
|------|------|
| `deploy-api.sh` | 构建 + 推送 API 镜像 + 滚动重启 |
| `deploy-h5.sh` | 构建 H5 → 上传 OSS → 刷新 CDN |
| `rollback.sh <version>` | 回滚到指定版本 |
| `health-check.sh` | 部署后验证 `/healthz` + `/readyz` |

## 当前部署方式

见 `DEPLOY.md` — 手动 SSH + docker compose。  
脚本化部署在 v3 Phase 0 完成后启动。
