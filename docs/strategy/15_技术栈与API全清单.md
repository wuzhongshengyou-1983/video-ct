# 15 · 技术栈与 API 全清单

> 整套战略落地所需的全部技术 · 外部 API · 内部接口 · 选型理由 · 成本预算

---

## 15.1 总览：技术地图（一张图看全栈）

```
┌─────────────────────────────────────────────────────────────────┐
│  端 ① C 端          端 ② 顾问端    端 ③ 运营端   端 ④ 开放端     │
│ Taro+React (小程序) │ Vue3+Antd Pro│ Vue3+Antd Pro│ OpenAPI+Stoplight│
│ Vite+Vue3 (H5)      │              │              │                 │
│ Flutter (App)       │              │              │                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  网关层  Nginx + Kong（限流/鉴权/计费）                            │
│  BFF     Python FastAPI（按端独立 BFF）                            │
│  协议    REST + GraphQL（顾问端用 GraphQL）+ WebSocket（实时预警） │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  核心微服务层（Python FastAPI / Go 选型）                          │
│  20+ 服务：账号/订阅/诊断/报告/对标/档案/预警/支付/人设/商业定位/    │
│           分享官/任务/优惠券/活动/CMS/CRM/财务...                  │
│                                                                  │
│  AI Agent 服务层（独立部署，调度 LLM 与工具）                      │
│  Orchestrator（LangGraph）+ 8 大 Agent + 工具集                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  数据层                                                          │
│  PostgreSQL（业务）│ ClickHouse（分析）│ Redis（缓存+会话）        │
│  MongoDB（半结构化）│ Milvus（向量）│ Elasticsearch（全文检索）    │
│  Kafka（事件总线）│ MinIO/OSS（对象存储）│ Neo4j（关系图谱，可选） │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15.2 技术栈分类清单（含选型理由）

### 15.2.1 编程语言

| 语言 | 用途 | 选型理由 |
|---|---|---|
| **Python 3.11+** | 后端微服务 / AI 推理 / 数据处理 | AI 生态最完整、研发速度快、招聘容易 |
| **TypeScript** | 全部前端 / Node 工具脚本 | 类型安全、维护成本低 |
| **Go 1.22+** | 高并发服务（网关、消息推送、风控） | 高并发、低内存、单文件部署 |
| **SQL** | 数据库查询 / 数据分析 | 行业标配 |
| **Shell/Bash** | 运维脚本 / CI/CD | 服务器操作 |
| **Dart** | Flutter App（Y2 上线） | 一套代码 iOS+Android |

### 15.2.2 后端框架

| 框架 | 用途 | 替代方案 |
|---|---|---|
| **FastAPI** | 主力后端框架 | Django REST（不选，太重）/ Flask（不选，太轻）|
| **Celery + Redis** | 异步任务队列 | RQ（轻量替代）|
| **APScheduler** | 定时任务 | Crontab（小规模）|
| **SQLAlchemy 2.0** | ORM | Tortoise ORM（异步原生）|
| **Pydantic v2** | 数据验证 | — |
| **Strawberry** | GraphQL（顾问端用） | Graphene（社区不活跃）|
| **Gin / Fiber** | Go 服务（网关/推送） | Echo |

### 15.2.3 前端框架（按端）

| 端 | 主框架 | UI 组件 | 状态管理 | 构建 |
|---|---|---|---|---|
| C 端·小程序 | **Taro 4 + React 18** | Taro UI / NutUI | Zustand | Vite |
| C 端·H5 | **Vue 3 + Composition API** | Vant 4 | Pinia | Vite |
| C 端·App（Y2） | **Flutter 3.x** | Material 3 | Riverpod | Flutter SDK |
| 顾问端 | **Vue 3 + TS** | Ant Design Vue Pro | Pinia | Vite |
| 运营端 | **Vue 3 + TS** | Ant Design Vue Pro | Pinia | Vite |
| 开放端·文档站 | **VitePress + Stoplight Elements** | — | — | Vite |
| 开放端·加盟商后台 | **Vue 3 + TS** | Ant Design Vue Pro | Pinia | Vite |

### 15.2.4 数据库选型

| 类型 | 选型 | 用途 | 替代 |
|---|---|---|---|
| **关系型主库** | **PostgreSQL 16** | 用户/订阅/订单/档案 | MySQL 8 |
| **OLAP 分析库** | **ClickHouse** | 数据看板、指标聚合、行为分析 | StarRocks |
| **缓存** | **Redis 7** | session、限流、热数据、任务队列 | DragonflyDB |
| **半结构化** | **MongoDB 7** | 视频元数据、AI 报告原始 JSON | DocumentDB |
| **向量** | **Milvus 2.4** | RAG embedding 检索 | Qdrant / Weaviate |
| **全文检索** | **Elasticsearch 8** | 案例库、模板库搜索 | Meilisearch（轻量替代）|
| **图谱（可选）** | **Neo4j** | 客户关系/分享官层级网络（Y2 起）| ArangoDB |
| **时序（可选）** | **TimescaleDB** | 六大指标时序数据 | InfluxDB |

### 15.2.5 消息与事件

| 组件 | 用途 | 选型 |
|---|---|---|
| 事件总线 | 跨服务异步通信 | **Apache Kafka** + Schema Registry |
| 消息队列 | 任务派发 | **RabbitMQ** 或 Redis Streams |
| WebSocket | 实时预警推送 | **Socket.IO** + Redis Adapter |
| WebRTC（可选） | 顾问视频会议自建 | Janus / LiveKit |

### 15.2.6 文件与媒体

| 用途 | 选型 |
|---|---|
| 对象存储 | **阿里云 OSS** / 腾讯云 COS / MinIO（自建） |
| CDN | **阿里云 CDN** + 七牛云（备） |
| 视频转码 | **阿里云 MPS** / FFmpeg 自建 |
| 图片处理 | OSS 内置 / **Sharp**（Node 端）|
| 视频抽帧 | **FFmpeg** 自建 |

### 15.2.7 AI/ML 技术栈

| 模块 | 选型 | 备选 |
|---|---|---|
| **大语言模型 API** | DeepSeek-V3.5 / Qwen-Plus / Qwen-Max / Claude Sonnet 4.6 / Claude Opus 4.7 / Claude Haiku 4.5 | GPT-4o / Gemini |
| **Embedding** | bge-large-zh-v1.5（自部署）/ Qwen Embedding | text-embedding-3-large |
| **OCR** | **PaddleOCR**（开源）/ 阿里云 OCR API | Tesseract（英文） |
| **ASR** | **Whisper Large v3**（自部署）/ 阿里云 ASR API | 火山引擎 ASR |
| **视觉理解** | **Qwen-VL-Max** / Claude Sonnet 4.6 | GPT-4o vision |
| **Agent 编排框架** | **LangGraph** | LangChain / LlamaIndex |
| **Prompt 管理** | **Langfuse**（开源自部署）| PromptLayer |
| **模型评估** | **DeepEval** + 自研双盲对照 | Ragas |
| **微调框架** | **LLaMA-Factory** | Axolotl / Unsloth |
| **向量检索** | **Milvus** + LangChain Retrieval | Qdrant |
| **RAG 框架** | **LlamaIndex** 或 自研 | LangChain RAG |
| **模型推理服务** | **vLLM**（自部署 LLM）/ TGI | Triton |
| **MLOps** | **MLflow** + DVC | Weights & Biases |

### 15.2.8 容器与编排

| 组件 | 用途 |
|---|---|
| **Docker** | 容器化 |
| **Kubernetes 1.30+** | 编排（M6+ 引入） |
| **Helm** | K8s 包管理 |
| **Istio**（可选） | 服务网格（Y2 引入） |
| **ArgoCD** | GitOps 部署 |

### 15.2.9 CI/CD 与开发流程

| 工具 | 用途 |
|---|---|
| **GitLab / GitHub** | 代码托管 |
| **GitLab CI** / **GitHub Actions** | 流水线 |
| **SonarQube** | 代码质量扫描 |
| **Snyk** | 安全漏洞扫描 |
| **Harbor** | Docker 镜像仓库 |
| **Sealos / 阿里云 ACR** | 国内镜像 |

### 15.2.10 监控、日志、告警

| 组件 | 用途 |
|---|---|
| **Prometheus** + **Grafana** | 系统指标 |
| **Loki** + **Promtail** | 日志聚合 |
| **Sentry** | 业务异常 |
| **OpenTelemetry** + **Jaeger** | 分布式链路追踪 |
| **AlertManager** + **飞书 / 钉钉机器人** | 告警分发 |
| **PagerDuty**（可选） | 严重告警 oncall |
| **神策数据 / GrowingIO / 自研 SDK** | 用户行为埋点 |
| **阿里云 ARMS** | 应用性能监控（可选） |

### 15.2.11 安全与风控

| 组件 | 用途 |
|---|---|
| **阿里云 WAF** | Web 应用防火墙 |
| **阿里云 DDoS 高防 IP** | 防 DDoS |
| **HashiCorp Vault** | 密钥管理 |
| **Keycloak**（可选） | 统一身份 OAuth 2.0 SSO |
| **JWT (RS256)** | API 鉴权 |
| **bcrypt / Argon2id** | 密码哈希 |
| **同盾 / 数美 / 顶象** | 风控（反刷单/反爬）|
| **腾讯云人脸识别** | 实名认证（分享官提现）|
| **腾讯天御 / 阿里绿网** | 内容审核 |

### 15.2.12 开发与协作

| 工具 | 用途 |
|---|---|
| **VS Code / Cursor** | 主力 IDE |
| **JetBrains 全家桶** | 后端/前端可选 |
| **Apifox / Postman** | API 调试 + Mock |
| **Figma** | UI/UX 设计 |
| **Tower / Lark / 飞书** | 项目管理 + 文档 |
| **Notion / Outline** | 知识库 |
| **Slack / 飞书** | 即时通讯 |

---

## 15.3 外部 API 与服务集成全清单（**重点**）

### 15.3.1 微信生态

| API | 用途 | 必需性 | 成本 |
|---|---|---|---|
| **微信小程序 API** | 主入口 | ★★★ | 免费 + 流量分摊 |
| **微信小程序订阅消息** | 推送通知 | ★★★ | 免费 |
| **微信公众号 API** | 引流入口 | ★★★ | 免费 |
| **微信支付 API（JSAPI/NATIVE）** | 主要支付 | ★★★ | 0.6% 手续费 |
| **微信开放平台 OAuth** | 第三方登录 | ★★★ | 免费 |
| **企业微信 API** | SCRM / 客服 / 顾问触达 | ★★★ | 免费 + 增值服务 |
| **微信视频号 API**（限商业认证） | 视频号数据采集（待开放）| ★★ | TBD |

### 15.3.2 短视频平台 API（核心数据源）

| 平台 | API/方式 | 必需性 | 成本 | 备注 |
|---|---|---|---|---|
| **抖音开放平台** | OAuth + 用户授权数据 | ★★★ | 部分免费 + 配额 | 必须开发者认证 |
| **抖音电商开放平台** | 带货数据 | ★★ | 配额制 | 卖货博主必备 |
| **快手开放平台** | OAuth + 用户授权 | ★★ | 配额制 | 同上 |
| **小红书开放平台**（仅特定客户）| OAuth | ★★ | 配额制 | 申请门槛高 |
| **B站开放平台** | OAuth + 用户授权 | ★★ | 免费 + 限流 | |
| **微博开放平台** | OAuth + 公开数据 | ★ | 配额制 | 辅助 |
| **TikTok for Business API**（Y2） | 国际版 | ★★ | 配额制 | 国际化 |

### 15.3.3 第三方数据商（补充 / 兜底）

| 商家 | 用途 | 成本 | 何时启用 |
|---|---|---|---|
| **飞瓜数据 API** | 头部账号、视频数据 | 1-5 万/年 | M3 起 |
| **新榜 API** | 公众号 + 短视频数据 | 1-3 万/年 | M3 起 |
| **蝉妈妈 API** | 抖音电商深度数据 | 2-5 万/年 | M6 起（带货赛道）|
| **灰豚数据 API** | 抖音+快手数据 | 1-3 万/年 | 备选 |
| **果集数据** | 全网媒介数据 | 协议价 | Y2 起 |

### 15.3.4 AI 模型 API

| 提供商 | 模型 | 单价（输入/输出）/千 tokens | 月预算估算 |
|---|---|---|---|
| **DeepSeek 官方** | deepseek-chat / deepseek-reasoner | 0.001 / 0.002 元 | PRO 主力，月 3,000 元 |
| **阿里云百炼** | qwen-plus / qwen-max | 0.004 / 0.012 元 / 0.04 / 0.12 元 | MAX 主力，月 10,000 元 |
| **阿里云百炼** | qwen-vl-max | 0.02 元（图片）| 月 5,000 元 |
| **Anthropic Claude API** | claude-sonnet-4-6 / claude-haiku-4-5 / claude-opus-4-7 | 0.003 / 0.015 / 0.0008 / 0.004 / 0.015 / 0.075 USD | MAX 高质量场景，月 5,000 元 |
| **OpenAI API**（备用） | gpt-4o-mini / gpt-4o | 0.15 / 0.6 USD | 应急 |
| **MiniMax / Moonshot / 智谱 GLM** | 备选 | 价格相近 | 多供应商策略 |

**多模型路由策略：**
- 单条 PRO 诊断成本 ≤ 0.3 元
- 单条 MAX 诊断成本 ≤ 2 元
- 单次脚本加购（Opus 4.7）≤ 8 元
- 总 AI 成本占营收比 < 8%

### 15.3.5 支付 API

| 商家 | 用途 | 费率 |
|---|---|---|
| **微信支付 商户号** | 主要支付 | 0.6% |
| **支付宝开放平台** | 备选支付 | 0.6% |
| **抖音小程序支付**（如做抖音端）| 抖音端付费 | 1% |
| **连连支付 / 易宝** | 对公收款 | 协议价 |
| **聚合支付（如收钱吧）** | 线下沙龙现场收款 | 0.38% |

### 15.3.6 通知与触达

| 服务 | 用途 | 成本 |
|---|---|---|
| **阿里云短信 SMS** | 验证码 / 预警 | 0.045 元/条 |
| **腾讯云短信** | 备用 | 0.045 元/条 |
| **腾讯企业邮 / 网易邮箱大师** | 邮件 | 月度套餐 |
| **SendGrid / Mailgun** | 海外邮件（Y2）| 用量计费 |
| **极光推送 / 友盟 +** | App 推送 | 免费 + 增值 |
| **微信订阅消息** | 小程序消息 | 免费 |
| **企微 SCRM 推送** | 客户触达 | 免费 + 工具费 |

### 15.3.7 实名 / 风控 / 合规

| 服务 | 用途 | 成本 |
|---|---|---|
| **腾讯云人脸核身** | 分享官提现实名认证 | 0.5 元/次 |
| **阿里云实人认证** | 备选 | 0.5 元/次 |
| **同盾 / 数美 / 顶象** | 反刷单、反作弊 | 协议价 |
| **e签宝 / 法大大 / 上上签** | 电子合同（服务协议）| 1-5 元/份 |
| **阿里云内容安全 / 腾讯云天御** | 内容审核 | 0.001-0.005 元/次 |
| **诺诺发票 / 百望云** | 电子发票 | 按张计费 |

### 15.3.8 客服 / CRM / 工单

| 服务 | 用途 | 成本 |
|---|---|---|
| **企业微信 + 自研工单** | 主力客服 | 免费 + 自研成本 |
| **容联七陌 / Udesk**（可选）| 全渠道客服 | 199-999/人/月 |
| **Zendesk / Intercom**（海外） | Y2 国际化 | 49 USD/人/月 |
| **腾讯文档 / 飞书多维表格** | 临时 CRM（M0-M3） | 免费 |
| **HubSpot / 销售易**（Y2） | 正式 CRM | 协议价 |

### 15.3.9 直播 / 视频会议

| 服务 | 用途 | 成本 |
|---|---|---|
| **腾讯会议 API** | MAX 顾问 1v1 | 免费基础版 / 100 元/账号/月 |
| **飞书会议** | 内部协作 | 飞书订阅含 |
| **声网 Agora**（可选）| 自建视频会议 | 用量计费 |
| **阿里云直播** | 周三公开直播 | 0.04 元/GB |
| **抖音直播 / 视频号直播** | 公开直播（原生） | 免费 |

### 15.3.10 数据/BI/埋点

| 服务 | 用途 | 成本 |
|---|---|---|
| **神策数据** | 用户行为分析 | 5-30 万/年 |
| **GrowingIO** | 增长分析 | 协议价 |
| **Apache Superset** | 自建 BI（运营端看板）| 开源免费 |
| **Metabase** | 轻量级 BI | 开源免费 |
| **DataDog**（可选） | 全栈监控 | $15-23/host/月 |

### 15.3.11 地图 / 位置

| 服务 | 用途 | 成本 |
|---|---|---|
| **高德开放平台** | IP 定位、地址搜索（线下沙龙）| 免费配额 |
| **腾讯位置服务** | 备选 | 免费配额 |

### 15.3.12 内容素材 / 字体 / 音效

| 服务 | 用途 | 成本 |
|---|---|---|
| **Pixabay / Pexels API** | 免版税图库 | 免费 |
| **Unsplash API** | 高质图库 | 免费 |
| **方正字库 / 汉仪字库**（商用授权）| 中文字体 | 1-10 万/年 |
| **AudioJungle**（商用） | 音乐音效 | 按曲购买 |
| **剪映素材库 API**（如有开放）| 视频模板 | TBD |

### 15.3.13 法律 / 财务工具

| 服务 | 用途 | 成本 |
|---|---|---|
| **企查查 / 天眼查 API** | 客户工商核验 | 协议价 |
| **慧算账 / 用友** | 财税 SaaS | 月度套餐 |
| **诺诺发票** | 电子发票开具 | 按张 |

---

## 15.4 内部 API 设计（按微服务列）

### 15.4.1 服务清单（20+ 微服务）

| 服务 | 端口段 | 主要职责 |
|---|---|---|
| **gateway-service** | 80/443 | 全局网关 |
| **auth-service** | 8001 | 注册/登录/JWT/SSO |
| **user-service** | 8002 | 用户档案/权限 |
| **subscription-service** | 8003 | PRO/MAX 订阅/续费 |
| **payment-service** | 8004 | 微信/支付宝/对公 |
| **diagnosis-service** | 8011 | CT 诊断任务管理 |
| **report-service** | 8012 | 报告生成/导出 |
| **benchmark-service** | 8013 | 头部对标数据 + 差距 |
| **archive-service** | 8014 | 终身成长档案 |
| **alert-service** | 8015 | 数据预警 |
| **persona-service** | 8021 | 人设 IPP |
| **positioning-service** | 8022 | 商业 BPS |
| **content-gen-service** | 8023 | 钩子/标题/封面/脚本 |
| **referrer-service** | 8031 | 分享官 + 关系链 |
| **task-engine-service** | 8032 | 任务系统 |
| **coupon-service** | 8033 | 优惠券/抵扣券 |
| **event-marketing-service** | 8034 | 活动（拼团/挑战/锦鲤）|
| **crm-service** | 8041 | 客户管理（顾问端用） |
| **cms-service** | 8042 | 内容/模板/案例库 |
| **finance-service** | 8043 | 财务对账 / 发票 |
| **risk-service** | 8044 | 风控反作弊 |
| **ai-orchestrator** | 8051 | Agent 调度 |
| **rag-service** | 8052 | 向量检索 |
| **crawler-service** | 8061 | 数据采集（合规爬虫）|
| **notification-service** | 8071 | 通知分发（短信/邮件/微信）|
| **file-service** | 8081 | 视频/图片上传 |
| **export-service** | 8082 | PDF/Excel 导出 |

### 15.4.2 核心服务 API 端点示例

#### auth-service
```
POST   /api/v1/auth/register            注册（微信 OAuth / 手机号）
POST   /api/v1/auth/login               登录
POST   /api/v1/auth/refresh             刷新 token
POST   /api/v1/auth/logout              登出
GET    /api/v1/auth/me                  当前用户信息
POST   /api/v1/auth/realname            实名认证（提现前）
```

#### subscription-service
```
GET    /api/v1/subscriptions/products   产品目录（PRO/MAX/单次/加购）
POST   /api/v1/subscriptions/order      创建订单
GET    /api/v1/subscriptions/my         我的订阅
POST   /api/v1/subscriptions/cancel     退订
POST   /api/v1/subscriptions/upgrade    升级（PRO→MAX）
GET    /api/v1/subscriptions/usage      配额使用情况
```

#### diagnosis-service
```
POST   /api/v1/diagnosis/submit         提交视频（链接/上传）
GET    /api/v1/diagnosis/{task_id}      查询诊断结果
GET    /api/v1/diagnosis/history        历史诊断列表
DELETE /api/v1/diagnosis/{task_id}      删除诊断记录
POST   /api/v1/diagnosis/feedback       用户反馈（👍👎+评分）
POST   /api/v1/diagnosis/review         顾问复审（MAX）
```

#### benchmark-service
```
GET    /api/v1/benchmark/tracks         全部赛道列表
POST   /api/v1/benchmark/lock           锁定客户专属 TOP10（MAX）
GET    /api/v1/benchmark/{user_id}/gap  当前差距
GET    /api/v1/benchmark/{user_id}/trend 差距趋势
GET    /api/v1/benchmark/top10/{track}  赛道头部画像
```

#### archive-service
```
GET    /api/v1/archive/{user_id}            成长档案
GET    /api/v1/archive/{user_id}/curve      成长曲线（六大指标）
GET    /api/v1/archive/{user_id}/level      当前等级（L1-L6）
GET    /api/v1/archive/{user_id}/whitebook  年度白皮书（MAX 年卡）
```

#### persona-service
```
POST   /api/v1/persona/scan             触发 IPP 扫描
GET    /api/v1/persona/{user_id}        当前人设档案
GET    /api/v1/persona/{user_id}/snapshots 演进快照
GET    /api/v1/persona/archetypes       12 原型库
POST   /api/v1/persona/{user_id}/canvas 生成人设画布
```

#### positioning-service
```
POST   /api/v1/positioning/scan         触发 BPS 扫描
GET    /api/v1/positioning/{user_id}    当前商业定位
GET    /api/v1/positioning/{user_id}/roadmap  12 月路线图
GET    /api/v1/positioning/industry-map 赛道商业地图
```

#### referrer-service
```
POST   /api/v1/referrer/apply           申请成为分享官
GET    /api/v1/referrer/me              我的分享官信息
GET    /api/v1/referrer/link            生成专属链接
GET    /api/v1/referrer/poster          生成专属海报
GET    /api/v1/referrer/me/level        当前等级
GET    /api/v1/referrer/me/rewards      奖励明细
POST   /api/v1/referrer/me/withdraw     提现申请
GET    /api/v1/referrer/leaderboard     月度排行榜
POST   /api/v1/referrer/track           归因记录
```

#### ai-orchestrator
```
POST   /api/v1/ai/task                  提交 AI 任务
GET    /api/v1/ai/task/{task_id}        查询任务状态
POST   /api/v1/ai/agent/{name}/invoke   直接调用某 Agent
GET    /api/v1/ai/agents                可用 Agent 列表
POST   /api/v1/ai/feedback              反馈（用于 Prompt 迭代）
```

#### crawler-service（仅内部 / 合规爬虫）
```
POST   /api/v1/crawler/account          抓取账号公开数据
POST   /api/v1/crawler/video            抓取视频公开数据
POST   /api/v1/crawler/comments         抓取评论池
GET    /api/v1/crawler/jobs/{job_id}    任务状态
```

### 15.4.3 开放端 API（对外暴露给加盟商/MCN）

```
# 鉴权（开放端独立 API Key 体系）
POST   /openapi/v1/auth                 获取 access_token
GET    /openapi/v1/me/credits           查询剩余配额

