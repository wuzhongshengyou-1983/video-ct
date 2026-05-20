#!/bin/bash
# =============================================================================
# Video CT · 数据库备份脚本
# 使用方法: bash scripts/backup-db.sh
# 依赖: pg_dump (PostgreSQL client tools)
# 环境变量: DATABASE_URL 或分别设置 PG* 变量
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${PROJECT_DIR}/backups"
RETENTION_DAYS=30

# ---------- 解析数据库连接 ----------
# 支持两种方式：
#   1. 完整 DATABASE_URL: postgresql://user:pass@host:port/db
#   2. 独立环境变量: PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE
parse_db_url() {
    local url="${DATABASE_URL:-}"
    if [[ -n "$url" && "$url" != sqlite* ]]; then
        # 解析 postgresql://user:pass@host:port/db
        # 去掉协议头
        local without_proto="${url#*://}"
        PGUSER="${without_proto%%:*}"
        local rest="${without_proto#*:}"
        PGPASSWORD="${rest%%@*}"
        local hostportdb="${rest#*@}"
        PGHOST="${hostportdb%%:*}"
        local portdb="${hostportdb#*:}"
        PGPORT="${portdb%%/*}"
        PGDATABASE="${portdb#*/}"
        # 去掉 query string
        PGDATABASE="${PGDATABASE%%\?*}"
    fi
}

# 尝试从 DATABASE_URL 解析
parse_db_url

# 设置默认值
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-video_ct}"
PGDATABASE="${PGDATABASE:-video_ct}"

export PGHOST PGPORT PGUSER PGDATABASE
export PGPASSWORD="${PGPASSWORD:-video_ct_dev_pwd}"

# ---------- 创建备份目录 ----------
mkdir -p "${BACKUP_DIR}"

# ---------- 生成文件名 ----------
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/video_ct_${TIMESTAMP}.dump"

echo "========================================"
echo " Video CT · 数据库备份"
echo "========================================"
echo "Host:     ${PGHOST}:${PGPORT}"
echo "Database: ${PGDATABASE}"
echo "Target:   ${BACKUP_FILE}"
echo "========================================"

# ---------- 执行备份 ----------
echo "[$(date '+%H:%M:%S')] 开始 pg_dump ..."
pg_dump -Fc -v --no-owner --no-acl -f "${BACKUP_FILE}" 2>&1

echo "[$(date '+%H:%M:%S')] 备份完成！"
ls -lh "${BACKUP_FILE}"

# ---------- 上传到 OSS/MinIO（可选） ----------
# 取消注释以下行以启用自动上传：
# if command -v mc &>/dev/null; then
#     echo "[$(date '+%H:%M:%S')] 上传到 MinIO..."
#     mc cp "${BACKUP_FILE}" "myminio/video-ct-backups/$(basename "${BACKUP_FILE}")"
# fi

# ---------- 清理过期备份 ----------
echo "[$(date '+%H:%M:%S')] 清理 ${RETENTION_DAYS} 天前的备份..."
find "${BACKUP_DIR}" -name "video_ct_*.dump" -type f -mtime +${RETENTION_DAYS} -print -delete

echo "[$(date '+%H:%M:%S')] 完成。"
echo "当前备份列表："
ls -lh "${BACKUP_DIR}"/video_ct_*.dump 2>/dev/null || echo "  (无备份文件)"
