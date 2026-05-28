# 文档目录重塑 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 fire-eye 两套文档体系（video-ct/docs + fire-eye-docs/docs）从重叠混乱重塑为职责清晰、逻辑自洽、版本隔离的单一文档架构

**Architecture:**
fire-eye-docs/docs 作为产品文档唯一真相源，按「战略→版本→专项方案→工程→进度→商业化→交接」线性组织；
video-ct/docs 精简为纯工程文档（API合约/DB/部署/调试），不再重复产品层文档；
从 v3.2 起每个版本文档完全独立，不引用其他版本的继承关系，自身即为全量规格。

**Tech Stack:** bash mv/rm/cp, HTML 文本编辑, Markdown

---

## 目标结构（执行完成后的最终状态）

### fire-eye-docs/docs/（产品文档主库）

```
fire-eye-docs/docs/
├── README.md                              # 全局文档导航（重写）
├── 01-战略/                               # 战略层（20个文件，原样保留）
│   └── 00-总览.md ~ 19-*.md
├── 02-版本/                               # 版本层（原"02-方案"重组）
│   ├── 00-版本索引.md                     # 版本导航表（更新）
│   ├── governance/                        # 版本治理
│   │   └── version-governance.html        # 版规总章（版规）
│   ├── v3.1/                              # v3.1 归档（已完结）
│   │   ├── README.md                      # 新建：v3.1 归档说明
│   │   └── v3.1-unified-full-spec.html    # 唯一权威（从 16-v3.1-unified-plan/ 移入）
│   └── v3.2/                              # 当前版本（持续更新）
│       └── v3.2-master.html               # 重写为完整独立规格（不引用 v3.1）
├── 03-专项方案/                           # 原02-方案的专项文档（历史演进记录）
│   ├── 00-方案索引.md                     # 新建：方案索引
│   ├── 01-开发架构与差距补全方案.md
│   ├── 02-v1.2-H5重构方案.md
│   ├── 03-v2-错误处理与自动修复方案.md
│   ├── 04-v2.5-整体方案功能梳理.md
│   ├── 05-v2.5-Celery接线升级方案.md
│   ├── 06-v3-完整系统解决方案.md
│   ├── 07-v3-产品升级方案.md
│   ├── 08-迭代归档-真实数据闭环.md
│   ├── 09-竞品池与爆火DNA方案.md
│   ├── 10-AI分析模块升级方案.md
│   ├── 11-找目标模块升级方案.md
│   ├── 12-数据中心改造方案.md
│   ├── 13-视觉验收与修复方案.md
│   ├── 14-找对标/                         # 子目录保留
│   └── 15-v3.1-automation-intelligence-research.md
├── 04-测试/                               # 原03-测试（更新编号）
├── 05-商业化/                             # 原04-商业化（更新编号）
├── 06-配置参考/                           # 原05-配置参考（更新编号）
├── 07-工程/                               # 原06-工程（加入2个根目录 html）
│   ├── design-system/
│   ├── mobile-debug-demo.html             # 从 docs/ 根移入
│   ├── mobile-tools-standard.html         # 从 docs/ 根移入
│   └── ports.md
├── 08-进度/                               # 原07-进度（更新编号）
├── 09-交接/                               # 原08-交接（更新编号）
├── images/                                # 图片（原样保留）
├── video-index.md
└── 99-归档/                               # 深度归档
    └── strategy-旧版/                     # 已有，保留
    （删除 docs/strategy/ 旧版目录）
```

### video-ct/docs/（工程文档，入仓）

```
video-ct/docs/
├── README.md                              # 工程文档导航（重写）
│                                          # 含指向 fire-eye-docs 的产品文档指引
├── 06-工程/                               # 唯一保留的工程文档目录
│   ├── api-contract.md
│   ├── database-schema.md
│   ├── agents-reference.md
│   ├── env-setup-guide.md
│   ├── ports.md
│   ├── mobile-debug-demo.html
│   ├── mobile-tools-standard.html
│   └── design-system/
├── 07-进度/                               # 进度跟踪（代码相关，保留）
├── 08-交接/                               # 交接材料（保留）
├── images/                                # 截图（删除 mp4）
├── video-index.md
└── 99-归档/                               # 保留
    └── strategy-旧版/
```

