# 诊断 API

视频 CT 的核心功能。通过提交一个视频链接，AI 自动采集元数据并进行多维诊断分析，生成结构化报告。

## 端点列表

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| `POST` | `/api/v1/diagnoses/submit` | JWT | 提交诊断任务 |
| `GET` | `/api/v1/diagnoses` | JWT | 诊断历史列表 |
| `GET` | `/api/v1/diagnoses/{diagnosis_id}` | JWT | 诊断详情 |
| `GET` | `/api/v1/diagnoses/{diagnosis_id}/report` | JWT | 获取诊断报告 |
| `POST` | `/api/v1/diagnoses/{diagnosis_id}/report/feedback` | JWT | 提交报告反馈 |

---

## 提交诊断

```
POST /api/v1/diagnoses/submit
```

提交一个视频链接，启动 AI 诊断流程。

### 请求体

```json
{
  "video_url": "https://v.douyin.com/xxxxx/",
  "track": "美食",
  "diagnosis_type": "ct_basic",
  "title": "我的爆款视频",
  "description": "想了解这条视频为什么火"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `video_url` | `string` | 是 | 视频链接（4-1000 字符）支持抖音/快手/B站/小红书/视频号 |
| `track` | `string` | 否 | 内容赛道（如"美食"、"科技"、"穿搭"） |
| `diagnosis_type` | `string` | 否 | 诊断类型：`ct_basic`（基础诊断）或 `ct_full`（全维度诊断），默认 `ct_basic` |
| `title` | `string` | 否 | 视频标题（可选覆盖） |
| `description` | `string` | 否 | 补充说明 |

::: tip 额度说明
- 免费用户每月 3 次基础诊断
- Pro 用户每月 20 次诊断（含全维度）
- Max 用户每月 100 次诊断（含全维度）
- 超出后可单独购买单次诊断（¥19/次基础，¥49/次全维度）
:::

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "video_url": "https://v.douyin.com/xxxxx/",
    "video_platform": "douyin",
    "status": "pending",
    "diagnosis_type": "ct_basic",
    "progress_pct": 0,
    "created_at": "2026-05-20T10:30:00Z",
    "completed_at": null
  }
}
```

诊断状态 (`status`) 流转：`pending` -> `crawling` -> `analyzing` -> `completed` / `failed`

### 诊断流程

```
提交链接 → 爬虫采集元数据 → OCR/ASR 多模态提取
  → AI 6 维 18 点位 CT 扫描 → 生成报告（HTML + PDF）
```

诊断完成后会自动更新成长档案和每日对标快照。

---

## 诊断历史

```
GET /api/v1/diagnoses?limit=20
```

### 查询参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `limit` | `int` | `20` | 返回条数 |

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": [
    {
      "id": 1,
      "video_url": "https://v.douyin.com/xxxxx/",
      "video_platform": "douyin",
      "status": "completed",
      "diagnosis_type": "ct_basic",
      "progress_pct": 100,
      "created_at": "2026-05-20T10:30:00Z",
      "completed_at": "2026-05-20T10:32:00Z"
    }
  ]
}
```

---

## 诊断详情

```
GET /api/v1/diagnoses/{diagnosis_id}
```

获取单个诊断任务的当前状态。

### 路径参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `diagnosis_id` | `int` | 诊断 ID |

### 响应

同提交诊断的响应格式。可轮询此接口获取任务进度。

---

## 获取诊断报告

```
GET /api/v1/diagnoses/{diagnosis_id}/report
```

获取诊断完成后生成的完整报告。

### 响应

```json
{
  "code": "OK",
  "message": "success",
  "data": {
    "id": 1,
    "diagnosis_id": 1,
    "overall_score": 72,
    "grade": "B",
    "dimensions": {
      "曝光率": {
        "score": 65,
        "advantages": ["标题吸引力较强，前3秒完播率高"],
        "findings": ["封面文字过多，信息密度过高"],
        "suggestions": ["简化封面，突出1个核心卖点"]
      },
      "点赞率": {
        "score": 78,
        "advantages": ["结尾引导自然"],
        "findings": ["中段内容节奏偏慢"],
        "suggestions": ["15-20秒处增加信息增量或反转"]
      }
    },
    "findings": [
      {
        "timestamp": "0:07",
        "dimension": "曝光率",
        "problem": "黄金3秒后信息密度骤降",
        "suggestion": "保持前15秒的节奏密度"
      }
    ],
    "suggestions": [],
    "benchmark_gap": {
      "overall_gap_pct": 18,
      "曝光率": -2.3,
      "点赞率": -1.1
    },
    "html_path": "/storage/reports/1_report.html",
    "pdf_path": "/storage/reports/1_report.pdf",
    "model_used": "deepseek-v3",
    "user_rating": null,
    "consultant_reviewed": false,
    "created_at": "2026-05-20T10:32:00Z"
  }
}
```

### 报告字段说明

| 字段 | 类型 | 说明 |
|---|---|---|
| `overall_score` | `int` | 综合评分（0-100） |
| `grade` | `string` | 评级：S(90+)、A(80-89)、B(70-79)、C(60-69)、D(<60) |
| `dimensions` | `object` | 六维逐项诊断，每项含 `score` / `advantages` / `findings` / `suggestions` |
| `findings` | `array` | 时间轴定位的具体问题点 |
| `benchmark_gap` | `object \| null` | 与赛道头部平均值的差距 |
| `html_path` | `string \| null` | HTML 报告本地路径 |
| `pdf_path` | `string \| null` | PDF 报告本地路径 |
| `model_used` | `string \| null` | 使用的 AI 模型名称 |
| `consultant_reviewed` | `bool` | 是否经过顾问人工复核 |

### 六大诊断维度

| 维度 | 诊断内容 |
|---|---|
| **曝光率** | 标题/封面吸引力、前3秒完播率、搜索权重 |
| **点赞率** | 内容价值感、情绪共鸣点、结尾引导 |
| **评论率** | 话题争议性、互动钩子、评论区运营 |
| **转发率** | 社交货币、实用价值、热门关联 |
| **收藏率** | 信息密度、干货占比、结构化程度 |
| **变现率** | 商业植入自然度、转化钩子、用户信任 |

---

## 提交报告反馈

```
POST /api/v1/diagnoses/{diagnosis_id}/report/feedback
```

对诊断报告进行评分和反馈，帮助 AI 持续优化诊断质量。

### 请求体

```json
{
  "rating": 4,
  "feedback": "分析很准确，建议部分如果再具体一些会更好"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `rating` | `int` | 是 | 评分 1-5 |
| `feedback` | `string` | 否 | 文字反馈 |
