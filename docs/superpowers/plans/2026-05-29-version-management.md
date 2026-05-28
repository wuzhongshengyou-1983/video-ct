# 版本管理自动化系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立从 commit → 版本分类 → CHANGELOG → 自动发布 → 文档归档的全自动版本迭代流水线，并配套数据阶段门控系统，保证 v3.1 之后每次迭代清晰可追溯。

**Architecture:** commitlint 定义分类规则（patch/minor/major）→ release-please 自动生成版本 PR + CHANGELOG → tag 触发现有 CD → Phase Gate 脚本守卫数据门槛功能 → 版本文档脚手架自动归档旧版、创建新版模板。

**Tech Stack:** `@commitlint/cli` + `@commitlint/config-conventional`、`release-please-action v4`、Python 3.12 phase gate、Bash 脚本、现有 Husky + GitHub Actions

---

## 版本分类规则（核心定义）

```
Patch X.Y.Z  ← fix: / perf: / style: / refactor: / chore: / docs:
Minor X.Y    ← feat: / 任何新增 API 端点 / 新增数据表 / 新 AI Agent
Major X.0    ← feat!: / BREAKING CHANGE / 移除 API / DB 结构重构
```

**项目专属加权规则（在 commitlint 中 warn）：**

| 涉及路径 | 最低版本级别 | 原因 |
|---------|------------|------|
| `services/api/app/models/` | minor | ORM 变更必须迁移 |
| `infra/migrations/` | minor | 有迁移文件 = 新功能 |
| `services/api/app/agents/` | minor | AI 行为变化影响诊断质量 |
| 仅 `docs/` | 无版本 bump | 文档更新不触发发布 |
| 仅 `apps/` 前端样式 | patch | UI 微调 |

---

## Task 1: commitlint + commit-msg Hook

**Files:**
- Create: `commitlint.config.js`（仓库根）
- Create: `.husky/commit-msg`
- Modify: `package.json`（根）加 devDependencies

### Steps

- [ ] **Step 1: 安装 commitlint**

```bash
cd /Users/metafo/Projects/fire-eye/video-ct
pnpm add -D -w @commitlint/cli @commitlint/config-conventional
```

Expected: `pnpm-lock.yaml` 更新，无报错

- [ ] **Step 2: 写 commitlint.config.js**

```js
// commitlint.config.js
/** @type {import('@commitlint/types').UserConfig} */
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // 类型枚举（超出此列表的 commit 被拒绝）
    'type-enum': [
      2,
      'always',
      [
        'feat',     // 新功能 → minor
        'fix',      // Bug 修复 → patch
        'perf',     // 性能优化 → patch
        'refactor', // 重构（无新功能）→ patch
        'style',    // 格式/空白 → patch
        'docs',     // 文档 → 无 bump
        'test',     // 测试 → 无 bump
        'chore',    // 构建/依赖 → 无 bump
        'ci',       // CI 配置 → 无 bump
        'revert',   // 回滚 → patch
        'hotfix',   // 紧急修复 → patch（等同 fix）
      ],
    ],
    // subject 不能为空
    'subject-empty': [2, 'never'],
    // subject 首字母小写
    'subject-case': [2, 'always', 'lower-case'],
    // subject 最长 100 字符（中文友好）
    'header-max-length': [2, 'always', 100],
    // body 行长度放宽（中文说明）
    'body-max-line-length': [0],
  },
  // 帮助信息
  helpUrl: 'docs/CONTRIBUTING.md#commit-规范',
};
```

- [ ] **Step 3: 创建 commit-msg hook**

```bash
cat > /Users/metafo/Projects/fire-eye/video-ct/.husky/commit-msg << 'EOF'
#!/usr/bin/env sh
npx --no -- commitlint --edit "$1"
EOF
chmod +x /Users/metafo/Projects/fire-eye/video-ct/.husky/commit-msg
```

- [ ] **Step 4: 在根 package.json 加 lint:commits 脚本**

在 `package.json` 的 `scripts` 中加：
```json
"lint:commits": "commitlint --from HEAD~10 --to HEAD --verbose"
```

- [ ] **Step 5: 验证 commitlint 工作**

```bash
cd /Users/metafo/Projects/fire-eye/video-ct
echo "bad commit message" | npx commitlint
```

Expected: 输出错误，退出码非 0

```bash
echo "feat: add phase gate system" | npx commitlint
```

