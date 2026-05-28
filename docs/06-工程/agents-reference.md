# AI Agent 能力卡

> 文件位置：`services/api/app/agents/`  
> 基类：`BaseAgent`（Plan → Tool → Observe → Reflect → Output 五步循环）  
> 编排入口：`AgentOrchestrator`（`orchestrator.py`）

---

## 总览

| Agent | 类名 | 主要输入 | 主要输出 | 调用端 |
|-------|------|---------|---------|-------|
| CT 诊断官 | `CTRadiologistAgent` | 视频元数据 + OCR/ASR 文本 | 6 维 18 点位 CT 报告 JSON | `POST /diagnosis/submit` |
| 对标分析师 | `BenchmarkAnalystAgent` | 用户指标 + 赛道头部数据 | 差距分析 + 异动检测 + 趋势 | `POST /benchmark/gap` |
| 人设观察员 | `PersonaScoutAgent` | 多条视频文本 + 博主自述 | IPP 人设档案 JSON | `POST /persona/scan` |
| 商业策略师 | `BizStrategistAgent` | 人设档案 + 业务目标 | BPS 商业定位 + 12 月路线图 | `POST /positioning/scan` |
| 内容生成手 | `ContentMakerAgent` | 选题 + 博主风格 | 钩子 / 标题 / 封面文案 | `POST /ai/content/generate` |
| 数据预警员 | `DataSentinelAgent` | 近期指标序列 + 阈值配置 | 分级告警列表 + 整体状态 | 定时任务 / 诊断后自动触发 |
| 顾问助理 | `ConsultantCopilotAgent` | 客户档案 + 历史诊断列表 | 月度/季度会议简报 JSON | 顾问端「生成简报」按钮 |
| 客户成功管家 | `CSButlerAgent` | 生命周期事件（首诊/续费/流失预警） | 运营动作推荐 + 消息模板 | 事件触发（EventBus） |
| Agent 编排器 | `AgentOrchestrator` | Chain 定义 + 上下文 | 多 Agent 协同结果 | 复杂任务入口 |
| 顾问副驾 | `ConsultantCopilotAgent` | （同顾问助理，兼任实时问答） | 实时回答顾问问询 | 顾问端对话框 |

---

## 详细说明

### CT 诊断官 `CTRadiologistAgent`

**职责**：对单条视频做 6 维 18 点位诊断，生成结构化 CT 报告。

**6 个诊断维度**：
1. 钩子力（前 3 秒留存）
2. 内容密度（信息量 / 时长）
3. 情绪曲线（高潮分布）
4. 视觉质量（画质 / 镜头稳定）
5. 完播率预测（节奏 + 时长适配）
6. 转化信号（CTA 清晰度）

**输出结构**：
```json
{
  "overall_score": 72,
  "dimensions": { "hook": {...}, "density": {...}, ... },
  "suggestions": [{ "id": "...", "priority": "P0", "text": "..." }],
  "version": "v3"
}
```

---

### 对标分析师 `BenchmarkAnalystAgent`

**职责**：计算用户指标与赛道头部的差距，检测数据异动。  
**特点**：大部分逻辑为数学运算，LLM 仅用于文字解读。

**输出结构**：
```json
{
  "gap_scores": { "views": -23, "engagement": +5 },
  "anomalies": [{ "metric": "completion_rate", "delta": -18, "severity": "high" }],
  "trend": "improving"
}
```

---

### 人设观察员 `PersonaScoutAgent`

**职责**：根据多条视频 + 博主自述，输出 IPP 人设档案。

**IPP 三维**：Identity（身份）/ Personality（性格）/ Positioning（定位）

---

### 商业策略师 `BizStrategistAgent`

**职责**：BPS 商业定位扫描 + 12 个月演进路线图。

**安全约束**：禁止输出「必涨粉、必爆款、必赚钱」等绝对化表述。

---

### 内容生成手 `ContentMakerAgent`

**职责**：为指定选题生成爆款钩子 / 标题 / 封面文案。  
**约束**：每条不超过 30 字，直接返回 JSON，不加 markdown。

---

### 数据预警员 `DataSentinelAgent`

**职责**：检测指标异动，输出分级告警（info / warning / critical）。  
**触发方式**：① 每次诊断完成后自动运行；② 定时任务（APScheduler 每日 06:00）。

---

### 顾问助理 `ConsultantCopilotAgent`

**职责**：为 MAX 客户的专属顾问准备月度/季度会议简报。  
**调用端**：`apps/consultant/` 顾问后台「生成简报」按钮。

---

### 客户成功管家 `CSButlerAgent`

**职责**：监听生命周期事件，推荐运营动作并生成消息模板。  
**事件类型**：首次诊断 / 连续三次诊断 / 订阅即将到期 / 流失预警 / 分享官晋级。

---

### Agent 编排器 `AgentOrchestrator`

**职责**：纯路由逻辑，不依赖 LLM。将多个 Agent 串联成 `Chain`，支持顺序 / 并行执行。

**内置 Chain**：
- `full_diagnosis_chain`：CT 诊断官 → 对标分析师 → 数据预警员
- `onboarding_chain`：人设观察员 → 商业策略师 → 客户成功管家
- `content_chain`：CT 诊断官 → 内容生成手

---

## 如何新增 Agent

1. 在 `services/api/app/agents/` 新建 `xxx.py`，继承 `BaseAgent`
2. 实现 `async def run(self, **kwargs) -> dict`
3. 在 `__init__.py` 导出
4. 在 `orchestrator.py` 注册到对应 Chain（如需编排）
5. 在路由层（`app/api/ai.py` 或新建路由文件）暴露端点
