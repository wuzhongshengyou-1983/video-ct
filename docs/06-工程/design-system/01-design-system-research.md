# video-ct 设计系统研究报告 v1.0

> **产品**：video-ct · 短视频 CT 诊断 SaaS  
> **技术栈**：Vue3 + Vant4 + TypeScript  
> **定位**：极简白色科技风 · 医学影像感 · 「像 Linear + Apple 体检报告」  
> **输出日期**：2026-05-28  
> **作者**：元帅设计研究

---

## 模块 1.1：开源设计系统对比调研

---

### 候选组 A：移动端组件库

---

#### A1. Vant 4（@vant-ui/vant，已在用）

- **GitHub**：https://github.com/youzan/vant
- **文档**：https://vant-ui.github.io/vant/
- **核心设计原则**：轻量、简洁、移动优先；基于 CSS 变量的主题系统；组件与业务解耦

**可融合优点（具体可执行）**：
1. CSS 变量完整覆盖：`--van-*` 命名空间，650+ token，全部可通过 `:root` 覆盖，无需 fork
2. 原生支持 `configProvider` 组件，运行时动态切换主题，适合 A/B 测试金色方案
3. `Toast`/`Notify` 组件内置 `lockScroll`，微信 WebView 滚动穿透已处理
4. `List` 组件内置虚拟滚动 + 无限加载，数据列表页零成本
5. 所有触摸区域默认 44px 最小高度（符合 Apple HIG），无需额外处理

**不适用原因**：
- 视觉风格偏"淘系电商"（橙色、圆润、大字），需全量覆盖 token 才能达到极简科技风
- 没有数据可视化组件（分数仪表盘/趋势图），需自行实现
- 图标库（vant-icons）风格偏圆润，不符合极简线条风，需替换

---

#### A2. NutUI（京东出品）

- **GitHub**：https://github.com/jdf2e/nutui
- **文档**：https://nutui.jd.com/
- **核心设计原则**：京东视觉规范延伸；B 端/C 端均有组件；支持多端（H5/小程序）

**可融合优点（具体可执行）**：
1. `Rate` 评分 + `CircleProgress` 环形进度条组件质量高，直接用于诊断分数展示
2. `Skeleton` 骨架屏支持 `animated` 波浪效果，医学"扫描感"极强
3. `Swipe` 横滑组件支持卡片式切换，适合多维度诊断结果展示
4. `Steps` 步进组件支持竖排 + 自定义 icon，可用于诊断流程时间轴

**不适用原因**：
- 主题色强绑定京东红，覆盖成本高于 Vant
- 与 Vant 同时使用存在 CSS 命名冲突风险，且打包体积翻倍
- 文档中英文混排质量差，社区维护活跃度低于 Vant

**结论**：不引入，仅参考 `CircleProgress` 组件实现思路

---

#### A3. Arco Design Mobile（字节跳动）

- **GitHub**：https://github.com/arco-design/arco-design-mobile
- **文档**：https://arco.design/mobile/
- **核心设计原则**：iOS/Android 原生感；高保真交互；支持 React/Vue

**可融合优点（具体可执行）**：
1. `Progress` 组件支持 `type="circle"` + 渐变色，视觉精度高，适合健康分圆环
2. 动效体系完整：Arco 内置 `@arco-design/mobile-utils` 动效工具，spring 参数可借用
3. 卡片投影系统（3 级 elevation）参数精准，可直接提取数值

**不适用原因**：
- Vue 版本维护度不足（主要维护 React 版），Vue3 issues 响应慢
- 字节设计语言偏"今日头条感"，极简科技风距离较远
- 体积大（~180KB gzip），WebView 首屏加载有压力

**结论**：不引入，仅提取 elevation 和 circle-progress 参数

---

### 候选组 B：设计规范参考

---

#### B1. Apple HIG（Human Interface Guidelines）

- **文档**：https://developer.apple.com/design/human-interface-guidelines/
- **核心设计原则**：清晰（Clarity）、顺从（Deference）、深度（Depth）；触摸目标最小 44×44pt

**可融合优点（具体可执行）**：
1. **触摸目标铁律 44×44pt**：所有可点击元素视觉尺寸可小，触摸区域必须 ≥44px（透明扩展）
2. **动态字体比例**：iOS SF Pro 的 6 级字体层级（Large Title 34/Title 28/Headline 17/Body 17/Callout 16/Caption 12）可直接映射到本产品 H1~Caption
3. **安全区域（Safe Area）**：微信 WebView 需处理 `env(safe-area-inset-bottom)`，HIG 给出了准确处理方式
4. **导航栏高度 44pt**：对应 CSS 44px，固定导航不遮挡内容
5. **弹出菜单 cornerRadius 13pt**：对应 13px，系统弹窗圆角参照