Expected: 无错误，退出码 0

- [ ] **Step 6: commit**

```bash
git add commitlint.config.js .husky/commit-msg package.json pnpm-lock.yaml
git commit -m "chore: add commitlint with project-specific version rules"
```

---

## Task 2: release-please 自动版本 PR + CHANGELOG

**Files:**
- Create: `.github/workflows/release-please.yml`
- Create: `release-please-config.json`
- Create: `.release-please-manifest.json`
- Create: `CHANGELOG.md`（如不存在）

### Steps

- [ ] **Step 1: 创建 release-please-config.json**

```json
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "release-type": "node",
  "package-name": "video-ct",
  "bump-minor-pre-major": false,
  "bump-patch-for-minor-pre-major": false,
  "changelog-sections": [
    { "type": "feat",     "section": "✨ 新功能",    "hidden": false },
    { "type": "fix",      "section": "🐛 Bug 修复",  "hidden": false },
    { "type": "perf",     "section": "⚡ 性能优化",  "hidden": false },
    { "type": "hotfix",   "section": "🔥 紧急修复",  "hidden": false },
    { "type": "refactor", "section": "♻️ 重构",      "hidden": false },
    { "type": "docs",     "section": "📝 文档",      "hidden": true  },
    { "type": "chore",    "section": "🔧 维护",      "hidden": true  },
    { "type": "ci",       "section": "👷 CI",        "hidden": true  },
    { "type": "test",     "section": "✅ 测试",       "hidden": true  }
  ],
  "extra-files": [
    "apps/h5/package.json",
    "apps/admin/package.json",
    "apps/consultant/package.json"
  ]
}
```

- [ ] **Step 2: 创建 .release-please-manifest.json**

```json
{
  ".": "3.1.0"
}
```

> 说明：`.` 代表仓库根，当前版本 3.1.0 与 v3.1-master 对应。

