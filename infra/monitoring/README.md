# 监控说明

> 技术栈：Prometheus + Grafana + （计划中：Sentry）

---

## 架构

```
API 服务 (/metrics 端点)
    ↓ scrape 15s
Prometheus (prometheus.yml)
    ↓ query
Grafana (grafana-dashboards/)
    ↓ alert
飞书机器人 / 邮件
```

---

## Prometheus

**配置文件**：`prometheus.yml`

**当前抓取目标**：

| job | target | 说明 |
|-----|--------|------|
| `video-ct-api` | `api:8000/metrics` | FastAPI 业务指标（由 `prometheus-fastapi-instrumentator` 自动暴露） |
| `prometheus` | `localhost:9090` | Prometheus 自身 |

**已注释（未来扩展）**：
- `postgres-exporter:9187` — PostgreSQL 连接数 / 锁 / 慢查询
- `redis-exporter:9121` — Redis 内存 / 命中率
- `node-exporter:9100` — 机器级 CPU / 内存 / 磁盘

**告警规则文件**：`alerts.yml`（待创建）

---

## Grafana 仪表板

**目录**：`grafana-dashboards/`

| 仪表板 | 受众 | 核心指标 |
|--------|------|---------|
| CEO 总览 | CEO / 决策层 | DAU / 付费用户数 / MRR / 诊断次数 |
| 增长看板 | 增长 / 运营 | 注册转化率 / 分享官裂变系数 / 优惠券核销率 |
| 产品健康 | 产品 / 研发 | API P99 延迟 / 诊断成功率 / Celery 队列深度 |

---

## 本地启动监控

```bash
# 先确保 docker-compose 已起（含 prometheus + grafana service）
make docker-up

# Prometheus UI
open http://localhost:9090

# Grafana（admin / admin）
open http://localhost:3000
```

---

## 关键指标说明

**API 层**（由 prometheus-fastapi-instrumentator 自动采集）：

| 指标 | 说明 | 告警阈值参考 |
|------|------|------------|
| `http_request_duration_seconds` | 请求延迟 | P99 > 3s → warning |
| `http_requests_total` | 请求总数（含状态码） | 5xx 率 > 1% → critical |
| `http_requests_in_progress` | 并发请求数 | > 100 → warning |

**业务层**（需在代码中手动埋点，待实现）：

| 指标 | 说明 |
|------|------|
| `diagnosis_submitted_total` | 诊断提交次数 |
| `diagnosis_completed_total` | 诊断成功次数 |
| `diagnosis_failed_total` | 诊断失败次数 |
| `celery_queue_depth` | Celery 队列深度 |

---

## 告警渠道（计划中）

- **飞书机器人**：critical 级别实时推送
- **Sentry**：Python 异常自动上报（`.env.example` 已预留 `SENTRY_DSN`）
- **邮件**：日报 / 周报 摘要