# 诊断
POST   /openapi/v1/diagnose             提交诊断（按次计费）
GET    /openapi/v1/diagnose/{id}        查询结果

# 对标
GET    /openapi/v1/benchmark/{track}    赛道头部画像
POST   /openapi/v1/benchmark/compare    自定义对比

# 客户管理（加盟商）
GET    /openapi/v1/customers            旗下客户列表
GET    /openapi/v1/customers/{id}/archive 客户档案
POST   /openapi/v1/customers/import     批量导入

# 财务
GET    /openapi/v1/billing/usage        用量账单
GET    /openapi/v1/billing/settlement   分账结算

# Webhook
POST   /openapi/v1/webhooks             订阅事件（diagnose.done / report.ready / customer.created）
```

### 15.4.4 内部事件总线（Kafka Topic 设计）

```
user.registered              用户注册
user.activated               用户激活
subscription.paid            订阅付费成功
subscription.renewed         续费成功
subscription.cancelled       退订
subscription.upgraded        升级
diagnosis.submitted          诊断提交
diagnosis.completed          诊断完成
report.generated             报告生成
alert.triggered              预警触发
referrer.activated           分享官激活
referrer.rewarded            分享官获得奖励
task.completed               任务完成（积分系统）
consultant.meeting.scheduled 顾问会议安排
consultant.meeting.completed 顾问会议完成
ai.feedback.received         AI 反馈（用于迭代）
```

---

## 15.4.5 协议规范（强制）

### REST API 规范
- 统一前缀：`/api/v{version}/{resource}`
- 版本化：MAJOR 版本分别部署，旧版本保留 ≥ 6 个月
- 鉴权：`Authorization: Bearer <JWT>`
- 限流：响应头 `X-RateLimit-*`
- 错误码：HTTP 状态码 + 业务子码 `{"code": "USER_NOT_FOUND", "message": "...", "trace_id": "..."}`
- 分页：`?page=1&size=20`，返回 `{"items":[], "total": N, "page": 1, "size": 20}`
- 幂等：写操作必须支持 `Idempotency-Key` header

### GraphQL（顾问端用）
- Schema 中央管理（Apollo Federation）
- 强类型 + DataLoader 防 N+1
- 持久化查询（Persisted Queries）减少带宽

### WebSocket（实时预警）
- 协议：`wss://ws.video-ct.com/v1`
- 心跳：30 秒 ping/pong
- 鉴权：连接时携带 JWT
- 频道：`user.{user_id}.alerts` / `user.{user_id}.archive_update`