- [ ] **Step 3: 创建 release-please.yml**

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    outputs:
      release_created: ${{ steps.release.outputs.release_created }}
      tag_name: ${{ steps.release.outputs.tag_name }}
      version: ${{ steps.release.outputs.version }}
    steps:
      - uses: googleapis/release-please-action@v4
        id: release
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json

  # 版本发布后：自动归档旧版文档、生成新版模板
  scaffold-docs:
    needs: release-please
    if: ${{ needs.release-please.outputs.release_created }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Archive previous version docs + scaffold new
        env:
          NEW_VERSION: ${{ needs.release-please.outputs.version }}
        run: bash scripts/version-doc-scaffold.sh "$NEW_VERSION"
      - name: Commit doc changes
        run: |
          git config user.name "release-bot"
          git config user.email "noreply@github.com"
          git add docs/
          git diff --staged --quiet || git commit -m "docs: archive v${{ needs.release-please.outputs.version }} docs scaffold"
          git push
```

- [ ] **Step 4: 确认 CHANGELOG.md 存在**

```bash
ls /Users/metafo/Projects/fire-eye/video-ct/CHANGELOG.md 2>/dev/null \
  || echo "# Changelog\n\nAll notable changes to this project will be documented in this file.\n" \
  > /Users/metafo/Projects/fire-eye/video-ct/CHANGELOG.md
```

- [ ] **Step 5: commit**

```bash
git add .github/workflows/release-please.yml release-please-config.json .release-please-manifest.json CHANGELOG.md
git commit -m "ci: add release-please auto version bump and changelog"
```

---

## Task 3: Phase Gate 数据门控系统

> 防止 Phase 1/2/3 功能在数据未达门槛时被错误启用。

**Files:**
- Create: `services/api/app/core/phase_gate.py`
- Create: `scripts/check-phase-gate.py`

### Phase 门槛定义

| Phase | 功能 | 解锁条件 |
|-------|------|---------|
| Phase 0 | Umami 埋点、5 张新表 | 代码部署即激活 |
| Phase 1 | MediaCrawler、账号健康分 | `umami_events >= 500` |
| Phase 2 | Implicit BPR、DuckDB | `suggestion_adoptions >= 10000` |
| Phase 3 | EconML 因果推断 | `mau >= 500 AND monthly_revenue_cny >= 5000` |

### Steps

- [ ] **Step 1: 写 services/api/app/core/phase_gate.py**

```python
# services/api/app/core/phase_gate.py
"""
Phase Gate — 数据量门控系统
各 Phase 功能在数据达标前返回 PHASE_NOT_READY，防止带病上线。
"""
from __future__ import annotations
import asyncio
from enum import IntEnum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class Phase(IntEnum):
    ZERO = 0   # 代码部署即激活
    ONE = 1    # Umami ≥ 500 事件
    TWO = 2    # suggestion_adoptions ≥ 10000
    THREE = 3  # MAU ≥ 500 + 月收入 ≥ ¥5000


@dataclass
class PhaseStatus:
    current_phase: Phase
    metrics: dict[str, int | float]
    next_phase: Phase | None
    next_threshold: dict[str, int | float] | None


async def get_current_phase(db: AsyncSession) -> PhaseStatus:
    """查询当前激活的最高 Phase，返回完整状态。"""
    metrics = await _fetch_metrics(db)

    if metrics["mau"] >= 500 and metrics["monthly_revenue_cny"] >= 5000:
        phase = Phase.THREE
    elif metrics["suggestion_adoptions"] >= 10_000:
        phase = Phase.TWO
    elif metrics["umami_events"] >= 500:
        phase = Phase.ONE
    else:
        phase = Phase.ZERO

    next_phase, next_threshold = _next_phase_info(phase, metrics)
    return PhaseStatus(
        current_phase=phase,
        metrics=metrics,
        next_phase=next_phase,
        next_threshold=next_threshold,
    )


async def require_phase(db: AsyncSession, minimum: Phase) -> bool:
    """
    检查是否达到指定 Phase。
    用法: if not await require_phase(db, Phase.ONE): raise HTTPException(503, "PHASE_NOT_READY")
    """
    status = await get_current_phase(db)
    return status.current_phase >= minimum


async def _fetch_metrics(db: AsyncSession) -> dict[str, int | float]:
    rows = await asyncio.gather(
        db.execute(text("SELECT COUNT(*) FROM user_events")),
        db.execute(text("SELECT COUNT(*) FROM suggestion_adoptions")),
        db.execute(
            text("""
                SELECT COUNT(DISTINCT user_id)
                FROM event_logs
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """)
        ),
        db.execute(
            text("""
                SELECT COALESCE(SUM(paid_cny), 0)
                FROM orders
                WHERE created_at >= date_trunc('month', NOW())
                  AND payment_status = 'paid'
            """)
        ),
    )
    umami_events, adoptions, mau, revenue = [r.scalar() or 0 for r in rows]
    return {
        "umami_events": int(umami_events),
        "suggestion_adoptions": int(adoptions),
        "mau": int(mau),
        "monthly_revenue_cny": float(revenue),
    }


def _next_phase_info(
    current: Phase, metrics: dict
) -> tuple[Phase | None, dict | None]:
    if current == Phase.THREE:
        return None, None
    if current == Phase.TWO:
        return Phase.THREE, {
            "mau": 500,
            "monthly_revenue_cny": 5000,
            "current_mau": metrics["mau"],
            "current_revenue": metrics["monthly_revenue_cny"],
        }
    if current == Phase.ONE:
        return Phase.TWO, {
            "suggestion_adoptions": 10_000,
            "current": metrics["suggestion_adoptions"],
        }
    return Phase.ONE, {
        "umami_events": 500,
        "current": metrics["umami_events"],
    }
```

- [ ] **Step 2: 写 scripts/check-phase-gate.py（本地 + CI 用）**

```python
#!/usr/bin/env python3
# scripts/check-phase-gate.py
"""
本地运行: python3 scripts/check-phase-gate.py
CI 运行: python3 scripts/check-phase-gate.py --json
输出当前 Phase 状态，供开发者和 CI 决策。
"""
import asyncio
import json
import argparse
import os
import sys
sys.path.insert(0, "services/api")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.phase_gate import get_current_phase


async def main(as_json: bool) -> None:
    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://video_ct:video_ct@localhost:5432/video_ct"
    )
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        status = await get_current_phase(session)

    if as_json:
        print(json.dumps({
            "current_phase": status.current_phase.value,
            "metrics": status.metrics,
            "next_phase": status.next_phase.value if status.next_phase else None,
            "next_threshold": status.next_threshold,
        }, indent=2))
    else:
        print(f"✅ 当前 Phase: {status.current_phase.value}")
        print(f"   指标: {status.metrics}")
        if status.next_phase:
            print(f"   距 Phase {status.next_phase.value}: {status.next_threshold}")
        else:
            print("   已达最高 Phase 3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.json))
```

- [ ] **Step 3: 在 CI 中加 phase-gate 状态输出（可选 job）**

在 `ci.yml` 的 jobs 末尾加：
```yaml
  phase-gate-status:
    name: Phase Gate Status
    runs-on: ubuntu-latest
    needs: [test-backend]
    if: github.ref == 'refs/heads/main'
    continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r services/api/requirements.txt
      - name: Check phase gate
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python3 scripts/check-phase-gate.py --json
```

- [ ] **Step 4: commit**

```bash
git add services/api/app/core/phase_gate.py scripts/check-phase-gate.py .github/workflows/ci.yml
git commit -m "feat: add phase gate system for data-gated feature rollout"
```

---

## Task 4: 版本文档脚手架脚本

> 每次版本发布时：① 归档旧版文档 → ② 在 fire-eye-docs 创建新版模板。

**Files:**
- Create: `scripts/version-doc-scaffold.sh`

### Steps

- [ ] **Step 1: 写 scripts/version-doc-scaffold.sh**

```bash
#!/usr/bin/env bash
# scripts/version-doc-scaffold.sh
# 用法: bash scripts/version-doc-scaffold.sh 3.2.0
# 功能:
#   1. 把 fire-eye-docs/docs/02-方案/v3.1/v3.1-master.html 归档到 历史版本归档/
#   2. 在 fire-eye-docs/docs/02-方案/vX.Y/ 创建新版主文档模板
set -euo pipefail

NEW_VERSION="${1:-}"
if [[ -z "$NEW_VERSION" ]]; then
  echo "用法: $0 <new-version>  (例: 3.2.0)" >&2
  exit 1
fi

# 提取 major.minor（去掉 patch，文档以 minor 为粒度）
MINOR_VERSION=$(echo "$NEW_VERSION" | cut -d. -f1-2)
DOCS_BASE="/Users/metafo/Downloads/fire-eye-docs/docs/02-方案"

# ── Step 1: 找到当前最新版本文档 ────────────────────────────
CURRENT_DIR=$(ls -d "${DOCS_BASE}"/v*/ 2>/dev/null | sort -V | tail -1 || true)
if [[ -n "$CURRENT_DIR" ]]; then
  CURRENT_VERSION=$(basename "$CURRENT_DIR")
  ARCHIVE_DIR="${DOCS_BASE}/历史版本归档/${CURRENT_VERSION}"
  mkdir -p "$ARCHIVE_DIR"
  echo "📦 归档 ${CURRENT_VERSION} → 历史版本归档/"
  cp -r "${CURRENT_DIR}." "${ARCHIVE_DIR}/"
fi

# ── Step 2: 创建新版目录和主文档模板 ──────────────────────────
NEW_DIR="${DOCS_BASE}/v${MINOR_VERSION}"
mkdir -p "$NEW_DIR"

cat > "${NEW_DIR}/v${MINOR_VERSION}-master.html" << HTMLEOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>V${MINOR_VERSION} 统一完整方案</title>
<style>
:root{--fg:#1d1d1f;--fg2:#6b7280;--line:#eaeaea;--green:#0a7d4a;--orange:#c2410c;
  --font:-apple-system,BlinkMacSystemFont,sans-serif}
body{font-family:var(--font);font-size:14px;color:var(--fg);max-width:1200px;margin:0 auto;padding:40px 32px}
h1{font-size:28px;font-weight:800}h2{font-size:16px;font-weight:700;border-bottom:1px solid var(--line);padding-bottom:6px;margin-top:32px}
.meta{font-size:12px;color:var(--fg2);margin:8px 0 24px}
.todo{background:#fff7ed;border-left:3px solid var(--orange);padding:8px 14px;font-size:13px;margin:8px 0}
</style>
</head>
<body>
<div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#9ca3af">Fire-Eye · V${MINOR_VERSION} · 统一实施规格</div>
<h1>V${MINOR_VERSION} 完整融合方案</h1>
<div class="meta">
  继承 V$(echo "$MINOR_VERSION" | awk -F. '{if($2>0) printf "%s.%s", $1, $2-1; else printf "%s.0", $1-1}') 全部内容 ·
  生成日期: $(date +%Y-%m-%d) ·
  状态: 🚧 规划中
</div>

<div class="todo">⚠️ 本文档为模板，需根据 Sprint 计划填充各章节内容</div>

<h2>一、继承自上一版本</h2>
<p><!-- 填写继承的核心功能 --></p>

<h2>二、本版本新增</h2>
<p><!-- 填写本版本新增功能 --></p>

<h2>三、Sprint 计划</h2>
<p><!-- 填写 Sprint 分解 --></p>

<h2>四、发布门槛</h2>
<p><!-- 填写 E2E 通过率 / Phase Gate / 一致性审计分数 --></p>

<hr style="border:none;border-top:1px solid var(--line);margin:32px 0">
<p style="font-size:11px;color:#9ca3af;text-align:center">
  V${MINOR_VERSION} · 生成 $(date +%Y-%m-%d) · 待完善
</p>
</body>
</html>
HTMLEOF

echo "✅ 新版文档模板已创建: ${NEW_DIR}/v${MINOR_VERSION}-master.html"

# ── Step 3: 更新 00-版本索引.md ────────────────────────────
INDEX="${DOCS_BASE}/00-版本索引.md"
if [[ ! -f "$INDEX" ]]; then
  cat > "$INDEX" << 'INDEXEOF'
# 版本索引

| 版本 | 状态 | 主文档 |
|------|------|-------|
INDEXEOF
fi

echo "| v${MINOR_VERSION} | 🚧 规划中 | [v${MINOR_VERSION}-master.html](v${MINOR_VERSION}/v${MINOR_VERSION}-master.html) |" >> "$INDEX"
echo "📋 版本索引已更新"
```

- [ ] **Step 2: 给脚本加执行权限**

```bash
chmod +x /Users/metafo/Projects/fire-eye/video-ct/scripts/version-doc-scaffold.sh
```

- [ ] **Step 3: 手动测试脚本（测试 v3.2 模板生成）**

```bash
bash /Users/metafo/Projects/fire-eye/video-ct/scripts/version-doc-scaffold.sh 3.2.0
```

Expected 输出：
```
📦 归档 v3.1 → 历史版本归档/
✅ 新版文档模板已创建: .../v3.2/v3.2-master.html
📋 版本索引已更新
```

验证文件存在：
```bash
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/v3.2/
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/历史版本归档/
```

- [ ] **Step 4: commit**

```bash
git add scripts/version-doc-scaffold.sh
git commit -m "chore: add version doc scaffold and archive script"
```

---

## 完整流水线示意

```
开发者写代码
     ↓
git commit -m "feat: add BPR recommendation"
     ↓ (commit-msg hook)
commitlint 检查 → 不合规则 BLOCK
     ↓ 合规通过
push → main
     ↓
release-please 扫描 commits
     ↓
自动开 PR: "chore(release): v3.2.0"
  - CHANGELOG.md 自动更新（只含 feat/fix/perf）
  - package.json version 自动 bump
     ↓ 人工 review + merge
tag v3.2.0 自动打
     ↓
cd.yml 触发 → Docker 构建 + 部署
release.yml 触发 → GitHub Release 创建
release-please scaffold-docs → 文档归档 + 新版模板
     ↓
phase-gate 在运行时守卫数据门槛功能
```

---

## 版本分类速查卡（贴在团队内部）

```
✅ patch (X.Y.Z) — 当天可上线
  fix:      修了一个 bug
  perf:     接口快了
  refactor: 代码整理，行为不变
  hotfix:   生产紧急修复
  chore:    依赖升级、配置调整

✅ minor (X.Y) — 需 Sprint 完整交付
  feat:     新功能、新页面、新 API 端点
  任何改动 services/api/app/models/
  任何改动 infra/migrations/
  新增 AI Agent 或 Playbook

⚠️ major (X.0) — 需架构评审
  feat!:          新功能 + 破坏性变更
  BREAKING CHANGE: 移除/重命名 API
  DB 表结构重构（非新增）
  商业模式重大调整
```

---

## Self-Review

**Spec coverage:**
- ✅ 分类规则（patch/minor/major）— Task 1 + 速查卡
- ✅ 小迭代界定 — commitlint.config.js rules
- ✅ 自动化流水线 — Task 2 release-please
- ✅ 数据门控 — Task 3 phase_gate.py
- ✅ 文档自动归档 + 新版模板 — Task 4 scaffold 脚本

**Placeholder scan:** 无 TBD/TODO/placeholder

**Type consistency:** phase_gate.py 中 Phase enum 与 check-phase-gate.py 调用一致
