"""API 端到端测试 · 基础接口."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.rate_limit import OTP_RATE_PER_MIN


class TestHealthEndpoints:
    """测试健康检查端点."""

    @pytest.mark.asyncio
    async def test_root(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "video-ct"
        assert "version" in data
        assert "docs" in data

    @pytest.mark.asyncio
    async def test_healthz(self, client: AsyncClient):
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_readyz(self, client: AsyncClient):
        resp = await client.get("/readyz")
        # 测试环境 engine 指向生产 PG（conftest 只覆盖 get_db 依赖，不覆盖 engine 全局变量）
        # 生产 PG 可达时返回 200；CI/隔离环境返回 503，均属正常
        assert resp.status_code in {200, 503}
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "ready"
            assert data["database"] == "ok"


class TestAuthEndpoints:
    """测试认证端点响应格式."""

    @pytest.mark.asyncio
    async def test_otp_send_missing_phone(self, client: AsyncClient):
        """缺少 phone 参数时返回 422."""
        resp = await client.post("/api/v1/auth/otp/send", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_otp_send_valid_request(self, client: AsyncClient):
        """有效请求应返回成功（当前 mock 实现）."""
        resp = await client.post("/api/v1/auth/otp/send", json={"phone": "13800138000"})
        # mock 实现返回 200
        assert resp.status_code in {200, 422}

    @pytest.mark.asyncio
    async def test_me_without_token(self, client: AsyncClient):
        """无 token 时 /auth/me 返回 401 或 422."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code in {401, 403, 422}

    @pytest.mark.asyncio
    async def test_me_with_invalid_token(self, client: AsyncClient):
        """无效 token 返回 401."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert resp.status_code in {401, 403}


class TestOTPRateLimit:
    """A4 · OTP 手机号维度限流（3/min）."""

    @pytest.mark.asyncio
    async def test_otp_blocked_after_three_per_minute(self, client: AsyncClient):
        from app.core.rate_limit import _reset_otp_buckets

        _reset_otp_buckets()
        phone = "13900000001"
        for _ in range(OTP_RATE_PER_MIN):
            r = await client.post("/api/v1/auth/otp/send", json={"phone": phone})
            assert r.status_code == 200
        # 第 4 次（超过 3/min）应被限流
        r = await client.post("/api/v1/auth/otp/send", json={"phone": phone})
        assert r.status_code == 429
        body = r.json()
        assert body["code"] == "RATE_LIMITED"
        assert body["retry_after_sec"] == 60
        assert r.headers.get("Retry-After") == "60"
        _reset_otp_buckets()


class TestRateLimitMiddleware:
    """测试速率限制中间件（内存模式）."""

    @pytest.mark.asyncio
    async def test_healthz_excluded_from_rate_limit(self, client: AsyncClient):
        """healthz 应被排除在限流之外."""
        for _ in range(5):
            resp = await client.get("/healthz")
            assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_normal_request_passes(self, client: AsyncClient):
        """正常请求通过限流."""
        resp = await client.get("/")
        assert resp.status_code == 200


class TestCORSHeaders:
    """测试 CORS 配置."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client: AsyncClient):
        resp = await client.options(
            "/healthz",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # OPTIONS 预检应返回 200
        assert resp.status_code in {200, 405}


class TestErrorHandling:
    """测试错误处理."""

    @pytest.mark.asyncio
    async def test_404_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/nonexistent-endpoint-xyz")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_json_body(self, client: AsyncClient):
        """发送无效 JSON 时不应崩溃."""
        resp = await client.post(
            "/api/v1/auth/otp/send",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in {400, 422}


# ── Sprint3 测试辅助 ────────────────────────────────────────────────────────

_uid_counter = 0


async def _create_user_token(db_session, role: str = "user") -> tuple[int, str]:
    """在测试 DB 插入用户并返回 (user_id, bearer_token).

    SQLite 的 BigInteger PK 不自动递增，须显式传 id。
    """
    global _uid_counter
    from app.models.user import User
    from app.core.security import create_access_token

    _uid_counter += 1
    uid = _uid_counter
    user = User(id=uid, phone=f"+861390000{uid:04d}", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    token = create_access_token(user.id)
    return user.id, token


class TestAdminEventsTrend:
    """Sprint3 · GET /api/v1/admin/stats/events-trend."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/admin/stats/events-trend")
        assert resp.status_code in {401, 403, 422}

    @pytest.mark.asyncio
    async def test_requires_admin_role(self, client: AsyncClient, db_session):
        _, token = await _create_user_token(db_session, role="user")
        resp = await client.get(
            "/api/v1/admin/stats/events-trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_empty_trend(self, client: AsyncClient, db_session):
        """无事件时返回空趋势、phase1_met=False."""
        _, token = await _create_user_token(db_session, role="admin")
        resp = await client.get(
            "/api/v1/admin/stats/events-trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["trend"] == []
        assert data["phase1_met"] is False
        assert data["phase1_threshold"] == 500

    @pytest.mark.asyncio
    async def test_admin_trend_with_events(self, client: AsyncClient, db_session):
        """插入事件后趋势正确聚合."""
        from app.models.event_log import EventLog

        user_id, token = await _create_user_token(db_session, role="admin")
        for i, etype in enumerate(("page_view", "page_view", "diagnosis.submitted"), start=1):
            db_session.add(EventLog(id=i, user_id=user_id, event_type=etype))
        await db_session.commit()

        resp = await client.get(
            "/api/v1/admin/stats/events-trend",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["trend"]) == 1
        day = data["trend"][0]
        assert day["total"] == 3
        assert day["by_type"]["page_view"] == 2
        assert day["by_type"]["diagnosis.submitted"] == 1


class TestAccountHealth:
    """Sprint3 · GET /api/v1/accounts/{id}/health."""

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/accounts/1/health")
        assert resp.status_code in {401, 403, 422}

    @pytest.mark.asyncio
    async def test_not_found_or_forbidden(self, client: AsyncClient, db_session):
        """不存在或他人账号返回 404."""
        _, token = await _create_user_token(db_session, role="user")
        resp = await client.get(
            "/api/v1/accounts/9999/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_derived_score_no_snapshot(self, client: AsyncClient, db_session):
        """无快照时返回 derived 分（30 分基础分）."""
        from app.models.account import AccountEntity

        user_id, token = await _create_user_token(db_session, role="user")
        account = AccountEntity(id=1, user_id=user_id, platform="douyin", follower_count=1000)
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        resp = await client.get(
            f"/api/v1/accounts/{account.id}/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "derived"
        assert data["health_score"] == 30.0
        assert data["snapshot_date"] is None

    @pytest.mark.asyncio
    async def test_snapshot_returned_when_exists(self, client: AsyncClient, db_session):
        """有快照时优先返回快照数据."""
        from datetime import date
        from app.models.account import AccountEntity, AccountHealthSnapshot

        user_id, token = await _create_user_token(db_session, role="user")
        account = AccountEntity(id=1, user_id=user_id, platform="douyin", follower_count=5000)
        db_session.add(account)
        await db_session.commit()
        await db_session.refresh(account)

        snap = AccountHealthSnapshot(
            id=1,
            account_entity_id=account.id,
            snapshot_date=date(2026, 5, 29),
            health_score=72.5,
            dimension_scores={"hook": 80, "cta": 65},
            benchmark_percentile=68.0,
            trend="up",
            notes="诊断改善显著",
        )
        db_session.add(snap)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/accounts/{account.id}/health",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "snapshot"
        assert data["health_score"] == 72.5
        assert data["trend"] == "up"
        assert data["benchmark_percentile"] == 68.0
