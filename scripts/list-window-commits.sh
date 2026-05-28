#!/usr/bin/env bash
# list-window-commits.sh — 查看各 Claude 窗口自上次 tag 以来的 commit 贡献
#
# 用法:
#   bash scripts/list-window-commits.sh           # 所有窗口贡献统计
#   bash scripts/list-window-commits.sh win-ops   # 指定窗口详情
set -euo pipefail

SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
RANGE="${SINCE_TAG:+${SINCE_TAG}..}HEAD"

if [[ -n "${1:-}" ]]; then
  echo "=== 窗口 [$1] commits (since ${SINCE_TAG:-beginning}) ==="
  git log "$RANGE" --pretty=format:"%C(yellow)%h%Creset %s" --grep="win: $1"
  echo ""
  echo "--- commit 数量 ---"
  git log "$RANGE" --grep="win: $1" --oneline | wc -l | tr -d ' '
else
  echo "=== 所有窗口贡献统计 (since ${SINCE_TAG:-beginning}) ==="
  echo ""
  git log "$RANGE" --pretty=format:"%b" \
    | grep "^win:" \
    | sed 's/win: //' \
    | sort \
    | uniq -c \
    | sort -rn \
    | awk '{printf "  %3d commits  %s\n", $1, $2}'

  echo ""
  echo "=== 未标注窗口的 commits ==="
  git log "$RANGE" --oneline \
    | while read -r hash msg; do
        body=$(git show -s --format="%b" "$hash")
        if ! echo "$body" | grep -q "^win:"; then
          echo "  $hash $msg"
        fi
      done | head -20
fi
