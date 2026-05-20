#!/bin/bash
# =============================================================================
# Video CT · 数据库恢复脚本
# 使用方法: bash scripts/restore-db.sh <backup-file>
# 示例:     bash scripts/restore-db.sh backups/video_ct_20260520_120000.dump
# 依赖: pg_restore (PostgreSQL client tools)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd | xargs dirname)"
BACKUP_DIR="${SCRIPT_DIR}/backups"

# ---------- 参数检查 ----------
if [ $# -lt 1 ]; then
    echo "用法: bash scripts/restore-db.sh <backup-file>"
    echo ""
    echo "可用备份文件："
    ls -lh "${BACKUP_DIR}"/video_ct_*.dump 2>/dev/null || echo "  (无备份文件)"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "错误：备份文件不存在：${BACKUP_FILE}"
    exit 1
fi

# ---------- 确认操作 ----------
echo "========================================"
echo " Video CT · 数据库恢复"
echo "========================================"
echo ""
echo "警告：此操作将覆盖当前数据库内容！"
echo ""
echo "备份文件: ${BACKUP_FILE}"
echo "文件大小: $(ls -lh "${BACKUP_FILE}" | awk '{print $5}')"
echo "目标数据库: ${PGDATABASE:-video_ct}"
echo ""
read -r -p "确认恢复？输入 yes 继续: " CONFIRM

if [ "${CONFIRM}" != "yes" ]; then
    echo "已取消。"
    exit 0
fi

# ---------- 解析数据库连接 ----------
parse_db_url() {
    local url="${DATABASE_URL:-}"
    if [[ -n "$url" && "$url" != sqlite* ]]; then
        local without_proto="${url#*://}"
        PGUSER="${without_proto%%:*}"
        local rest="${without_proto#*:}"
        PGPASSWORD="${rest%%@*}"
        local hostportdb="${rest#*@}"
        PGHOST="${hostportdb%%:*}"
        local portdb="${hostportdb#*:}"
        PGPORT="${portdb%%/*}"
        PGDATABASE="${portdb#*/}"
        PGDATABASE="${PGDATABASE%%\?*}"
    fi
}

parse_db_url

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-video_ct}"
PGDATABASE="${PGDATABASE:-video_ct}"

export PGHOST PGPORT PGUSER PGDATABASE
export PGPASSWORD="${PGPASSWORD:-video_ct_dev_pwd}"

# ---------- 执行恢复 ----------
echo "[$(date '+%H:%M:%S')] 终止现有连接..."
psql -c "SELECT pg_terminate_backend(pg_stat_activity.pid)
         FROM pg_stat_activity
         WHERE pg_stat_activity.datname = '${PGDATABASE}'
           AND pid <> pg_backend_pid();" 2>/dev/null || true

echo "[$(date '+%H:%M:%S')] 删除现有数据库..."
dropdb --if-exists "${PGDATABASE}" 2>/dev/null || true

echo "[$(date '+%H:%M:%S')] 创建新数据库..."
createdb "${PGDATABASE}" 2>/dev/null || true

echo "[$(date '+%H:%M:%S')] 开始 pg_restore ..."
pg_restore -v --no-owner --no-acl -d "${PGDATABASE}" "${BACKUP_FILE}" 2>&1

echo ""
echo "========================================"
echo " 恢复完成！"
echo "========================================"
echo ""
echo "[$(date '+%H:%M:%S')] 验证数据库连接..."
psql -c "SELECT
    (SELECT COUNT(*) FROM users) AS users,
    (SELECT COUNT(*) FROM diagnoses) AS diagnoses,
    (SELECT COUNT(*) FROM reports) AS reports;"
