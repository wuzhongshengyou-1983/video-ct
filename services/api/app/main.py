"""FastAPI 应用入口."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from loguru import logger

from app import __version__
from app.api import api_router
from app.api.ws import router as ws_router
from app.config import settings
from app.core.exceptions import BizException
from app.core.middleware import ExceptionMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动
    logger.info(f"启动 {settings.APP_NAME} v{__version__} env={settings.NODE_ENV}")
    Path("./storage").mkdir(exist_ok=True)
    Path(settings.STORAGE_LOCAL_PATH).mkdir(parents=True, exist_ok=True)

    # SQLite 自动建表（生产用 Alembic）
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            # 导入所有 models 触发 metadata 注册
            from app import models  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite tables ensured")

    yield

    # 关闭
    logger.info("应用关闭")
    from app.services.llm_router import llm_router
    await llm_router.close()


app = FastAPI(
    title="视频 CT API",
    description="视频 CT · 短视频博主 AI 诊断 + 对标 + 陪跑 SaaS",
    version=__version__,
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 速率限制中间件（基于 user_id 的每分钟限流）
app.add_middleware(
    RateLimitMiddleware,
    rate=settings.RATE_LIMIT_PER_MINUTE,
    exclude_paths=["/healthz", "/readyz", "/docs", "/openapi.json", "/redoc"],
    redis_url=settings.REDIS_URL if settings.REDIS_URL else None,
)

# 全局异常处理中间件（捕获未处理异常，返回标准 JSON）
app.add_middleware(ExceptionMiddleware)

app.include_router(api_router)
app.include_router(ws_router)


@app.exception_handler(BizException)
async def biz_handler(_request, exc: BizException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": __version__,
        "docs": "/docs",
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok"}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": str(exc)},
        )
