---
layout: home

hero:
  name: "视频 CT"
  text: "短视频博主 AI 诊断 SaaS"
  tagline: 提交一个视频链接，获得一份 CT 级多维诊断报告。对标头部，定位人设，用 AI 陪跑你的每一次创作。
  image:
    src: /logo.svg
    alt: 视频 CT
  actions:
    - theme: brand
      text: 快速开始
      link: /guide/quickstart
    - theme: alt
      text: API 参考
      link: /api/overview
    - theme: alt
      text: 查看 SDK
      link: /sdk/js

features:
  - icon: 🔍
    title: CT 级多维诊断
    details: 六维 18 点位深度扫描。从曝光率到变现率，AI 逐帧分析你的视频短板，生成结构化诊断报告。
    link: /api/diagnosis
  - icon: 🎯
    title: 头部对标差距分析
    details: 实时对比同赛道 Top10 博主。量化你和头部的六大指标差距，数据驱动你的迭代策略。
    link: /api/diagnosis
  - icon: 🧬
    title: 人设 DNA 扫描
    details: 基于视频画像 + 评论语义，AI 反向工程你的人设原型。发现你的人设一致性得分与漂移告警。
    link: /api/persona
  - icon: 📊
    title: 商业定位引擎
    details: 结合博主特性 + 赛道分析，AI 推荐最优变现路径、绘制 12 个月路线图、BMC 商业画布。
    link: /api/diagnosis
  - icon: 🤝
    title: 分享官裂变体系
    details: 内置三级分享官等级 + 奖励机制。用户拉新你赚钱，自动归因 + 实时看板。
    link: /api/referrer
  - icon: 🔌
    title: 开放端 API
    details: RESTful API + JWT 鉴权 + API Key + HMAC 签名。提供 JS/Python SDK，15 分钟即可集成到你自己的产品。
    link: /api/overview

---

## 什么是视频 CT？

**视频 CT** 是一款面向短视频博主的 AI 诊断 + 对标 + 陪跑 SaaS 产品。

它的核心能力是将一个视频链接转化为一份**结构化诊断报告**：

```
提交视频链接 → AI 采集元数据 → 多模态分析（视频/音频/字幕/评论）
  → 6 维 18 点位 CT 扫描 → 生成诊断报告 + 对标差距 + 改善建议
```

## 四端架构

| 端 | 技术栈 | 说明 |
|---|---|---|
| **C 端 H5** | Vue3 + Vant4 | 面向博主用户，诊断提交 + 报告查看 |
| **顾问端** | Vue3 + Antd Pro | 面向付费顾问，博主管理 + 人工复核 |
| **运营端** | Vue3 + Antd Pro | 面向运营团队，数据看板 + 用户管理 |
| **开放端** | VitePress（本站） | 面向开发者，API 文档 + SDK |

## 快速集成

### 注册获取 API Key

1. 访问 [视频 CT](https://video-ct.cn) 注册账号
2. 进入「开发者中心」获取 API Key
3. 使用 API Key 调用开放端接口

### 首次调用

```bash
curl -X POST "https://api.video-ct.cn/api/v1/auth/otp/send" \
  -H "Content-Type: application/json" \
  -d '{"phone": "13800138000"}'
```

### 查看完整文档

- [快速开始指南](/guide/quickstart) — 从零到第一次诊断报告
- [API 参考](/api/overview) — 全部 API 端点详解
- [JS SDK](/sdk/js) — 前端 / Node.js 快速集成
- [Python SDK](/sdk/python) — 后端 / 脚本快速集成

## 技术栈速览

- **后端**: Python FastAPI + SQLAlchemy + PostgreSQL + Redis
- **AI**: DeepSeek / Qwen 系列模型（通过硅基流动 API）
- **前端 C 端**: Vue3 + Vant4 + Pinia + ECharts
- **开放端文档**: VitePress（本站）
- **部署**: Docker Compose（开发） / K8s（生产）

::: tip 开源协议
视频 CT 采用 MIT 开源协议。欢迎提交 PR 和 Issue。
:::