---

## 15.5 数据架构详解

### 15.5.1 数据库分片策略

| 库 | 分片维度 | 副本 |
|---|---|---|
| PostgreSQL 主库 | user_id hash（Y2 起） | 1 主 + 2 从 |
| ClickHouse | 时间分区（按月） | 双副本 |
| MongoDB | sharded by user_id | 副本集 |
| Redis | Cluster 模式 | 6 主 6 从 |
| Milvus | collection 按赛道分 | 副本 |

### 15.5.2 关键数据流向（一图）

```
用户提交视频
    ↓
[file-service] 上传 OSS → 写 MongoDB 元数据
    ↓
[Kafka] diagnosis.submitted 事件
    ↓
[diagnosis-service] 创建任务 → Celery 队列
    ↓
[ai-orchestrator] 调度 Agents → 并行调用工具
    ↓
[report-service] 渲染 H5/PDF → OSS
    ↓
[archive-service] 写入档案
    ↓
[Kafka] diagnosis.completed 事件
    ↓
[notification-service] 推送用户
    ↓
[crm-service] 顾问端可见（如 MAX）
    ↓
[analytics] 写入 ClickHouse 看板
```

### 15.5.3 备份策略

| 库 | 全量 | 增量 | 异地 | 保留 |
|---|---|---|---|---|
| PostgreSQL | 每日 03:00 | 每小时 WAL | 异地双活 | 90 天 |
| ClickHouse | 每日 04:00 | — | 异地副本 | 180 天 |
| MongoDB | 每日 05:00 | 每小时 oplog | 异地副本 | 90 天 |
| Redis | RDB 每 6 小时 | AOF 实时 | 副本 | 30 天 |
| OSS | 跨区域复制 | 实时 | 异地 | 永久 |

