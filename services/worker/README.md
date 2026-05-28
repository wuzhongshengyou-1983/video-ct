# Celery Worker 服务（预留）

> 状态：未独立部署（当前 worker 逻辑在 `services/api/app/services/task_queue.py` 内运行）  
> 独立时机：任务队列深度持续 > 50，或 v3 Phase 1 MediaCrawler 采集任务启用

## 为什么要独立

- API 进程和 Worker 进程共享资源，采集任务 CPU 密集时影响 API 响应延迟
- Worker 需要独立扩容（多副本），API 不需要
- 数据采集任务（`fire_eye` 六族）执行时间长，不适合与 API 同进程

## 独立步骤（届时执行）

1. 从 `services/api/` 复制 `app/` 目录到 `services/worker/`
2. `services/worker/` 只保留 `celery_app.py` + `tasks/` + 依赖的 `services/`
3. `docker-compose.yml` 新增 `worker` service，挂载同一个 `redis` broker
4. `pnpm-workspace.yaml` 不需要注册（Python 服务）

## 当前任务入口

```python
# services/api/app/services/task_queue.py
from celery import Celery
app = Celery(...)

@app.task
def run_diagnosis_task(diagnosis_id: str): ...
```
