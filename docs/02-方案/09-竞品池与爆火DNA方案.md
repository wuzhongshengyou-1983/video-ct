# 火眼金睛 · 竞品池与爆火 DNA 方案

> 落地日期：2026-05-19 · 触发原因：基因访谈设定美容但匹配出美食 + 竞品页无同行业博主

---

## 一、Bug 根因（已确认）

**前端存的是英文 value，后端模板 key 是中文**。

| 位置 | 现状 | 问题 |
|---|---|---|
| `gene-interview.html:119` | `{v:'beauty', l:'美妆护肤'}` 存 `state.answers.industry='beauty'` | 存的是机器值 |
| 前端发送 | `body: {profile: state.geneProfile}` 含 `industry='beauty'` | 原样传英文 v |
| `server.js:2596` L1 远程 | `extract.py --search "beauty"` | 中文平台搜不到 |
| `server.js:2626` L2 知识库 | `description.indexOf('beauty')` | 中文 desc 不含英文 → fallback 全量按 confidence 排 → 美食类 evidence 最高 → **吐出美食结果** |
| `server.js:2782` L3 模板 | `templates['beauty']` undefined → default | 美容→default 综合占位 |
| `competitor-analysis.html:232` | `var indLabel = state.geneProfile.industry` | 顶部显示 'beauty' 不是 '美妆护肤' |

---

## 二、修复 + 扩展方案（P0~P5）

### P0 字段语义统一

- 前端 `saveToServer` / `autoMatch` 时附加 `industry_label`
- 后端优先用 `industry_label || mapVtoL(industry)` 做匹配
- 前端 reminder 显示走 `findLabel()`

### P1 行业池 5→50 + 模板 key 改中文

每个 industry 准备 50 个博主三档分层（**Top10 头部 + Mid20 腰部 + Long20 新锐**），覆盖：
美妆护肤 / 美食 / 知识教育 / 科技数码 / 时尚穿搭 / 健身运动 / 母婴亲子 / 旅游 / 职场成长 / 汽车 / 搞笑娱乐 / 三农 / 剧情 / 萌宠 / 游戏

### P2 API 契约

```
POST /api/fire-eye/competitors/match
Body: {
  profile,                  // 含 industry + industry_label
  refresh_token,            // 同次会话稳定
  offset: 0,
  size: 5,
  exclude_ids: []
}
Response: {
  ok, competitors[5], total_pool, cursor:{offset, has_more}, source
}
```

### P3 7 维评分 + viral_score 因子归因

```
viral_score = 0.32*hook + 0.24*density + 0.18*trust + 0.14*algo + 0.12*monetize
```

每竞品返回 `top_factors: [{name, contribution_pct, evidence}]`

### P4 F-Frame 时间轴 UI

```
0-3s  钩子    | 3-8s 密度  | 8-20s 转折 | 20-45s 高潮 | 结尾 CTA
[★91 数字承诺]  [★78 6cut/s] [★85 反差]   [★88 极限]    [★82 短路径]
```

7 维雷达 + Top 5 贡献因子百分比 + 你能抄 / 别抄 / 改造 / 超越点。

### P5 TikHub Tier-A 数据源接入桩

需 API key，按 memory「不静默降级」：未配置时返回 `source: 'template'` 并在 UI 明示「估算池，建议配置 TIKHUB_API_KEY 启用真榜单」。

---

## 三、数据源降级链

```
Tier-A: TikHub /douyin/search/general → 真实榜单
   ↓ 未配置/失败
Tier-B: 本地 KB SQLite patterns（带 industry_zh 字段）
   ↓ 空
Tier-C: 行业种子表 50 个 / 行业（人工标注 + 6 维评分卡）
```

---

## 四、验收清单

- [x] 选「美妆护肤」→ 匹配出美妆 KOL，非美食
- [x] 顶部赛道徽章显示中文 label
- [x] 「换一批」按钮每次刷出 5 个未见过的
- [x] 每个竞品展开看到 7 维雷达 + Top 5 因子百分比
- [x] 50 个看完后提示「重新洗牌」
- [x] 有/无 TikHub key 状态在 UI 明示（真实/估算徽章）

---

## 五、迭代日志（2026-05-19 全部落地）

### 迭代 1 — P0~P5 首次落地
- 新建 `xiaosheng-server/data/industry-pool.js`：19 行业字典 + 150 头部真实种子 + 程序化扩展到 50/行业
- server.js `/api/fire-eye/competitors/match` 改池化+分页+7维归因，删旧 `getIndustryTemplateCompetitors`
- 前端 gene-interview / competitor-analysis 统一 v↔label，加「换一批/重新洗牌」、7维雷达 SVG、Top5因子进度条、F-Frame 时间轴
- sort 改 tier 优先（头部>腰部>新锐）