**不适用原因**：
- 基于 pt 单位（需换算）；颜色系统基于 iOS 系统色（与品牌金色冲突需忽略）
- 部分规则（如 Sidebar）仅适用 iPadOS，移动端 H5 不适用

---

#### B2. Google Material Design 3

- **文档**：https://m3.material.io/
- **核心设计原则**：Material You 个性化；动态色彩系统；Tonal surface

**可融合优点（具体可执行）**：
1. **色彩角色系统**（Color Role）：Primary/Secondary/Tertiary/Error + 各自 Container/On 共 12 个语义色，比直接用十六进制更系统化
2. **Motion 规范（M3 Expressive）**：4 种 easing：`emphasized`(cubic-bezier(0.2,0,0,1.0)) / `emphasizedDecelerate`(0.05,0.7,0.1,1.0) / `emphasizedAccelerate`(0.3,0,0.8,0.15) / `standard`(0.2,0,0,1.0)，可直接移植
3. **Elevation Tonal 系统**：不用 box-shadow，用背景色叠加 Primary 透明度（5%/8%/11%/12%/14%）模拟层级，纯白背景下更优雅
4. **Typography Scale 精确**：`displayLarge` 57/40pt → `labelSmall` 11/16pt，完整 15 级，可精简后用
5. **State Layer 规范**：hover 8% / pressed 12% / focused 12% / dragged 16%，交互反馈精确到百分比

**不适用原因**：
- 动态色彩（Material You）强依赖 Android 系统，H5 无法使用
- M3 组件库（Web）体积庞大且与 Vant 冲突
- Roboto/Noto 字体与产品中文科技感不符

---

#### B3. Linear App Design 原则

- **参考**：https://linear.app / Linear 官方设计 talk
- **核心设计原则**：高密度信息密度；极度克制的色彩（几乎只用黑白灰）；快速响应的交互

**可融合优点（具体可执行）**：
1. **信息密度优先**：行高 1.4（非 1.6/1.8），字号最小 11px 使用（不因"可读性"无限放大），单屏信息量最大化
2. **颜色极度克制**：除 1 个 accent 色，其余全部灰度；accent 仅用于最重要 1 个 CTA 和最重要状态
3. **1px 线条分割**：用 `border: 1px solid rgba(0,0,0,0.06)` 替代阴影，比 box-shadow 更轻
4. **hover 背景**：`rgba(0,0,0,0.04)` 轻触反馈，不改变边框不改变颜色
5. **字重层级**：仅用 400/500/600 三个字重（不用 300 不用 700+），层级靠字号差和透明度，不靠加粗

**不适用原因**：
- 纯桌面端设计，没有移动端触摸区域考量
- 过于克制的动效（几乎无动画）对 H5 体验偏生硬

---

### 候选组 C：白色系极简参考

---

#### C1. Vercel Design（vercel.com）

- **参考**：https://vercel.com/design
- **核心设计原则**：纯白背景；Geist 字体；功能即美学；无装饰，零视觉噪音

**可融合优点（具体可执行）**：
1. **背景层级 3 级**：`#ffffff`（主）→ `#fafafa`（卡片）→ `#f5f5f5`（内嵌块），不用阴影分层
2. **分割线 `#eaeaea`（1px）**：比 Material 的 `rgba(0,0,0,0.12)` 更干净，无颜色偏差
3. **Geist Sans 数字等宽**：数字对齐无需额外 `font-variant-numeric: tabular-nums`
4. **链接无下划线**：只靠颜色区分，hover 加 0.5px 下划线，极简
5. **错误/成功 chip**：背景 `#fef2f2` 文字 `#dc2626`（error），纯色无阴影，信息清晰

**不适用原因**：
- Geist 字体仅英文优化，中文 fallback 到系统字体，混排时字重不一致
- 桌面端高密度在 375px 宽度下可能过挤，需适配手机

---

#### C2. Stripe Dashboard Design

- **参考**：https://stripe.com/blog/designing-accessible-color-systems
- **核心设计原则**：专业金融感；数据优先；高可读性；可访问性优先（WCAG AA）

