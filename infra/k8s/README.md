# Kubernetes 配置（预留）

> 状态：未启用  
> 启用条件：MAU > 10,000，或 M6+ 里程碑，或单台 ECS 瓶颈明显

## 当前部署形态

Docker Compose — 见 `docker-compose.yml` 和 `DEPLOY.md`。

## K8s 启用时的结构规划

```
infra/k8s/
├── base/
│   ├── api-deployment.yaml
│   ├── worker-deployment.yaml
│   ├── postgres-statefulset.yaml
│   ├── redis-deployment.yaml
│   └── minio-statefulset.yaml
├── overlays/
│   ├── staging/
│   └── production/
└── ingress.yaml
```

## 迁移关键点

- API 无状态，直接 Deployment + HPA
- Worker 独立 Deployment，按队列深度 HPA
- PostgreSQL / Redis / MinIO 用 StatefulSet + PVC
- 配置从 `.env` 迁移到 K8s Secrets + ConfigMap
- 数据库迁移改为 Job（`alembic upgrade head`）
