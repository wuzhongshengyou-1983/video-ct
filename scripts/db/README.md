# scripts/db/ — 数据库运维脚本

## 脚本说明

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `backup-db.sh` | PostgreSQL 全量备份到 `backups/` | `make backup` |
| `restore-db.sh <file>` | 从备份文件恢复 | `make restore FILE=backups/xxx.dump` |

## 常用命令

```bash
# 手动备份
make backup
# 输出: backups/video_ct_20260528_214100.dump

# 恢复（需指定文件）
make restore FILE=backups/video_ct_20260528_214100.dump

# 查看现有备份
ls -lh backups/video_ct_*.dump
```

## Alembic 迁移（不在这里，在 services/api/）

```bash
# 升级到最新
make db-migrate        # = alembic upgrade head

# 新建迁移脚本
cd services/api && alembic revision --autogenerate -m "add xxx table"

# 回滚一步
cd services/api && alembic downgrade -1
```

## 生产环境备份策略

- 定时任务：`cron 0 3 * * * make -C /opt/video-ct backup`（每日 03:00）
- 保留策略：本地保留最近 7 天，超出自动清理
- 异地备份：上传到阿里云 OSS（`scripts/data/` 计划实现）