---

## 15.6 安全与合规技术清单

### 15.6.1 加密
- 传输：TLS 1.3 全站
- 存储：AES-256（敏感字段）+ pgcrypto
- 密码：Argon2id
- 密钥：HashiCorp Vault 或阿里云 KMS

### 15.6.2 鉴权
- 用户：JWT (RS256)
- 服务间：mTLS 双向证书
- API Key（开放端）：HMAC-SHA256
- SSO：OAuth 2.0 / OIDC

### 15.6.3 审计
- 所有 DB 写操作：Postgres Audit Extension
- 所有 API 调用：access log + ELK
- 敏感操作（财务/权限变更）：单独 audit_log 表 + 邮件告警
- 数据访问留痕：90 天

### 15.6.4 合规认证
- **ICP 备案**（必须）
- **公安网络备案**（必须）
- **等保 2.0 二级**（用户 ≥ 1 万即办，约 5-8 万一次）
- **等保 2.0 三级**（用户 ≥ 10 万升级，约 15-25 万）
- **ISO 27001**（B 端合作要求，Y2）
- **PIPL 合规审计**（年度）

---

## 15.7 基础设施与云服务

### 15.7.1 主云：阿里云

| 服务 | 用途 | 月预算（M12 时）|
|---|---|---|
| ECS（计算） | 业务服务器（16 台 8c16g）| 3 万 |
| RDS PostgreSQL | 主数据库 | 5,000 |
| Redis 企业版 | 缓存 | 3,000 |
| MongoDB | 文档库 | 2,000 |
| OSS | 对象存储（1TB+） | 1,000 |
| CDN | 流量分发（5TB+） | 4,000 |
| 短信 SMS | 验证码 + 预警 | 2,000 |
| WAF | 防火墙 | 1,500 |
| DDoS 高防 | 防 DDoS | 4,000 |
| 域名 + SSL | 域名 + 证书 | 200 |
| **小计** | | **~6 万/月** |