### 迭代 2 — 三项待补
- **TikHub 真接入**：key 在 `~/999/tools/video-extractor/.env`；server.js 加轻量 .env 加载器（无 dotenv 依赖）；正确端点 `POST /api/v1/douyin/search/fetch_general_search_v1`（原桩路径 404）
- **industry 解析统一**：fire-eye.js 不涉及；index.html 是静态 demo；后端消费点（gene-interview 存档 + breakdown）统一 `resolveIndustry`，持久化 industry(v)+industry_label(中文)
- **进程持久化**：新建 `ecosystem.config.js`，nohup → pm2 托管（autorestart，已 pm2 save）

### 迭代 3 — 富化 + 排序失真 + 性能
- **真实粉丝富化**：`handler_user_profile`（非 v2/v3）拿真实 follower_count，`fans_estimated` 标记如实显示
- **排序失真修复**（根因+解法）：TikHub 搜索 API 不返回 play_count(=0)，原 `engagement=like/follower` 比率法让小号虚高、头部沉底 → `is_tikhub` 分支改用**绝对量级** log 映射（点赞/转发/粉丝绝对量）；骆王宇 1520万粉 viral 58→82 回第1
- **双层缓存**：`TIKHUB_FANS_CACHE`（sec_uid→粉丝, TTL 1h）+ `TIKHUB_POOL_CACHE`（行业+词→富化池, TTL 10min）；冷 9s → 热 0.002s（4500×），翻页/换一批秒回

### 关键文件清单
| 文件 | 角色 |
|---|---|
| `xiaosheng-server/data/industry-pool.js` | 行业字典 + 50/行业种子池 |
| `xiaosheng-server/server.js` | match/breakdown 端点 + TikHub 接入 + 双层缓存 + 7维评分 + v2 三模块原生实现 |
| `xiaosheng-server/ecosystem.config.js` | pm2 进程托管 |
| `ruyi-h5/gene-interview.html` | v↔label 双传 |
| `ruyi-h5/competitor-analysis.html` | 池化分页 UI + 7维雷达 + F-Frame |
| `ruyi-h5/js/app.js` | 前端智变推荐 3 模块渲染（证据驱动 UI） |
| `xiaosheng-shared/fire-eye.json` | 五端单一真相源 v1.2.0（含 v2 三端点） |

### 迭代 4 — 智变推荐 3 模块全重写（证据驱动，去硬编码占位）
- **架构变更**：删除 `_proxyV2`（向 Python 8701 代理）、`getIndustryTemplateCompetitors`（硬编码模板）、`buildCompetitorEntry`（旧占位函数）；v2 三模块改为 server.js 原生实现
- **模块1 爆款基因复刻** (`v2/replicate`)：`extractEvidence()` 解析真实诊断报告（转写/情绪曲线/流失点），8 维基因每项带 `evidence` + `why` + `transfer`；`biggestDropOff()` 找真实完播最大跌幅点；`why_viral` 用真实数字归因（非通用模板）；`next_video_brief` 绑定真实 climax 时刻
- **模块2 二创剧本工坊** (`v2/remix`)：AI 生成替代原「减脂餐」硬编码占位；抽取真实视频骨架（按 tag 合并分段）→ `callSiliconAI('chat')` 用 DeepSeek-V4-Flash 生成行业适配脚本；`robustJsonParse()` 状态机处理 AI 返回的 markdown  fence / 内嵌换行 / 尾部逗号；输出 segments 每项含 stage/duration/function/new_script/shot/why
- **模块3 全网选题侦察** (`v2/topics`)：TikHub 实时热搜聚合替代规则池占位；真实 `like_count/comment_count/share_count` 驱动 hotness 评分；每条选题带 `why_hot`（引用真实互动量）/ `how_to`（赛道适配建议）/ `risk`（竞争预警）；降级池明示「⚠️ 规则估算」
- **前端渲染** (`ruyi-h5/js/app.js`)：`_renderReplicate` 证据徽章+why_viral+gene grid+persuasion_note；`_renderRemix` AI 生成徽章+why_keep_structure/viral_logic+segment shot/why；`_renderTopics` 真实数据徽章+honesty meta+real likes/comments/shares+source_url 链接；新增 `_evidenceBadge(level)`
- **fire-eye.json 同步**：`api_endpoints` 新增 `v2_replicate`/`v2_remix`/`v2_topics` 三条，标注 native

### 已知限制（非阻塞，留待后续）
- TikHub `general_search` 不返回 play_count，单条互动率靠估算；要更精准需逐视频 detail（额外计费）
- 富化固定 Top12；冷启动首次仍需 ~9s（外部 API 固有延迟）
- 模块2 remix 依赖 smart-proxy:7070（SiliconFlow → DeepSeek-V4-Flash），不可用时返回 502（不编造占位）
