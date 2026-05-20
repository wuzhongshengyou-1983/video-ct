# Grafana Dashboards · 占位目录

Grafana Dashboard JSON 文件将在此处放置。

## 计划中的 Dashboard

- **video-ct-overview.json** — 整体健康：API QPS / 延迟 / 错误率 / 诊断任务队列
- **video-ct-business.json** — 业务指标：诊断数 / 付费转化 / ARPU / 用户留存
- **video-ct-ai.json** — AI 调用：DeepSeek API 调用量 / 延迟 / 成本 / 错误率
- **video-ct-infra.json** — 基础设施：CPU / 内存 / PG 连接数 / Redis 命中率

## 导入方式

Grafana → Dashboards → Import → Upload JSON file

## 数据源

- Prometheus (video-ct metrics)
- PostgreSQL (business metrics, via Grafana PostgreSQL plugin)