**可融合优点（具体可执行）**：
1. **表格/列表行高 48px**：比普通 40px 多 8px，扫读更舒适，不会太"密"
2. **数据标签（Label）全大写 + letter-spacing 0.05em**：专业感，用于分类标签 / 章节标题
3. **Badge 系统**：圆角 100px（pill）+ 小字 11px + 字重 500，状态标签统一规范
4. **空状态（Empty State）设计**：居中图标（40px）+ 标题 + 描述 + CTA，三件套模板固化
5. **数字颜色系统**：正值 `#10b981`（绿）负值 `#ef4444`（红），不用"上涨红下跌绿"（国际化友好）

**不适用原因**：
- Stripe 色彩系统为蓝紫色调（Stripe purple #635bff），与金色品牌色偏差大
- 桌面端高密度设计，列宽逻辑在手机单列布局下无需参考

---

#### C3. Raycast Design System

- **参考**：https://www.raycast.com/blog/how-raycast-uses-design-tokens
- **核心设计原则**：极简精准；键盘优先；Spotlight 感；深色/浅色无缝切换

**可融合优点（具体可执行）**：
1. **Token 命名规范**：`--raycast-primary-text` / `--raycast-secondary-text` 语义命名，可直接借鉴命名体系
2. **模糊背景（backdrop-filter blur）**：`backdrop-filter: blur(20px) saturate(180%)`，用于浮层/底部弹窗背景，科技感强
3. **列表项悬停 + 选中**：`border-radius: 8px` + `background: rgba(255,255,255,0.08)`（暗色）/ `rgba(0,0,0,0.04)`（亮色），精确
4. **键盘快捷键 Badge**：`font-family: 'SF Mono', monospace; font-size: 11px; padding: 2px 5px; border-radius: 4px; border: 1px solid`，可用于「快捷操作」标签

**不适用原因**：
- 主要为 macOS 桌面 app，深色模式为主，移植到白色 H5 需大量反转
- blur 效果在低端安卓 WebView 有性能问题，需降级方案

---

### 融合优点清单（20 条 · 每条含具体参数）

| # | 来源 | 融合优点 | 具体参数 |
|---|------|---------|---------|
| 1 | Apple HIG | 触摸目标最小保障 | 所有可点击元素触摸区域 ≥44×44px（透明 padding 扩展） |
| 2 | Apple HIG | 安全区域处理 | `padding-bottom: env(safe-area-inset-bottom, 16px)` 所有固定底栏必加 |
| 3 | Apple HIG | 字体层级比例 | 主体字 16px → 标题差 1.5x 递增（16/20/24/28/34px） |
| 4 | M3 | Motion easing 参数 | 入场：`cubic-bezier(0.05,0.7,0.1,1.0)`；退场：`cubic-bezier(0.3,0,0.8,0.15)` |
| 5 | M3 | State Layer 交互反馈 | hover `rgba(0,0,0,0.04)` / pressed `rgba(0,0,0,0.10)` / focused `rgba(0,0,0,0.10)` |
| 6 | M3 | 语义色角色系统 | Primary/Surface/Error + Container/On 双色对，共 12 个语义 token |
| 7 | Linear | 信息密度行高 | `line-height: 1.4`（正文）/ `1.2`（标题），不用 1.6+ |
| 8 | Linear | 颜色极度克制 | 全站仅 1 个 accent（品牌金 `#f59e0b`），其余 100% 灰度系 |
| 9 | Linear | 1px 线条分割代替阴影 | `border: 1px solid rgba(0,0,0,0.07)` 优先于 `box-shadow` |
| 10 | Linear | 字重仅 3 档 | 400（正文）/ 500（强调）/ 600（标题/按钮），不用 300/700+ |
| 11 | Vercel | 背景 3 级无阴影分层 | `#ffffff`→`#fafafa`→`#f5f5f5`，层级靠背景色差，不靠 shadow |
| 12 | Vercel | 分割线色值 | `#eaeaea`（默认）/ `#e5e5e5`（强调），1px solid |
| 13 | Vercel | Error/Success chip 配色 | Error: bg`#fef2f2` fg`#dc2626`；Success: bg`#f0fdf4` fg`#16a34a` |
| 14 | Stripe | 数据行高 48px | 列表单行高度 48px，比通用 40px 增 8px，扫读更舒适 |
| 15 | Stripe | Label 全大写样式 | `text-transform: uppercase; letter-spacing: 0.05em; font-size: 11px; font-weight: 500` |
| 16 | Stripe | 状态 Badge 规范 | `border-radius: 100px; padding: 2px 8px; font-size: 11px; font-weight: 500` |
| 17 | Raycast | 浮层毛玻璃背景 | `backdrop-filter: blur(20px) saturate(180%); background: rgba(255,255,255,0.85)` |
| 18 | Vant 4 | CSS 变量完整覆盖 | 通过 `:root{--van-primary-color:#f59e0b}` 等 650+ token 全量覆盖品牌色 |
| 19 | Vant 4 | Toast 滚动穿透已处理 | `lockScroll: true`（默认），微信 WebView 无需额外处理 |
| 20 | Arco | Spring 动效参数 | 弹出元素：`spring(stiffness:300, damping:24, mass:0.8)` ≈ `cubic-bezier(0.34,1.56,0.64,1)` |