### 15.7.2 备份云：腾讯云（容灾）
- 关键数据异地备份
- 短信兜底
- 微信生态原生支持

### 15.7.3 海外（Y2）：AWS / Cloudflare
- 海外区域部署
- Cloudflare CDN + WAF
- AWS Lambda（按量付费）

---

## 15.8 开发节奏与团队所需技能

### 15.8.1 团队角色与技能要求（M0-M12）

| 角色 | M0-M3 | M4-M6 | M7-M12 | 核心技能 |
|---|---|---|---|---|
| **全栈/后端** | 1 | 3 | 6 | Python + FastAPI + PostgreSQL + Redis + Docker |
| **AI 工程师** | 0 | 1 | 2 | LLM API + LangGraph + Prompt + RAG + 微调 |
| **前端 C 端** | 1（兼）| 2 | 3 | Taro + Vue3 + TS |
| **前端 B 端** | 0 | 1 | 2 | Vue3 + Ant Design Pro + TS |
| **数据/BI** | 0 | 1 | 2 | SQL + ClickHouse + Superset |
| **DevOps/SRE** | 0（外包）| 1 | 2 | K8s + Prometheus + 阿里云 |
| **测试** | 0 | 1 | 2 | Pytest + Playwright |
| **顾问 / 内容** | 1 | 2 | 5 | 短视频运营 + Prompt 调优 |
| **运营/客服** | 1 | 2 | 4 | 用户运营 + 数据分析 |

