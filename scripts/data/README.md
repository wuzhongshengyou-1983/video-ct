# scripts/data/ — 数据采集 & 种子脚本

> 职责：对标库刷新、批量采集调度、数据初始化

## 计划脚本（v3 Phase 1 启用）

| 脚本 | 说明 | 触发方式 |
|------|------|---------|
| `refresh-benchmarks.sh` | 刷新各赛道 Top10 头部博主数据 | APScheduler 每日 03:00 |
| `seed-benchmarks.py` | 初始化对标库样例数据（开发用） | 手动 / make seed |
| `crawl-track.py <track>` | 按赛道抓取竞品视频数据 | 手动触发 |

## 现有种子脚本位置

开发初始化种子数据：`services/api/scripts/seed.py`（API 内部，不移动）

```bash
make seed   # 等价于 cd services/api && python scripts/seed.py
```