---

## 模块 1.2：UI 标准体系 · 完整精确参数

---

### A. 色彩系统

#### A1. 主色 Primary（中性黑 → 文字主色）

用途：正文、标题、高权重交互元素

| Token | HEX | HSL |
|-------|-----|-----|
| primary-50 | `#f9f9f9` | `hsl(0,0%,97.6%)` |
| primary-100 | `#f0f0f0` | `hsl(0,0%,94.1%)` |
| primary-500 | `#404040` | `hsl(0,0%,25.1%)` |
| primary-700 | `#1a1a1a` | `hsl(0,0%,10.2%)` |
| primary-900 | `#000000` | `hsl(0,0%,0%)` |

#### A2. 品牌金色 Brand（#f59e0b 基准）

用途：CTA 按钮、分数高亮、圆环进度、关键数字

| Token | HEX | HSL |
|-------|-----|-----|
| brand-50 | `#fffbeb` | `hsl(48,100%,96.1%)` |
| brand-100 | `#fef3c7` | `hsl(45,96.6%,88.8%)` |
| brand-500 | `#f59e0b` | `hsl(37.7,92.1%,50.2%)` |
| brand-700 | `#b45309` | `hsl(26,90.5%,37.1%)` |
| brand-900 | `#78350f` | `hsl(21.7,75.9%,26.5%)` |

#### A3. 灰度系统（11 级）

| Token | HEX | 用途 |
|-------|-----|------|
| gray-050 | `#fafafa` | 卡片背景、次级 surface |
| gray-100 | `#f5f5f5` | 内嵌块背景、disabled 背景 |
| gray-150 | `#ededed` | 骨架屏底色 |
| gray-200 | `#e5e5e5` | 强分割线 |
| gray-300 | `#d4d4d4` | 边框、输入框 border |
| gray-400 | `#a3a3a3` | placeholder、四级文字 |
| gray-500 | `#737373` | 三级文字（meta/辅助） |
| gray-600 | `#525252` | 二级文字 |
| gray-700 | `#404040` | 一级正文 |
| gray-800 | `#262626` | 标题 |
| gray-950 | `#0a0a0a` | 最高权重文字 |

#### A4. 语义色（各 3 个：背景/文字/边框）

**Success（绿）**
| 用途 | HEX |
|------|-----|
| success-bg | `#f0fdf4` |
| success-text | `#16a34a` |
| success-border | `#bbf7d0` |

**Warning（金 · 品牌金降饱和）**
| 用途 | HEX |
|------|-----|
| warning-bg | `#fffbeb` |
| warning-text | `#d97706` |
| warning-border | `#fde68a` |

**Error（红）**
| 用途 | HEX |
|------|-----|
| error-bg | `#fef2f2` |
| error-text | `#dc2626` |
| error-border | `#fecaca` |

**Info（蓝，仅用于中性提示）**
| 用途 | HEX |
|------|-----|
| info-bg | `#eff6ff` |
| info-text | `#2563eb` |
| info-border | `#bfdbfe` |

#### A5. 特殊层透明度

| Token | 值 | 用途 |
|-------|-----|------|
| surface-overlay | `rgba(0,0,0,0.45)` | 全屏遮罩（底部弹窗、Modal） |
| surface-scrim | `rgba(0,0,0,0.03)` | 卡片 hover 背景叠层 |
| overlay-white | `rgba(255,255,255,0.85)` | 毛玻璃浮层底色 |
| backdrop-blur | `blur(20px) saturate(180%)` | 毛玻璃 filter 值 |

---

### B. 字体层级

#### B1. 基础字体栈

```css
/* 正文 */
font-family: 
  -apple-system,         /* iOS SF Pro */
  BlinkMacSystemFont,    /* macOS SF Pro */
  "PingFang SC",         /* iOS/macOS 中文 */
  "Noto Sans SC",        /* Android/备用 */
  "Microsoft YaHei",     /* Windows */
  sans-serif;

/* 数字等宽（分数/百分比/数据）*/
font-family:
  "SF Mono",
  "Fira Code",
  "JetBrains Mono",
  "Courier New",
  monospace;
font-variant-numeric: tabular-nums;
```

