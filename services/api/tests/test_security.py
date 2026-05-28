"""A1 · JWT(authlib) + JTI 吊销名单单元测试."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings
from app.core import security


class FakeRevokeRedis:
    """最小内存 Redis 替身（setex/exists/get/delete）."""

    def __init__(self):
        self.store: dict[str, str] = {}

    async def setex(self, key: str, ttl: int, val: str):
        self.store[key] = val

    async def exists(self, key: str) -> int:
        return 1 if key in self.store else 0

    async def get(self, key: str):
        return self.store.get(key)

    async def delete(self, key: str) -> int:
        return 1 if self.store.pop(key, None) is not None else 0


def test_token_roundtrip_has_jti_and_claims():
    t = security.create_access_token(123, extra={"role": "user"})
    assert isinstance(t, str)
    p = security.decode_token(t)
    assert p is not None
    assert p["sub"] == "123"
    assert p["role"] == "user"
    assert p["iss"] == settings.APP_NAME
    assert len(p.get("jti", "")) > 0


def test_tampered_and_garbage_token_rejected():
    t = security.create_access_token(1)
    assert security.decode_token(t[:-3] + "zzz") is None
    assert security.decode_token("not.a.jwt") is None
    assert security.decode_token("") is None


def test_alg_none_attack_rejected():
    import base64
    import json

    def b64(d: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    forged = b64({"alg": "none", "typ": "JWT"}) + "." + b64({"sub": "999", "role": "admin"}) + "."
    assert security.decode_token(forged) is None


def test_expired_token_rejected(monkeypatch):
    monkeypatch.setattr(settings, "JWT_EXPIRE_MINUTES", -1)
    expired = security.create_access_token(7)
    assert security.decode_token(expired) is None


@pytest.mark.asyncio
async def test_revoke_then_is_revoked(monkeypatch):
    fake = FakeRevokeRedis()
    monkeypatch.setattr(security, "_revoke_redis", fake)
    t = security.create_access_token(42)
    jti = security.decode_token(t)["jti"]

    assert await security.is_jti_revoked(jti) is False
    ok = await security.revoke_access_token(t)
    assert ok is True
    assert await security.is_jti_revoked(jti) is True


@pytest.mark.asyncio
async def test_is_revoked_false_without_redis(monkeypatch):
    monkeypatch.setattr(security, "_revoke_redis", None)
    monkeypatch.setattr(security, "_HAS_REDIS", False)
    assert await security.is_jti_revoked("anything") is False


@pytest.mark.asyncio
async def test_logout_endpoint_ok(client: AsyncClient):
    t = security.create_access_token(99)
    r = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


# ── refresh 轮换 ────────────────────────────────────────

def test_refresh_token_has_refresh_type():
    rt, jti = security.create_refresh_token(5)
    p = security.decode_token(rt)
    assert p["type"] == "refresh"
    assert p["jti"] == jti
    assert p["sub"] == "5"


@pytest.mark.asyncio
async def test_consume_refresh_single_use(monkeypatch):
    monkeypatch.setattr(security, "_revoke_redis", FakeRevokeRedis())
    rt, jti = security.create_refresh_token(8)
    await security.store_refresh(jti, 8)
    assert await security.consume_refresh(rt) == "8"
    # 二次消费 → 已删除 → None（单次使用）
    assert await security.consume_refresh(rt) is None


@pytest.mark.asyncio
async def test_consume_refresh_rejects_access_token(monkeypatch):
    monkeypatch.setattr(security, "_revoke_redis", FakeRevokeRedis())
    access = security.create_access_token(8)
    assert await security.consume_refresh(access) is None


@pytest.mark.asyncio
async def test_consume_refresh_none_without_redis(monkeypatch):
    monkeypatch.setattr(security, "_revoke_redis", None)
    monkeypatch.setattr(security, "_HAS_REDIS", False)
    rt, _ = security.create_refresh_token(8)
    assert await security.consume_refresh(rt) is None


@pytest.mark.asyncio
async def test_refresh_endpoint_rotates_and_old_dies(client: AsyncClient, db_session, monkeypatch):
    from app.models.user import User

    monkeypatch.setattr(security, "_revoke_redis", FakeRevokeRedis())
    user = User(id=90001, phone="13900000099", nickname="t")  # sqlite BigInteger 不自增，显式 id
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()

    rt, jti = security.create_refresh_token(user.id)
    await security.store_refresh(jti, user.id)

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user_id"] == user.id

    # 旧 refresh 已被轮换失效
    r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": rt})
    assert r2.status_code == 401