### 15.8.2 各阶段技术里程碑

**M0-M1（MVP）必须有：**
- ✅ FastAPI 后端骨架
- ✅ PostgreSQL + Redis
- ✅ 微信小程序 + H5
- ✅ 微信支付集成
- ✅ DeepSeek/Qwen API 接入
- ✅ OCR/ASR 流水线
- ✅ 基础日志 + Sentry

**M2-M3（PMF）补：**
- ✅ Kafka 事件总线
- ✅ Celery 异步任务
- ✅ 顾问端 Web 后台
- ✅ Milvus 向量库
- ✅ 8 大 Agent 基础版

**M4-M6（增长）补：**
- ✅ K8s 集群（替代 ECS 单机部署）
- ✅ ClickHouse + Superset 看板
- ✅ 神策埋点
- ✅ 分享官系统
- ✅ 第三方数据商接入
- ✅ 等保 2.0 二级

**M7-M12（规模化）补：**
- ✅ 开放 API + Stoplight 文档站
- ✅ 加盟商后台
- ✅ 自研模型微调上线
- ✅ 多地容灾
- ✅ ISO 27001（B 端要求）

---

## 15.9 成本总览（一年技术成本）

### 月度成本演进

| 月 | 服务器+云 | AI API | 第三方数据 | 短信/支付 | 工具订阅 | 合计 |
|---|---|---|---|---|---|---|
| M1 | 1,500 | 500 | 0 | 200 | 1,000 | **3,200** |
| M3 | 5,000 | 3,000 | 5,000 | 1,000 | 3,000 | **17,000** |
| M6 | 25,000 | 15,000 | 12,000 | 5,000 | 8,000 | **65,000** |
| M9 | 45,000 | 35,000 | 20,000 | 10,000 | 15,000 | **125,000** |
| M12 | 60,000 | 60,000 | 30,000 | 20,000 | 20,000 | **190,000** |

