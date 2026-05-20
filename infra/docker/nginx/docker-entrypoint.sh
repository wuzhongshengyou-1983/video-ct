#!/bin/sh
# =============================================================================
# Nginx Docker 入口脚本 · 环境变量替换
# 将 ${VITE_API_BASE_URL} 等占位符替换为实际值
# =============================================================================

set -e

# 替换 API Base URL 占位符（在编译后的 JS 文件中）
# 如果环境变量 VITE_API_BASE_URL 存在，替换 dist 中的默认值
if [ -n "${VITE_API_BASE_URL}" ]; then
    echo "Setting VITE_API_BASE_URL to: ${VITE_API_BASE_URL}"
    # 替换硬编码的 localhost:8000 为实际地址
    find /usr/share/nginx/html -type f \( -name "*.js" -o -name "*.html" \) \
        -exec sed -i "s|http://localhost:8000|${VITE_API_BASE_URL}|g" {} + 2>/dev/null || true
fi

echo "Starting Nginx..."
exec "$@"
