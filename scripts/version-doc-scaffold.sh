#!/usr/bin/env bash
# version-doc-scaffold.sh
# 用法: bash scripts/version-doc-scaffold.sh 3.2.0
#
# 功能:
#   1. 把当前最新版本文档归档到 历史版本归档/
#   2. 在 vX.Y/ 创建新版主文档模板
#   3. 更新 00-版本索引.md
set -euo pipefail

NEW_VERSION="${1:-}"
if [[ -z "$NEW_VERSION" ]]; then
  echo "用法: $0 <new-version>  (例: 3.2.0)" >&2
  exit 1
fi

# 取 major.minor（文档以 minor 为粒度）
MINOR_VERSION=$(echo "$NEW_VERSION" | cut -d. -f1-2)
DOCS_BASE="/Users/metafo/Downloads/fire-eye-docs/docs/02-方案"

# ── 1. 归档当前最新版本目录 ──────────────────────────────────
CURRENT_DIR=$(ls -d "${DOCS_BASE}"/v*/ 2>/dev/null | sort -V | tail -1 || true)
if [[ -n "$CURRENT_DIR" ]]; then
  CURRENT_LABEL=$(basename "$CURRENT_DIR")
  ARCHIVE_DIR="${DOCS_BASE}/历史版本归档/${CURRENT_LABEL}"
  mkdir -p "$ARCHIVE_DIR"
  cp -r "${CURRENT_DIR}." "${ARCHIVE_DIR}/"
  echo "📦 归档 ${CURRENT_LABEL} → 历史版本归档/"
fi

# ── 2. 创建新版目录和主文档模板 ──────────────────────────────
NEW_DIR="${DOCS_BASE}/v${MINOR_VERSION}"
mkdir -p "$NEW_DIR"
PREV_MINOR=$(echo "$MINOR_VERSION" | awk -F. '{if($2>0) printf "%s.%s", $1, $2-1; else printf "%s.0", $1-1}')

cat > "${NEW_DIR}/v${MINOR_VERSION}-master.html" << HTMLEOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>V${MINOR_VERSION} 统一完整方案</title>
<style>
:root{--fg:#1d1d1f;--fg2:#6b7280;--fg3:#9ca3af;--line:#eaeaea;--green:#0a7d4a;
  --orange:#c2410c;--blue:#0070f3;--r:8px;
  --font:-apple-system,BlinkMacSystemFont,'SF Pro Text',sans-serif}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font);font-size:14px;color:var(--fg);line-height:1.6}
.page{max-width:1200px;margin:0 auto;padding:40px 32px 100px}
h1{font-size:28px;font-weight:800;letter-spacing:-.03em}
h2{font-size:16px;font-weight:700;border-bottom:1px solid var(--line);
   padding-bottom:8px;margin:36px 0 14px}
p{margin:6px 0;color:var(--fg2);font-size:13px}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 28px}
.chip{display:inline-flex;align-items:center;padding:3px 10px;border-radius:999px;
  font-size:12px;font-weight:500;background:#f4f4f5;color:var(--fg2);border:1px solid var(--line)}
.chip.g{background:#f0fdf4;color:var(--green);border-color:#bbf7d0}
.chip.o{background:#fff7ed;color:var(--orange);border-color:#fed7aa}
.todo{border-left:3px solid var(--orange);padding:10px 14px;background:#fff7ed;
  border-radius:0 6px 6px 0;margin:10px 0;font-size:13px}
.card{background:#fafafa;border:1px solid var(--line);border-radius:var(--r);
  padding:14px 18px;margin:10px 0}
</style>
</head>
<body>
<div class="page">

<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--fg3)">
  Fire-Eye · V${MINOR_VERSION} · 统一实施规格
</div>
<h1>V${MINOR_VERSION} 完整融合方案</h1>
<div class="meta">
  <span class="chip">继承 V${PREV_MINOR}</span>
  <span class="chip o">🚧 规划中</span>
  <span class="chip">生成 $(date +%Y-%m-%d)</span>
</div>

<div class="todo">
  ⚠️ 本文档为模板，需根据实际 Sprint 交付填充各章节。
  参考上一版本：<a href="../历史版本归档/v${PREV_MINOR}/v${PREV_MINOR}-master.html">V${PREV_MINOR} 主文档</a>
</div>

<h2>一、继承自 V${PREV_MINOR}</h2>
<div class="card">
  <p><!-- 从上一版本继承的核心功能清单 --></p>
</div>

<h2>二、本版本新增功能</h2>
<div class="card">
  <p><!-- 本版本新增功能，对应 feat: commits --></p>
</div>

<h2>三、数据库变更</h2>
<div class="card">
  <p><!-- 新增表 / ALTER TABLE / 新增迁移文件 --></p>
</div>

<h2>四、API 变更</h2>
<div class="card">
  <p><!-- 新增端点 / 废弃端点 --></p>
</div>

<h2>五、Sprint 计划</h2>
<div class="card">
  <p><!-- Sprint 分解，含 Gate 条件 --></p>
</div>

<h2>六、发布门槛</h2>
<div class="card">
  <p>E2E 通过率：___% &nbsp;|&nbsp; 一致性审计：___分 &nbsp;|&nbsp; Phase Gate：Phase ___</p>
</div>

<hr style="border:none;border-top:1px solid var(--line);margin:32px 0">
<p style="font-size:11px;color:var(--fg3);text-align:center">
  V${MINOR_VERSION} · 生成 $(date +%Y-%m-%d) · 待完善 · 唯一权威版本
</p>
</div>
</body>
</html>
HTMLEOF

echo "✅ 新版模板: ${NEW_DIR}/v${MINOR_VERSION}-master.html"

# ── 3. 更新版本索引 ──────────────────────────────────────────
INDEX="${DOCS_BASE}/00-版本索引.md"
if [[ ! -f "$INDEX" ]]; then
  cat > "$INDEX" << 'INDEXEOF'
# 版本索引

| 版本 | 状态 | 主文档 | 发布日期 |
|------|------|-------|---------|
INDEXEOF
fi

# 把上一版本状态从"当前"改为"已发布"
if [[ -n "${CURRENT_LABEL:-}" ]]; then
  sed -i.bak "s|${CURRENT_LABEL%/} | 🟢 当前|${CURRENT_LABEL%/} | ✅ 已发布|g" "$INDEX" 2>/dev/null || true
  rm -f "${INDEX}.bak"
fi

echo "| v${MINOR_VERSION} | 🟢 当前 | [v${MINOR_VERSION}-master.html](v${MINOR_VERSION}/v${MINOR_VERSION}-master.html) | $(date +%Y-%m-%d) |" >> "$INDEX"
echo "📋 版本索引已更新"