### Year 1 技术成本累计：**~ 90-110 万**

（不含人力，人力详见 [08 实施路线图](08_实施路线图.md)）

---

## 15.10 技术选型决策原则（应对未来变化）

1. **开源优先**：能开源就不商用，能自部署就不 SaaS
2. **国产可控**：核心链路用国产（阿里云/Qwen/DeepSeek），降低被卡风险
3. **多供应商**：AI 模型至少 3 家、数据商至少 2 家
4. **配置化**：业务规则 → 配置化（不要硬编码）
5. **平台无关**：UI 设计与业务逻辑分离，便于多端复用
6. **垂直可扩**：单服务先单实例，配额超阈值再分布式
7. **可降级**：每个外部依赖都有降级方案
8. **数据回流**：所有交互必须留 trace，回流入训练池

---

## 15.11 必踩的技术坑（提前避雷）

| 坑 | 表现 | 应对 |
|---|---|---|
| 一上来上 K8s | 增加复杂度、调试困难 | M0-M3 用 ECS + Docker Compose，M6+ 再上 K8s |
| 一上来微服务过细 | 团队小+服务过多 = 维护噩梦 | 起步 5-8 个服务，按需拆分 |
| 数据库不分库 | M12 时单库压力爆表 | M6 起规划分片维度 |
| 用 LangChain 全家桶 | 抽象层过厚，调试痛苦 | 仅用 LangGraph 编排，其余自研 |
| AI 输出直接给用户 | 幻觉/越界/不一致 | 必须 JSON Schema 校验 + Reflect 自检 |
| 把分享官写成传销 | 法律风险 | 严格 ≤ 2 级、无入门费 |
| 爬虫无节制 | 平台封禁 IP | 配额限制 + 第三方数据兜底 |
| 客服全人工 | M6 后人力爆炸 | AI 客服优先 + 人工兜底 |

---

## 修订日志
- v1.0 · 2026-05-20 · 初版（响应"技术栈与 API 详尽清单"需求新增）