#### B2. 完整字体层级参数

| 层级 | size | weight | line-height | letter-spacing | 用途 |
|------|------|--------|-------------|----------------|------|
| H1 | 28px | 700 | 1.2 | -0.02em | 页面大标题（诊断结果） |
| H2 | 24px | 700 | 1.25 | -0.015em | 模块标题（各维度分析） |
| H3 | 20px | 600 | 1.3 | -0.01em | 卡片标题 |
| H4 | 18px | 600 | 1.35 | -0.005em | 次级标题 |
| H5 | 16px | 600 | 1.4 | 0 | 列表项标题 |
| H6 | 14px | 600 | 1.4 | 0.005em | 小节标题 |
| Body L | 17px | 400 | 1.5 | 0 | 正文（主要阅读内容） |
| Body M | 15px | 400 | 1.5 | 0 | 正文（卡片内容） |
| Body S | 13px | 400 | 1.45 | 0 | 次要说明文字 |
| Caption | 12px | 400 | 1.4 | 0.01em | 图注、时间戳、meta |
| Label | 11px | 500 | 1.2 | 0.05em | 标签、Badge 文字（全大写）|
| Code | 13px | 400 | 1.6 | 0 | 数值代码块 |

#### B3. 数字等宽字体（tnum）

用于分数（如 87.3 分）、百分比（43%）、计数（1.2万）：

```css
.num-display {
  font-family: "SF Mono", "JetBrains Mono", monospace;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum" 1;
}

/* 大分数展示（诊断结果核心数字） */
.score-display {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.0;
  letter-spacing: -0.03em;
  font-variant-numeric: tabular-nums;
}
```

---

### C. 间距栅格

#### C1. 基础单位：4px

选择 4px 而非 8px 的理由：手机 375px 宽度下，8px 步进太粗，无法精细控制卡片内部间距；4px 步进兼容所有 Vant 组件内部逻辑。

#### C2. 完整间距梯度

| Token | 值 | 用途 |
|-------|-----|------|
| t0 | 0px | reset |
| t1 | 4px | 图标与文字间距、inline 元素间距 |
| t2 | 8px | 紧凑间距（Badge padding、tag 内边距） |
| t3 | 12px | 默认行内间距（列表 icon-text 间距） |
| t4 | 16px | **基础单元**（卡片内水平 padding） |
| t5 | 20px | 段落间距、section 内 gap |
| t6 | 24px | 卡片垂直 padding、模块内 gap |
| t7 | 28px | 次级模块间距 |
| t8 | 32px | 主要模块间距 |
| t9 | 36px | 大模块上下间距 |
| t10 | 40px | 页面顶部 header 高度补偿 |
| t11 | 44px | 触摸目标最小高度（Apple HIG） |
| t12 | 48px | 列表行高（Stripe 标准） |
| t13 | 56px | 大按钮高度 |
| t14 | 64px | 底部导航栏高度 |
| t15 | 80px | 大图标容器 |
| t16 | 96px | hero 区域内边距 |

#### C3. 页面边距（不同宽度断点）

| 断点 | 页面左右 margin | 用途 |
|------|---------------|------|
| < 375px（小屏）| 12px | 极小屏适配（iPhone SE） |
| 375px～414px（主力屏） | 16px | iPhone 12/13/14 主力机型 |
| 415px～768px（平板横屏） | 24px | 平板 portrait |
| > 768px（桌面/大平板） | 32px（max-width 640px 居中） | 桌面访问降级 |

#### C4. 卡片内边距（padding）规则

| 卡片类型 | padding |
|---------|---------|
| 紧凑卡片（list item） | `12px 16px` |
| 标准卡片 | `16px 16px` |
| 大卡片（诊断结果主卡） | `20px 16px` |
| 全屏 section | `24px 16px` |
| 底部弹窗（sheet） | `20px 16px 32px` |

#### C5. 组件间距规则（相邻组件 margin）

| 场景 | margin |
|------|--------|
| 同类卡片列表堆叠 | `margin-bottom: 8px` |
| 不同 section 分组 | `margin-bottom: 16px` |
| 大模块（维度分析/建议） | `margin-bottom: 24px` |
| 页面底部最后一个组件距底部导航 | `margin-bottom: 80px`（含导航栏高度） |
| 表单 field 行间距 | `margin-bottom: 12px` |

