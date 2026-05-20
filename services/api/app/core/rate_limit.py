"""速率限制中间件 · 基于 Redis 令牌桶 + 用户 ID."""
from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

# 优雅处理 Redis 可选依赖
try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

# Redis key 前缀
RATE_LIMIT_PREFIX = "rate_limit:"


class TokenBucket:
    """令牌桶实现 · Redis 原子操作版本."""

    def __init__(
        self,
        redis_client: "aioredis.Redis | None" = None,
        rate: int | None = None,
        window_sec: int = 60,
    ):
        self._redis = redis_client
        self._rate = rate or settings.RATE_LIMIT_PER_MINUTE
        self._window_sec = window_sec
        # 内存回退（开发环境无 Redis 时使用）
        self._memory_buckets: dict[str, tuple[float, int]] = {}
        self._memory_cleanup_at: float = time.monotonic()

    async def consume(self, key: str, tokens: int = 1) -> bool:
        """尝试消费令牌 · 返回 True 表示允许."""
        if self._redis is not None:
            return await self._consume_redis(key, tokens)
        return self._consume_memory(key, tokens)

    async def _consume_redis(self, key: str, tokens: int) -> bool:
        """Redis 原子令牌桶 · Lua 脚本保证原子性."""
        now_ms = int(time.time() * 1000)
        window_ms = self._window_sec * 1000
        rk = f"{RATE_LIMIT_PREFIX}{key}"

        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local rate = tonumber(ARGV[3])
        local tokens = tonumber(ARGV[4])

        -- 清理过期记录
        redis.call("ZREMRANGEBYSCORE", key, 0, now - window)

        -- 当前窗口内已用令牌数
        local used = redis.call("ZCARD", key)
        if used + tokens > rate then
            return 0
        end

        -- 添加令牌消费记录
        for i = 1, tokens do
            redis.call("ZADD", key, now + i * 0.001, now .. ":" .. i)
        end
        redis.call("EXPIRE", key, math.ceil(window / 1000) + 1)
        return 1
        """

        try:
            result = await self._redis.eval(
                lua_script, 1, rk, now_ms, window_ms, self._rate, tokens
            )
            return bool(result)
        except Exception as exc:
            logger.warning(f"[RateLimit] Redis error, falling back to allow: {exc}")
            # Redis 异常时放行，避免误拦
            return True

    def _consume_memory(self, key: str, tokens: int) -> bool:
        """内存令牌桶 · 开发环境回退."""
        now = time.monotonic()

        # 定期清理过期桶（每 5 分钟）
        if now - self._memory_cleanup_at > 300:
            self._memory_cleanup_at = now
            expired = [
                k for k, (ts, _) in self._memory_buckets.items()
                if now - ts > self._window_sec
            ]
            for k in expired:
                del self._memory_buckets[k]

        bucket = self._memory_buckets.get(key)
        if bucket is None:
            self._memory_buckets[key] = (now, tokens)
            return True

        ts, used = bucket
        if now - ts > self._window_sec:
            # 窗口过期，重置
            self._memory_buckets[key] = (now, tokens)
            return True

        if used + tokens > self._rate:
            return False

        self._memory_buckets[key] = (ts, used + tokens)
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI 速率限制中间件 · 基于用户 ID 的每分钟限流."""

    def __init__(
        self,
        app,
        rate: int | None = None,
        exclude_paths: list[str] | None = None,
        redis_url: str | None = None,
    ):
        super().__init__(app)
        self._rate = rate or settings.RATE_LIMIT_PER_MINUTE
        self._exclude_paths = set(exclude_paths or ["/healthz", "/readyz", "/docs", "/openapi.json", "/redoc"])

        # 初始化 Redis（可选）
        redis_client = None
        if HAS_REDIS and redis_url:
            try:
                redis_client = aioredis.from_url(
                    redis_url, encoding="utf-8", decode_responses=True
                )
                logger.info("[RateLimit] using Redis backend")
            except Exception as exc:
                logger.warning(f"[RateLimit] Redis unavailable, using in-memory: {exc}")
        else:
            logger.info("[RateLimit] using in-memory backend")

        self._bucket = TokenBucket(redis_client=redis_client, rate=self._rate)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 排除某些路径
        path = request.url.path
        if path in self._exclude_paths:
            return await call_next(request)

        # 提取用户标识（优先 user_id header → X-Forwarded-For → client host）
        user_id = (
            request.headers.get("X-User-ID")
            or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.client.host if request.client else "unknown"
        )

        key = f"user:{user_id}:{self._window_key()}"
        allowed = await self._bucket.consume(key)

        if not allowed:
            logger.warning(f"[RateLimit] blocked user={user_id} path={path}")
            return JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMITED",
                    "message": f"请求过于频繁，每分钟限制 {self._rate} 次",
                    "retry_after_sec": self._retry_after(),
                },
                headers={"Retry-After": str(self._retry_after())},
            )

        return await call_next(request)

    @staticmethod
    def _window_key() -> str:
        """当前分钟窗口 key."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M")

    @staticmethod
    def _retry_after() -> int:
        """距离下一窗口的秒数."""
        return 60 - int(time.time()) % 60
