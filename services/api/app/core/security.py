"""安全工具：JWT(authlib) + 密码哈希 + JTI 吊销名单.

A1 止血：弃用存在 CVE-2024-33663 的 python-jose，改用 authlib 并锁定算法（防 alg 混淆）；
每个 token 带唯一 jti，配合 Redis 吊销名单实现登出/主动失效（无状态 JWT 本不可吊销）。
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from loguru import logger
from passlib.context import CryptContext

from app.config import settings

# 锁定算法白名单 —— 只接受配置的算法，杜绝 alg=none / RS↔HS 混淆攻击
_jwt = JsonWebToken([settings.JWT_ALGORITHM])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis JTI 吊销名单（可选依赖，无 Redis 时降级为不可吊销）
try:
    import redis.asyncio as aioredis
    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

_REVOKE_PREFIX = "jwt:revoked:"
_revoke_redis: "aioredis.Redis | None" = None


def _get_revoke_redis() -> "aioredis.Redis | None":
    global _revoke_redis
    if _revoke_redis is None and _HAS_REDIS and settings.REDIS_URL:
        try:
            _revoke_redis = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True
            )
        except Exception as exc:
            logger.warning(f"[Security] 吊销名单 Redis 初始化失败: {exc}")
    return _revoke_redis


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": settings.APP_NAME,
        "jti": uuid4().hex,
    }
    if extra:
        payload.update(extra)
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    token = _jwt.encode(header, payload, settings.JWT_SECRET)
    return token.decode("utf-8") if isinstance(token, bytes) else token


def decode_token(token: str) -> dict | None:
    """解码并校验签名 + 过期；失败返回 None（不在此处查吊销，吊销在鉴权依赖异步查）."""
    try:
        claims = _jwt.decode(token, settings.JWT_SECRET)
        claims.validate()  # 校验 exp / nbf / iat
        return dict(claims)
    except JoseError:
        return None
    except Exception as exc:  # 容错：格式错误等
        logger.debug(f"[Security] token decode error: {exc}")
        return None


async def revoke_jti(jti: str, ttl_sec: int) -> None:
    """把 jti 写入吊销名单，TTL 设为 token 剩余寿命（到期后自动清理）."""
    r = _get_revoke_redis()
    if r is None or not jti:
        return
    try:
        await r.setex(f"{_REVOKE_PREFIX}{jti}", max(1, ttl_sec), "1")
    except Exception as exc:
        logger.warning(f"[Security] revoke_jti 写入失败: {exc}")


async def is_jti_revoked(jti: str | None) -> bool:
    """查 jti 是否被吊销。无 Redis 时返回 False（无法吊销，与全局降级策略一致）."""
    if not jti:
        return False
    r = _get_revoke_redis()
    if r is None:
        return False
    try:
        return bool(await r.exists(f"{_REVOKE_PREFIX}{jti}"))
    except Exception as exc:
        logger.warning(f"[Security] is_jti_revoked 查询失败，放行: {exc}")
        return False


async def revoke_access_token(token: str) -> bool:
    """吊销一个仍有效的 access token（用于登出）. 返回是否成功登记吊销."""
    payload = decode_token(token)
    if not payload:
        return False
    jti = payload.get("jti")
    if not jti:
        return False
    exp = payload.get("exp")
    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(1, int(exp) - now) if exp else settings.JWT_EXPIRE_MINUTES * 60
    await revoke_jti(jti, ttl)
    return True


create_token = create_access_token