**删除清单（video-ct/docs）**：
- `docs/01-战略/`（20文件，与 fire-eye-docs 完全重复）
- `docs/02-方案/`（15文件，与 fire-eye-docs 95% 重复）
- `docs/03-测试/`（4文件，与 fire-eye-docs 重复）
- `docs/04-商业化/`（1文件，重复）
- `docs/05-配置参考/`（2文件，重复）
- `docs/images/media/yuefei_zhuxianzhen_20260324_002406.mp4`（违反 R27）
- `docs/superpowers/plans/`（内部计划，不属于业务文档）

---

## Task 1：fire-eye-docs · v3.1 三份合一

**Files:**
- 删除: `Downloads/fire-eye-docs/docs/02-方案/v3.1/`（除 unified-full-spec）
- 删除: `Downloads/fire-eye-docs/docs/02-方案/16-v3.1-unified-plan/`（整个目录）
- 删除: `Downloads/fire-eye-docs/docs/02-方案/历史版本归档/`（整个目录，完全重复）
- 移动: `16-v3.1-unified-plan/v3.1-unified-full-spec.html` → `v3.1/`
- 创建: `Downloads/fire-eye-docs/docs/02-方案/v3.1/README.md`

- [ ] **Step 1：把 unified-full-spec 从 16- 目录移入 v3.1/**

```bash
cp /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/16-v3.1-unified-plan/v3.1-unified-full-spec.html \
   /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/v3.1/v3.1-unified-full-spec.html
```

- [ ] **Step 2：删除 v3.1/ 里的其他文件（只保留 unified-full-spec）**

```bash
cd /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/v3.1/
rm index.html v3.1-geo-generative-engine-optimization.html \
   v3.1-github-project-management.html v3.1-github-resource-research.html \
   v3.1-h5-design-capability-spec.html v3.1-implementation-spec.html \
   v3.1-master.html v3.1-opensource-business-strategy.html
```

- [ ] **Step 3：删除 16-v3.1-unified-plan 整个目录**

```bash
rm -rf /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/16-v3.1-unified-plan/
```

- [ ] **Step 4：删除历史版本归档（完全重复）**

```bash
rm -rf /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/历史版本归档/
```

- [ ] **Step 5：新建 v3.1/README.md 归档说明**

创建 `/Users/metafo/Downloads/fire-eye-docs/docs/02-方案/v3.1/README.md`，内容：

```markdown
# V3.1 归档说明

**状态**: 🔵 已归档 · 2026-05-28 完结

**唯一权威文档**: [v3.1-unified-full-spec.html](v3.1-unified-full-spec.html)

本目录为 V3.1「自动化与智能化」版本的完整归档。
该文档融合了以下专项方案：
- GEO 生成式引擎优化
- H5 设计体系六大能力
- GitHub 项目管理治理
- 开源策略
- Sprint 实施计划（9周·36天）

**归档规则（版规 §八）**: 归档文件只读，不得修改。
后续改动在 V3.2 及以后版本文档中进行。
```

- [ ] **Step 6：验证 v3.1 目录结构**

```bash
ls -la /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/v3.1/
```

Expected:
```
README.md
v3.1-unified-full-spec.html
```

---

## Task 2：fire-eye-docs · 02-方案 重组为 02-版本 + 03-专项方案

**Files:**
- 改名: `02-方案/` → `02-版本/`（保留 v3.1/, v3.2/, governance/, 00-版本索引.md）
- 新建: `03-专项方案/`（存放原 01-15 编号方案）
- 新建: `03-专项方案/00-方案索引.md`
- 移动: `02-版本/` 中的 01-15 方案文件 → `03-专项方案/`
- 移动: `02-版本/v3.2/version-governance.html` → `02-版本/governance/version-governance.html`

- [ ] **Step 1：在 02-方案 内新建 governance 目录并移入版规文档**

```bash
mkdir -p /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/governance
mv /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/v3.2/version-governance.html \
   /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/governance/version-governance.html
```

- [ ] **Step 2：新建 03-专项方案 目录，移入 01-15 方案文件**

```bash
mkdir -p /Users/metafo/Downloads/fire-eye-docs/docs/03-专项方案
# 移动所有数字编号文件（01-15）
cd /Users/metafo/Downloads/fire-eye-docs/docs/02-方案
for f in 0[0-9]-* 1[0-5]-*; do
  [ -e "$f" ] && mv "$f" ../03-专项方案/
done
# 14-找对标 是子目录，单独处理
mv "14-找对标" ../03-专项方案/ 2>/dev/null || true
```

- [ ] **Step 3：验证 02-方案 此时只剩版本相关内容**

```bash
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/
```

Expected:
```
governance/
v3.1/
v3.2/
```

（注：00-版本索引.md 已在 Step 2 移走，这是正确的，后续 Step 5 会处理）

- [ ] **Step 4：把 00-版本索引.md 放回 02-方案（若已被移走）**

```bash
# 如果 00-版本索引.md 被移到了 03-专项方案，移回来
[ -f /Users/metafo/Downloads/fire-eye-docs/docs/03-专项方案/00-版本索引.md ] && \
  mv /Users/metafo/Downloads/fire-eye-docs/docs/03-专项方案/00-版本索引.md \
     /Users/metafo/Downloads/fire-eye-docs/docs/02-方案/00-版本索引.md
```

- [ ] **Step 5：将 02-方案 目录重命名为 02-版本**

```bash
mv /Users/metafo/Downloads/fire-eye-docs/docs/02-方案 \
   /Users/metafo/Downloads/fire-eye-docs/docs/02-版本
```

- [ ] **Step 6：新建 03-专项方案/00-方案索引.md**

创建 `/Users/metafo/Downloads/fire-eye-docs/docs/03-专项方案/00-方案索引.md`，内容：

```markdown
# 专项方案索引

本目录收录 v1.0 → v3.1 各阶段的专项升级方案，为历史演进记录。
当前版本规格请查阅 [02-版本/](../02-版本/00-版本索引.md)。

| 编号 | 方案 | 对应版本 | 状态 |
|------|------|---------|------|
| 01 | 开发架构与差距补全方案 | v1.0 | 🔵 归档 |
| 02 | v1.2 H5 重构方案 | v1.2 | 🔵 归档 |
| 03 | v2 错误处理与自动修复方案 | v2.0 | 🔵 归档 |
| 04 | v2.5 整体方案功能梳理 | v2.5 | 🔵 归档 |
| 05 | v2.5 Celery 接线升级方案 | v2.5 | 🔵 归档 |
| 06 | v3 完整系统解决方案 | v3.0 | 🔵 归档 |
| 07 | v3 产品升级方案 | v3.0 | 🔵 归档 |
| 08 | 迭代归档·真实数据闭环 | v3.0 | 🔵 归档 |
| 09 | 竞品池与爆火 DNA 方案 | v3.0 | 🔵 归档 |
| 10 | AI 分析模块升级方案 | v3.0 | 🔵 归档 |
| 11 | 找目标模块升级方案 | v3.0 | 🔵 归档 |
| 12 | 数据中心改造方案 | v3.0 | 🔵 归档 |
| 13 | 视觉验收与修复方案 | v3.1 | 🔵 归档 |
| 14 | 找对标品类扩展方案 | v3.1 | 🔵 归档 |
| 15 | v3.1 自动化与智能化研究 | v3.1 | 🔵 归档 |
```

- [ ] **Step 7：更新各目录的编号（03→04, 04→05, 05→06, 06→07, 07→08, 08→09）**

```bash
cd /Users/metafo/Downloads/fire-eye-docs/docs
mv 03-测试      04-测试
mv 04-商业化    05-商业化
mv 05-配置参考  06-配置参考
mv 06-工程      07-工程
mv 07-进度      08-进度
mv 08-交接      09-交接
```

- [ ] **Step 8：验证最终 fire-eye-docs/docs 目录列表**

```bash
ls /Users/metafo/Downloads/fire-eye-docs/docs/
```

Expected:
```
README.md        01-战略/    02-版本/    03-专项方案/
04-测试/         05-商业化/  06-配置参考/ 07-工程/
08-进度/         09-交接/    images/     video-index.md
99-归档/         资料索引.md
```

---

## Task 3：fire-eye-docs · v3.2-master.html 重写为独立版本

**背景**：当前 v3.2-master.html 有"一、继承自 V3.1"章节，违反 v3.2 起版本隔离原则。
需重写为自身完整的规格文档：不说"继承"，直接描述 v3.2 的完整功能矩阵。

**Files:**
- 修改: `Downloads/fire-eye-docs/docs/02-版本/v3.2/v3.2-master.html`

- [ ] **Step 1：读取当前 v3.2-master.html 全文**

```bash
cat /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/v3.2/v3.2-master.html
```

（注：路径在 Task 2 完成后已变为 02-版本/v3.2/）

- [ ] **Step 2：重写 v3.2-master.html**

重写原则：
- 去掉"一、继承自 V3.1"章节
- 新的章节结构：

```
一、产品定位与版本目标       ← 本版本要达成什么
二、完整功能矩阵             ← 所有功能（含从 v3.1 沿用的，不说"继承"，直接列）
三、数据库结构（全量）        ← 当前 DB 全量快照
四、API 全量清单              ← 当前 API 全量
五、Sprint 计划（v3.2）       ← 本版本 Sprint
六、发布门槛（Phase Gate）    ← 数据门槛
七、版本代号说明              ← 数据飞轮版
```

重写后的 v3.2-master.html 完整内容如下（基于当前框架扩充）：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<meta name="version" content="v3.2">
<meta name="codename" content="数据飞轮版">
<meta name="status" content="current">
<title>V3.2 数据飞轮版 · 完整规格</title>
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
h3{font-size:14px;font-weight:600;margin:20px 0 8px;color:var(--fg)}
p{margin:6px 0;color:var(--fg2);font-size:13px}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 28px}
.chip{display:inline-flex;align-items:center;padding:3px 10px;border-radius:999px;
  font-size:12px;font-weight:500;background:#f4f4f5;color:var(--fg2);border:1px solid var(--line)}
.chip.g{background:#f0fdf4;color:var(--green);border-color:#bbf7d0}
.chip.o{background:#fff7ed;color:var(--orange);border-color:#fed7aa}
.chip.b{background:#eff6ff;color:var(--blue);border-color:#bfdbfe}
.card{background:#fafafa;border:1px solid var(--line);border-radius:var(--r);
  padding:14px 18px;margin:10px 0}
table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}
th{text-align:left;padding:8px 12px;border-bottom:2px solid var(--line);
  font-weight:600;color:var(--fg2);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
td{padding:8px 12px;border-bottom:1px solid var(--line);color:var(--fg2)}
tr:last-child td{border-bottom:none}
.eyebrow{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--fg3)}
</style>
</head>
<body>
<div class="page">

<div class="eyebrow">Fire-Eye · V3.2 数据飞轮版 · 完整规格</div>
<h1>V3.2 数据飞轮版 · 完整规格</h1>
<div class="meta">
  <span class="chip g">🟢 当前版本</span>
  <span class="chip b">代号：数据飞轮版</span>
  <span class="chip">基线 2026-05-29</span>
  <span class="chip o">唯一权威版本</span>
</div>

<h2>一、产品定位与版本目标</h2>
<div class="card">
  <p><strong>本版本核心目标</strong>：从 AI 主观判断升级为数据实证驱动，建立真实用户数据闭环，打通「采集→分析→报告→商业化」全链路。</p>
  <p><strong>版本代号含义</strong>：「数据飞轮」指通过真实数据积累驱动 AI 精准度持续提升，精准度提升吸引更多用户，形成自增强正反馈。</p>
  <p><strong>Phase Gate 门槛</strong>：进入 v3.2 正式发布需满足 Phase 1（≥500 真实事件/日）。</p>
</div>

<h2>二、完整功能矩阵</h2>
<table>
  <thead><tr><th>功能模块</th><th>子功能</th><th>状态</th><th>说明</th></tr></thead>
  <tbody>
    <tr><td rowspan="4"><strong>视频诊断</strong></td><td>38维·8组诊断报告</td><td>✅</td><td>SSE 5阶段进度推送</td></tr>
    <tr><td>即时数据面板</td><td>✅</td><td>播放/点赞/收藏/转发/评论</td></tr>
    <tr><td>账号诊断</td><td>✅</td><td>账号整体健康度</td></tr>
    <tr><td>诊断重提交</td><td>✅</td><td>失败后重试流程</td></tr>
    <tr><td rowspan="3"><strong>对标系统</strong></td><td>竞品雷达图</td><td>✅</td><td>多维对比可视化</td></tr>
    <tr><td>对标品类扩展</td><td>✅</td><td>跨品类找对标</td></tr>
    <tr><td>爆火 DNA 分析</td><td>🚧</td><td>v3.2 新增</td></tr>
    <tr><td rowspan="3"><strong>用户系统</strong></td><td>微信 OAuth 登录</td><td>✅</td><td></td></tr>
    <tr><td>配额管理</td><td>✅</td><td>免费 3 次/日</td></tr>
    <tr><td>邀请追踪码</td><td>✅</td><td>分销增长引擎</td></tr>
    <tr><td rowspan="3"><strong>商业化</strong></td><td>微信支付</td><td>✅</td><td></td></tr>
    <tr><td>订阅制套餐</td><td>✅</td><td>月/季/年</td></tr>
    <tr><td>优惠券系统</td><td>✅</td><td></td></tr>
    <tr><td rowspan="2"><strong>AI 引擎</strong></td><td>LLM 路由</td><td>✅</td><td>多模型降级策略</td></tr>
    <tr><td>Agent 编排</td><td>✅</td><td>8个专项 Agent</td></tr>
    <tr><td rowspan="2"><strong>数据采集</strong></td><td>TikHub API 接入</td><td>✅</td><td></td></tr>
    <tr><td>事件埋点系统</td><td>🚧</td><td>v3.2 重点，Phase Gate 前置</td></tr>
    <tr><td rowspan="2"><strong>运营工具</strong></td><td>管理后台</td><td>✅</td><td>Admin 端</td></tr>
    <tr><td>顾问工作台</td><td>✅</td><td>Consultant 端</td></tr>
    <tr><td rowspan="2"><strong>成长档案</strong></td><td>历史诊断归档</td><td>✅</td><td></td></tr>
    <tr><td>精度等级体系</td><td>✅</td><td>🌿萌芽→ 成熟 5级</td></tr>
  </tbody>
</table>

<h2>三、数据库结构（全量快照）</h2>
<div class="card">
  <p>详细 Schema 见工程文档：<code>video-ct/docs/06-工程/database-schema.md</code></p>
  <p><strong>核心表</strong>：users · diagnoses · video_metrics · benchmarks · personas · subscriptions · coupons · referrers · archive · event_log · positioning</p>
  <p><strong>v3.2 新增</strong>：event_log 表扩展（埋点字段增加）</p>
</div>

<h2>四、API 全量清单</h2>
<div class="card">
  <p>详细 API 合约见工程文档：<code>video-ct/docs/06-工程/api-contract.md</code></p>
  <h3>核心路由前缀</h3>
  <table>
    <thead><tr><th>前缀</th><th>模块</th><th>端点数</th></tr></thead>
    <tbody>
      <tr><td>/api/auth</td><td>微信 OAuth + JWT</td><td>4</td></tr>
      <tr><td>/api/diagnosis</td><td>视频诊断</td><td>6</td></tr>
      <tr><td>/api/benchmark</td><td>对标系统</td><td>5</td></tr>
      <tr><td>/api/persona</td><td>人设定位</td><td>4</td></tr>
      <tr><td>/api/subscription</td><td>订阅/支付</td><td>8</td></tr>
      <tr><td>/api/users</td><td>用户管理</td><td>5</td></tr>
      <tr><td>/api/admin</td><td>管理后台</td><td>12</td></tr>
      <tr><td>/api/events</td><td>埋点事件</td><td>3</td></tr>
      <tr><td>/api/ai</td><td>AI 直接交互</td><td>2</td></tr>
      <tr><td>/ws</td><td>WebSocket 实时推送</td><td>1</td></tr>
    </tbody>
  </table>
</div>

<h2>五、Sprint 计划</h2>
<div class="card">
  <p><!-- 待 Sprint 开始后填充具体任务，参考版规 §九 路线图 --></p>
  <p><strong>Sprint 1 焦点</strong>：事件埋点系统上线，达到 Phase 1 门槛（≥500 事件/日）</p>
  <p><strong>Sprint 2 焦点</strong>：爆火 DNA 分析模块，MAU 增长至 500+</p>
</div>

<h2>六、发布门槛（Phase Gate）</h2>
<div class="card">
  <table>
    <thead><tr><th>Phase</th><th>门槛</th><th>解锁功能</th></tr></thead>
    <tbody>
      <tr><td>Phase 1</td><td>≥ 500 真实事件/日</td><td>数据仪表盘 · 精度等级进化</td></tr>
      <tr><td>Phase 2</td><td>≥ 10,000 次 adoption</td><td>爆火 DNA · 竞品智能推荐</td></tr>
      <tr><td>Phase 3</td><td>MAU ≥ 500 + 月收 ¥5,000</td><td>企业版 · 白标授权</td></tr>
    </tbody>
  </table>
  <p>Phase Gate 实现：<code>video-ct/services/api/app/core/phase_gate.py</code></p>
</div>

<h2>七、版本代号说明</h2>
<div class="card">
  <p><strong>代号</strong>：数据飞轮版</p>
  <p><strong>含义</strong>：真实数据积累→ AI 精准度提升→ 吸引更多用户→ 更多数据，形成自增强正反馈回路。</p>
  <p><strong>版本治理</strong>：版号由 release-please 自动生成，窗口禁止手动指定。版规详见 <a href="../governance/version-governance.html">version-governance.html</a>。</p>
</div>

<hr style="border:none;border-top:1px solid var(--line);margin:32px 0">
<p style="font-size:11px;color:var(--fg3);text-align:center">
  V3.2 数据飞轮版 · 生成 2026-05-29 · 唯一权威版本 · 本文档自身完整，不引用其他版本
</p>
</div>
</body>
</html>
```

- [ ] **Step 3：验证重写后的文档结构**

```bash
grep -n "<h2" /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/v3.2/v3.2-master.html
```

Expected（不应出现"继承"字样）:
```
一、产品定位与版本目标
二、完整功能矩阵
三、数据库结构（全量快照）
四、API 全量清单
五、Sprint 计划
六、发布门槛（Phase Gate）
七、版本代号说明
```

```bash
grep "继承\|inherit" /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/v3.2/v3.2-master.html
```

Expected: 无输出（不含继承引用）

---

## Task 4：fire-eye-docs · 清理杂项

**Files:**
- 删除: `Downloads/fire-eye-docs/docs/strategy/`（旧版，video-ct/docs/99-归档 已有）
- 移动: `Downloads/fire-eye-docs/docs/mobile-debug-demo.html` → `07-工程/`
- 移动: `Downloads/fire-eye-docs/docs/mobile-tools-standard.html` → `07-工程/`
- 更新: `Downloads/fire-eye-docs/docs/02-版本/00-版本索引.md`
- 重写: `Downloads/fire-eye-docs/docs/README.md`

- [ ] **Step 1：删除 strategy/ 旧版目录**

```bash
rm -rf /Users/metafo/Downloads/fire-eye-docs/docs/strategy/
```

- [ ] **Step 2：移动根目录 html 到 07-工程/**

```bash
mv /Users/metafo/Downloads/fire-eye-docs/docs/mobile-debug-demo.html \
   /Users/metafo/Downloads/fire-eye-docs/docs/07-工程/
mv /Users/metafo/Downloads/fire-eye-docs/docs/mobile-tools-standard.html \
   /Users/metafo/Downloads/fire-eye-docs/docs/07-工程/
```

- [ ] **Step 3：更新版本索引**

将 `02-版本/00-版本索引.md` 内容更新为：

```markdown
# 版本索引

| 版本 | 状态 | 主文档 | 代号 | 发布日期 |
|------|------|-------|------|---------|
| v3.2 | 🟢 当前 | [v3.2-master.html](v3.2/v3.2-master.html) | 数据飞轮版 | 2026-05-29 |
| v3.1 | 🔵 归档 | [v3.1-unified-full-spec.html](v3.1/v3.1-unified-full-spec.html) | 自动化与智能化版 | 2026-05-28 |

版本治理规则：[版规总章](governance/version-governance.html)
```

- [ ] **Step 4：重写 docs/README.md（全局导航）**

```markdown
# Fire-Eye 产品文档

> 此目录为 fire-eye/video-ct 产品文档主库（离仓存储）。
> 工程文档（API/DB/部署）请查阅 video-ct 仓库 docs/06-工程/。

## 目录导航

| 目录 | 内容 | 说明 |
|------|------|------|
| [01-战略/](01-战略/) | 战略层文档 | 竞品分析、商业模式、增长飞轮 |
| [02-版本/](02-版本/) | 版本规格 | 当前/归档版本完整规格 + 版规总章 |
| [03-专项方案/](03-专项方案/) | 历史专项方案 | v1.0→v3.1 各阶段升级方案（归档） |
| [04-测试/](04-测试/) | 测试文档 | 自动化测试方案、E2E 修复实录 |
| [05-商业化/](05-商业化/) | 商业化 | H5 商业化功能开源方案 |
| [06-配置参考/](06-配置参考/) | 配置参考 | Proxy 配置、模型清单 |
| [07-工程/](07-工程/) | 工程文档 | 移动端调试、设计系统、端口规划 |
| [08-进度/](08-进度/) | 进度追踪 | 上线评估、缺失项、版本审计 |
| [09-交接/](09-交接/) | 交接材料 | 交接清单、环境配置 |
| [99-归档/](99-归档/) | 深度归档 | 不再维护的历史文档 |

## 版本快速入口

- **当前版本**：[V3.2 数据飞轮版](02-版本/v3.2/v3.2-master.html)
- **归档版本**：[V3.1 自动化与智能化版](02-版本/v3.1/v3.1-unified-full-spec.html)
- **版规总章**：[version-governance.html](02-版本/governance/version-governance.html)
```

- [ ] **Step 5：验证 fire-eye-docs/docs 根目录干净**

```bash
ls /Users/metafo/Downloads/fire-eye-docs/docs/
```

Expected：无散落的 html 文件，只有目录和 README.md、video-index.md、资料索引.md

---

## Task 5：video-ct/docs · 删除重复内容，精简为工程文档

**Files:**
- 删除: `docs/01-战略/`（20文件，与 fire-eye-docs 完全重复）
- 删除: `docs/02-方案/`（与 fire-eye-docs 重复，无版本目录）
- 删除: `docs/03-测试/`（重复）
- 删除: `docs/04-商业化/`（重复）
- 删除: `docs/05-配置参考/`（重复）
- 删除: `docs/images/media/yuefei_zhuxianzhen_20260324_002406.mp4`（违反 R27）
- 移动: `docs/superpowers/plans/` → `.claude/plans/`
- 重写: `docs/README.md`

- [ ] **Step 1：删除与 fire-eye-docs 重复的目录**

```bash
cd /Users/metafo/Projects/fire-eye/video-ct/docs
rm -rf 01-战略/ 02-方案/ 03-测试/ 04-商业化/ 05-配置参考/
```

- [ ] **Step 2：删除违规 mp4 视频并记录到 video-index.md**

```bash
rm /Users/metafo/Projects/fire-eye/video-ct/docs/images/media/yuefei_zhuxianzhen_20260324_002406.mp4
```

在 `docs/video-index.md` 追加记录（执行者手动补充，记录视频本地路径）

- [ ] **Step 3：移动 superpowers/plans 到 .claude/plans**

```bash
mkdir -p /Users/metafo/Projects/fire-eye/video-ct/.claude/plans
mv /Users/metafo/Projects/fire-eye/video-ct/docs/superpowers/plans/* \
   /Users/metafo/Projects/fire-eye/video-ct/.claude/plans/
rm -rf /Users/metafo/Projects/fire-eye/video-ct/docs/superpowers/
```

- [ ] **Step 4：重写 docs/README.md**

```markdown
# video-ct 工程文档

> 本目录为入仓工程文档，随代码版本管理。
> 产品文档（战略/方案/版本规格）存于 fire-eye-docs（离仓）。

## 目录

| 目录 | 内容 |
|------|------|
| [06-工程/](06-工程/) | API 合约、DB Schema、Agent 参考、开发环境、端口规划、移动端调试 |
| [07-进度/](07-进度/) | 上线前评估、缺失项总览、测试覆盖现状 |
| [08-交接/](08-交接/) | 交接清单、环境配置、部署说明 |
| [99-归档/](99-归档/) | 历史归档（strategy 旧版等） |

## 产品文档入口

产品文档存于本地 `~/Downloads/fire-eye-docs/docs/`（不入仓）：
- [版本索引](~/Downloads/fire-eye-docs/docs/02-版本/00-版本索引.md)
- [战略文档](~/Downloads/fire-eye-docs/docs/01-战略/)
```

- [ ] **Step 5：验证 video-ct/docs 精简结果**

```bash
ls /Users/metafo/Projects/fire-eye/video-ct/docs/
```

Expected:
```
06-工程/   07-进度/   08-交接/   images/
99-归档/   README.md  video-index.md  资料索引.md
```

- [ ] **Step 6：commit 清理结果**

```bash
cd /Users/metafo/Projects/fire-eye/video-ct
git add -A
git commit -m "docs: 精简 video-ct/docs 为纯工程文档，移除与 fire-eye-docs 重复内容"
```

---

## Task 6：最终验证

- [ ] **Step 1：验证版本文档完整性**

```bash
# v3.1 只有唯一文件
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/v3.1/
# Expected: README.md  v3.1-unified-full-spec.html

# v3.2 完整存在
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/v3.2/
# Expected: v3.2-master.html

# 版规存在
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/governance/
# Expected: version-governance.html
```

- [ ] **Step 2：验证 v3.2 无继承引用**

```bash
grep -i "继承\|inherit\|来自 V3.1\|来自v3.1" \
  /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/v3.2/v3.2-master.html
# Expected: 无输出
```

- [ ] **Step 3：验证无重复目录**

```bash
# fire-eye-docs 不应有 strategy/ 旧版
ls /Users/metafo/Downloads/fire-eye-docs/docs/strategy/ 2>&1
# Expected: No such file or directory

# fire-eye-docs 不应有 16-v3.1-unified-plan/
ls /Users/metafo/Downloads/fire-eye-docs/docs/02-版本/16-v3.1-unified-plan/ 2>&1
# Expected: No such file or directory

# video-ct/docs 不应有 01-战略
ls /Users/metafo/Projects/fire-eye/video-ct/docs/01-战略/ 2>&1
# Expected: No such file or directory
```

- [ ] **Step 4：更新 MEMORY.md 中版规路径（因目录改名）**

版规路径从 `02-方案/v3.2/version-governance.html` 变为 `02-版本/governance/version-governance.html`，
更新 fire-eye 项目 memory 中的 `ref-version-governance.md`。

- [ ] **Step 5：最终 commit**

```bash
cd /Users/metafo/Projects/fire-eye/video-ct
git add -A
git commit -m "docs: 完成文档目录重塑 - 版本隔离 + 精简双轨 + v3.2 独立规格"
```

---

## 自检：规格覆盖

| 用户要求 | 对应任务 |
|---------|---------|
| v3.1 保留 unified-full-spec.html 一个文件 | Task 1 |
| v3.2 起版本隔离，不引用其他版本 | Task 3（重写 v3.2-master.html） |
| 文件夹重塑，补充完整 | Task 2（02-方案→02-版本+03-专项） |
| 该合并的合并 | Task 1（三份→一份）、Task 4（编号重排） |
| 该删除的删除 | Task 1（历史版本归档）、Task 4（strategy旧版）、Task 5（重复目录）|
| 逻辑性·次序·顺序·完整度 | Task 2（编号重排）、Task 4（README+版本索引）|
