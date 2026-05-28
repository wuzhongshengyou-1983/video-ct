"""A3 · LLM 成本硬上限守卫单元测试."""
from __future__ import annotations

import pytest

from app.config import settings
from app.core.exceptions import LLMBudgetExceededError
from app.services.llm_router import BudgetGuard


class FakeRedis:
    """最小内存 Redis 替身（仅支持守卫用到的 get/incrby/expire）."""

    def __init__(self, store: dict | None = None):
        self.store: dict[str, int] = store or {}

    async def get(self, key: str):
        val = self.store.get(key)
        return None if val is None else str(val)

    async def incrby(self, key: str, n: int) -> int:
        self.store[key] = int(self.store.get(key, 0)) + n
        return self.store[key]

    async def expire(self, key: str, ttl: int) -> bool:
        return True


@pytest.mark.asyncio
async def test_check_blocks_when_at_or_over_cap(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DAILY_BUDGET_CENTS", 100)
    g = BudgetGuard()
    g._redis = FakeRedis({g._today_key(): 100})
    with pytest.raises(LLMBudgetExceededError):
        await g.check()


@pytest.mark.asyncio
async def test_check_passes_under_cap_then_records(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DAILY_BUDGET_CENTS", 100)
    g = BudgetGuard()
    key = g._today_key()
    g._redis = FakeRedis({key: 50})
    await g.check()  # 50 < 100，不抛
    await g.record(30)
    assert g._redis.store[key] == 80


@pytest.mark.asyncio
async def test_cap_zero_disables_guard(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DAILY_BUDGET_CENTS", 0)
    g = BudgetGuard()
    g._redis = FakeRedis({g._today_key(): 999_999})
    await g.check()  # 上限=0 视为关闭，即使远超也不抛


@pytest.mark.asyncio
async def test_fail_open_allows_when_no_redis(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DAILY_BUDGET_CENTS", 100)
    monkeypatch.setattr(settings, "LLM_BUDGET_FAIL_OPEN", True)
    g = BudgetGuard()
    g._redis = None
    await g.check()  # 无 Redis + fail_open → 放行


@pytest.mark.asyncio
async def test_fail_closed_blocks_when_no_redis(monkeypatch):
    monkeypatch.setattr(settings, "LLM_DAILY_BUDGET_CENTS", 100)
    monkeypatch.setattr(settings, "LLM_BUDGET_FAIL_OPEN", False)
    g = BudgetGuard()
    g._redis = None
    with pytest.raises(LLMBudgetExceededError):
        await g.check()  # 无 Redis + fail_closed → 拒绝