---

### D. 圆角系统

#### D1. 完整圆角梯度

| Token | 值 | 用途 |
|-------|-----|------|
| r-none | 0px | 全屏组件、分割线 |
| r-xs | 4px | 小标签、code block、checkbox |
| r-sm | 6px | 输入框、小按钮 |
| r-md | 8px | 列表项、hover 背景、Raycast 行 |
| r-lg | 12px | 标准卡片、Dropdown |
| r-xl | 16px | 大卡片、诊断结果卡 |
| r-2xl | 20px | 模态框（Modal） |
| r-sheet | 20px 20px 0 0 | 底部弹窗（top 两角圆，bottom 直角） |
| r-full | 100px | pill 按钮、Badge、Tag |

#### D2. 组件圆角对应规则

| 组件 | 圆角值 |
|------|--------|
| 主操作按钮（CTA） | `r-full`（100px pill） |
| 次要按钮 | `r-sm`（6px） |
| 输入框 | `r-sm`（6px，左右全圆角） |
| 标准卡片 | `r-xl`（16px） |
| 列表悬停背景 | `r-md`（8px） |
| Badge / Tag | `r-full`（100px） |
| Toast / Snackbar | `r-lg`（12px） |
| 底部弹窗（Sheet） | `r-sheet`（20px 20px 0 0） |
| 模态框（Modal） | `r-2xl`（20px） |
| 图片缩略图 | `r-lg`（12px） |
| 骨架屏块 | `r-md`（8px） |
| Tooltip | `r-xs`（4px） |

---

### E. 阴影层级

#### E1. elevation-0 ~ elevation-5

```css
/* elevation-0: 无阴影（flat，用 border 代替） */
--shadow-0: none;
border: 1px solid #eaeaea;

/* elevation-1: 微提升（卡片默认态） */
--shadow-1: 0 1px 2px 0 rgba(0,0,0,0.05);

/* elevation-2: 标准提升（卡片 hover、浮动工具栏） */
--shadow-2: 0 4px 6px -1px rgba(0,0,0,0.07),
            0 2px 4px -1px rgba(0,0,0,0.04);

/* elevation-3: 明显提升（下拉菜单、Popover） */
--shadow-3: 0 10px 15px -3px rgba(0,0,0,0.08),
            0 4px 6px -2px rgba(0,0,0,0.04);

/* elevation-4: 高提升（Modal、Sheet 的影子） */
--shadow-4: 0 20px 25px -5px rgba(0,0,0,0.09),
            0 10px 10px -5px rgba(0,0,0,0.03);

/* elevation-5: 最高（全屏覆盖类 Toast、系统级弹窗） */
--shadow-5: 0 25px 50px -12px rgba(0,0,0,0.15);
```

#### E2. 禁用阴影规则

以下场景**禁止使用任何 box-shadow**，改用 border：
1. 白底白卡（背景和卡片同色时阴影无意义）
2. 列表项普通态（未选中/未 hover）
3. 输入框静止态（用 `border: 1px solid #d4d4d4` 代替）
4. inline 按钮/文字链接
5. 骨架屏占位块

#### E3. 替代方案（border 替代 shadow 场景）

| 场景 | 替代方案 |
|------|---------|
| 卡片与白底区分 | `background: #fafafa` + `border: 1px solid #eaeaea` |
| 输入框 focus 状态 | `border: 1.5px solid #f59e0b`（品牌色描边） |
| 选中状态 | `border: 2px solid #f59e0b` |
| 分割线 | `border-bottom: 1px solid #eaeaea` |
| header 与内容分离 | `border-bottom: 1px solid #eaeaea`（不用 shadow） |

---

### F. 动效规则

#### F1. 基础 Easing（4 条贝塞尔曲线）

```css
/* ease-out: 元素进场（从外入内，减速停下） */
--ease-out: cubic-bezier(0.05, 0.7, 0.1, 1.0);
/* 感觉：自然飞入，有重量感，到位精准 */

/* ease-in: 元素退场（从内出外，加速离开） */
--ease-in: cubic-bezier(0.3, 0, 0.8, 0.15);
/* 感觉：快速收走，不拖泥带水 */

/* ease-in-out: 平移/换页（中间匀速，首尾缓） */
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
/* 等同 M3 standard，平滑自然 */

/* spring: 弹出元素（scale/translate 弹性） */
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
/* 轻微过冲后回弹，有生命感 */
```

#### F2. 时长梯度

