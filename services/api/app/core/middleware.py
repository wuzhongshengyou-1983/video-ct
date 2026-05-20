"""全局中间件 · 统一异常处理 + 请求日志."""
from __future__ import annotations

import time
import traceback
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


class ExceptionMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件 · 捕获未处理的异常，返回标准 JSON.

    生产环境不暴露 traceback 详情.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # 记录完整异常日志（内部）
            logger.exception(
                f"[ExceptionMiddleware] 未处理异常: "
                f"path={request.url.path} method={request.method} "
                f"error={exc}"
            )

            # 敏感信息脱敏
            error_detail: str = "Internal Server Error"
            if not settings.is_production:
                error_detail = f"{type(exc).__name__}: {exc}"

            return JSONResponse(
                status_code=500,
                content={
                    "code": "INTERNAL_ERROR",
                    "message": error_detail,
                },
            )


class RequestLogMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 · 记录每个请求的耗时和状态码."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        t0 = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - t0) * 1000

        # 只记录 API 路径，跳过静态资源
        path = request.url.path
        if path.startswith("/api") or path.startswith("/ws"):
            logger.info(
                f"[Request] {request.method} {path} "
                f"→ {response.status_code} ({elapsed_ms:.0f}ms)"
            )

        return response
