# 视频 CT · 后端 API

## 快速启动

```bash
# 1. 准备 Python 3.11+
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 准备 env
cp ../../.env.example ../../.env.local
# 编辑 .env.local · 至少填入 DEEPSEEK_API_KEY

# 3. 初始化数据库 + 基础数据
python scripts/seed.py

# 4. 启动
uvicorn app.main:app --reload --port 8000

# 5. 打开 http://localhost:8000/docs 看 Swagger
```

## 默认账号
- 管理员：`13800138000` / `admin1234`
- 顾问：`13900139000` / `consult1234`
- 普通用户：用手机号 + 验证码登录，开发模式万能码 `0000`

## 目录
```
app/
├── main.py              FastAPI 入口
├── config.py            环境变量配置
├── database.py          SQLAlchemy 引擎
├── deps.py              FastAPI 依赖（CurrentUser 等）
├── core/                工具（security, exceptions）
├── models/              ORM 模型
├── schemas/             Pydantic schemas
├── api/                 路由
├── agents/              8 大 AI Agent
└── services/            业务逻辑
```

## API 路由
- `/healthz` `/readyz` `/metrics`
- `/api/v1/auth/*` 鉴权
- `/api/v1/users/*` 用户
- `/api/v1/subscriptions/*` 订阅 + 订单
- `/api/v1/diagnoses/*` 诊断 + 报告
- `/api/v1/benchmarks/*` 头部对标
- `/api/v1/archives/*` 成长档案
- `/api/v1/personas/*` 人设 IPP
- `/api/v1/positionings/*` 商业定位 BPS
- `/api/v1/referrers/*` 分享官
- `/api/v1/ai/*` AI 直接调用
- `/api/v1/admin/*` 管理后台
- `/api/v1/webhooks/*` 第三方回调