| Token | 毫秒 | 用途 |
|-------|------|------|
| duration-instant | 0ms | 无动效（reduce-motion 降级） |
| duration-fast | 100ms | 微交互（hover 背景色变、active 按压） |
| duration-normal | 200ms | 标准过渡（卡片 hover shadow、颜色变化） |
| duration-moderate | 300ms | 中等动效（Toast 出现、列表项 expand） |
| duration-slow | 400ms | 大动效（Modal 进场、Sheet 升起） |
| duration-extra-slow | 600ms | 仪表盘动画（分数圆环加载、进度条） |

#### F3. 各组件动效规则

**Toast（通知提示条）**
```css
/* in: 从顶部下滑 + fade in */
transform: translateY(-100%) → translateY(0);
opacity: 0 → 1;
duration: 300ms; easing: --ease-out;

/* out: 上滑消失 + fade out */
transform: translateY(0) → translateY(-100%);
opacity: 1 → 0;
duration: 200ms; easing: --ease-in;
```

**Modal（居中弹窗）**
```css
/* in: scale 弹出 + fade */
transform: scale(0.95) → scale(1);
opacity: 0 → 1;
duration: 300ms; easing: --ease-spring;

/* out: scale 缩小 + fade */
transform: scale(1) → scale(0.95);
opacity: 1 → 0;
duration: 200ms; easing: --ease-in;

/* overlay */
opacity: 0 → 1; duration: 200ms; easing: --ease-out;
```

**Bottom Sheet（底部弹窗）**
```css
/* in: 从底部升起 */
transform: translateY(100%) → translateY(0);
duration: 400ms; easing: --ease-out;

/* out: 向下收起 */
transform: translateY(0) → translateY(100%);
duration: 300ms; easing: --ease-in;
```

**Page Transition（页面切换）**
```css
/* 新页面 in: 从右侧滑入 */
transform: translateX(100%) → translateX(0);
duration: 300ms; easing: --ease-in-out;

/* 旧页面 out: 向左推出（同时） */
transform: translateX(0) → translateX(-30%);
opacity: 1 → 0.8;
duration: 300ms; easing: --ease-in-out;
```

**List Item（列表项入场）**
```css
/* 列表顺序入场（stagger） */
每项延迟: index * 40ms（上限 200ms，第6项以后不再延迟）;
transform: translateY(8px) → translateY(0);
opacity: 0 → 1;
duration: 200ms; easing: --ease-out;
```

**Score Circle（分数圆环）**
```css
/* stroke-dashoffset 从 full → target */
stroke-dashoffset: [full] → [target];
duration: 600ms; easing: cubic-bezier(0.4, 0, 0.2, 1);
delay: 300ms（页面加载后延迟，让用户看清静止状态再动）;
```

---

### G. 图标规范

#### G1. 推荐图标库

**主选：Lucide Icons**
- GitHub：https://github.com/lucide-icons/lucide
- npm：`lucide-vue-next`（官方 Vue3 包，tree-shakeable）
- 风格：2px 线宽、圆角端点、极简线条、无填充
- 与 Vant4 兼容性：完全兼容（独立组件，无冲突）
- 图标数量：1400+，覆盖所有业务场景

**备选：Phosphor Icons**（需要多风格时）
- GitHub：https://github.com/phosphor-icons/vue
- 支持 thin/light/regular/bold/fill/duotone 6 种风格
- 同一图标可切换风格，适合区分层级

#### G2. 尺寸规范

| Token | px | 用途 |
|-------|-----|------|
| icon-xs | 12px | 内嵌文字中的图标（行内小图标） |
| icon-sm | 16px | 列表项副图标、Badge 内图标 |
| icon-md | 20px | 默认图标尺寸（最常用） |
| icon-lg | 24px | 导航栏图标、主要操作图标 |
| icon-xl | 32px | 卡片头部功能图标 |
| icon-2xl | 48px | 空状态图示、模块图标 |

#### G3. 颜色规则

| 场景 | 颜色值 |
|------|--------|
| 默认（继承父级文字色） | `currentColor`（100% 继承） |
| 导航栏未选中 | `#a3a3a3`（gray-400） |
| 导航栏选中 | `#f59e0b`（brand-500） |
| 列表项图标 | `#737373`（gray-500） |
| 主操作按钮图标 | `#ffffff`（白，在金底上） |
| 危险操作图标 | `#dc2626`（error-text） |
| 禁用态图标 | `#d4d4d4`（gray-300） |
| 强调/提示图标 | `#f59e0b`（brand-500） |

**规则**：优先用 `currentColor` 继承；仅当图标颜色需要独立于文字时才固定颜色值。

