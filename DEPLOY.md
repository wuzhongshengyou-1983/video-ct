# 部署指南

## 开发环境（本机）

### 后端
```bash
cd services/api
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example ../../.env.local  # 填入真实 keys
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

测试：`curl http://localhost:8000/healthz`

### 前端（H5）
```bash
cd apps/h5
pnpm install
pnpm dev
```

访问 `http://localhost:5173`

### 管理后台
```bash
cd apps/admin
pnpm install
pnpm dev   # port 5174
```

### 顾问后台
```bash
cd apps/consultant
pnpm install
pnpm dev   # port 5175
```

---

## 联调环境（Docker Compose）

```bash
docker-compose up -d   # 起 PG/Redis/Milvus/MinIO
# 修改 .env.local 中 DATABASE_URL/REDIS_URL 到 docker-compose 网络
make dev
```

---

## 生产部署

### 阿里云 ECS + RDS（MVP）
1. 购买 ECS (2c4g+) · CentOS / Alibaba Cloud Linux
2. 购买 RDS PostgreSQL (1c2g)
3. 配置 OSS bucket
4. 配置域名 + SSL（阿里云 DCDN）
5. 服务器 `docker compose -f docker-compose.prod.yml up -d`
6. 前端构建并上传到 OSS + CDN：
   ```bash
   pnpm -r build
   ossutil cp -rf apps/h5/dist oss://video-ct/h5/
   ```

### Kubernetes（规模化）
见 `infra/k8s/`（M6+ 启用）

---

## 健康检查

```
GET /healthz       存活
GET /readyz        就绪（含 DB/Redis 检查）
GET /metrics       Prometheus 指标
```

---

## 监控告警

- **Prometheus + Grafana**：系统指标
- **Sentry**：异常上报
- **飞书机器人**：严重告警推送

---

## 备份恢复

```bash
# PostgreSQL 全量备份（每日 03:00）
pg_dump -Fc video_ct > backup_$(date +%Y%m%d).dump

# 恢复
pg_restore -d video_ct backup_20260520.dump
```
