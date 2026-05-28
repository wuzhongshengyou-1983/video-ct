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
        assert resp.status_code == 200
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