#### G4. 触摸区域规则（最小 44px）

```css
/* 所有可点击图标必须满足 44×44px 触摸区域 */
.icon-btn {
  min-width: 44px;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  /* 视觉图标可以小于 44px，通过 padding 撑开触摸区域 */
}

/* icon-md(20px) 按钮：padding 各 12px，总触摸 44px */
.icon-btn-md {
  padding: 12px;
}

/* icon-lg(24px) 按钮：padding 各 10px，总触摸 44px */
.icon-btn-lg {
  padding: 10px;
}

/* 紧凑排列时（多个图标相邻），最小 36px，不能再小 */
.icon-btn-compact {
  min-width: 36px;
  min-height: 36px;
  padding: 8px;
}
```

---

## 附录：CSS Token 完整定义（可直接使用）

```css
:root {
  /* === 品牌色 === */
  --brand-50:  #fffbeb;
  --brand-100: #fef3c7;
  --brand-500: #f59e0b;
  --brand-700: #b45309;
  --brand-900: #78350f;

  /* === 灰度 === */
  --gray-050: #fafafa;
  --gray-100: #f5f5f5;
  --gray-150: #ededed;
  --gray-200: #e5e5e5;
  --gray-300: #d4d4d4;
  --gray-400: #a3a3a3;
  --gray-500: #737373;
  --gray-600: #525252;
  --gray-700: #404040;
  --gray-800: #262626;
  --gray-950: #0a0a0a;

  /* === 语义色 === */
  --success-bg:     #f0fdf4;
  --success-text:   #16a34a;
  --success-border: #bbf7d0;
  --warning-bg:     #fffbeb;
  --warning-text:   #d97706;
  --warning-border: #fde68a;
  --error-bg:       #fef2f2;
  --error-text:     #dc2626;
  --error-border:   #fecaca;
  --info-bg:        #eff6ff;
  --info-text:      #2563eb;
  --info-border:    #bfdbfe;

  /* === Surface === */
  --bg:           #ffffff;
  --bg-soft:      #fafafa;
  --bg-inset:     #f5f5f5;
  --border:       #eaeaea;
  --border-strong:#e5e5e5;
  --overlay:      rgba(0,0,0,0.45);
  --scrim:        rgba(0,0,0,0.03);

  /* === 文字色 === */
  --text-primary:   #0a0a0a;
  --text-secondary: #404040;
  --text-tertiary:  #737373;
  --text-disabled:  #a3a3a3;
  --text-inverse:   #ffffff;

  /* === 间距 === */
  --t1:  4px;  --t2:  8px;  --t3:  12px;
  --t4:  16px; --t5:  20px; --t6:  24px;
  --t7:  28px; --t8:  32px; --t9:  36px;
  --t10: 40px; --t11: 44px; --t12: 48px;
  --t13: 56px; --t14: 64px; --t15: 80px;
  --t16: 96px;

  /* === 圆角 === */
  --r-none: 0px;
  --r-xs:   4px;
  --r-sm:   6px;
  --r-md:   8px;
  --r-lg:   12px;
  --r-xl:   16px;
  --r-2xl:  20px;
  --r-full: 100px;

  /* === 阴影 === */
  --shadow-0: none;
  --shadow-1: 0 1px 2px 0 rgba(0,0,0,0.05);
  --shadow-2: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);
  --shadow-3: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04);
  --shadow-4: 0 20px 25px -5px rgba(0,0,0,0.09), 0 10px 10px -5px rgba(0,0,0,0.03);
  --shadow-5: 0 25px 50px -12px rgba(0,0,0,0.15);

  /* === 动效 === */
  --ease-out:      cubic-bezier(0.05, 0.7, 0.1, 1.0);
  --ease-in:       cubic-bezier(0.3, 0, 0.8, 0.15);
  --ease-in-out:   cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1);

  --dur-instant:    0ms;
  --dur-fast:       100ms;
  --dur-normal:     200ms;
  --dur-moderate:   300ms;
  --dur-slow:       400ms;
  --dur-extra-slow: 600ms;

  /* === 图标 === */
  --icon-xs:  12px;
  --icon-sm:  16px;
  --icon-md:  20px;
  --icon-lg:  24px;
  --icon-xl:  32px;
  --icon-2xl: 48px;
}
```

---

> 文件路径：`docs/06-工程/design-system/01-design-system-research.md`  
> 版本：v1.0  
> 下一步：基于本文件生成 `tokens.css` + Vant4 主题覆盖配置
