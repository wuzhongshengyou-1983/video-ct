"""Agent 基类 · Plan → Tool → Observe → Reflect → Output."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from app.services.llm_router import llm_router


class BaseAgent(ABC):
    """所有 AI Agent 的基类."""

    name: str = "BaseAgent"
    role: str = "通用 AI 代理"
    default_tier: str = "free"

    @abstractmethod
    async def run(self, **kwargs) -> dict:
        """执行任务. 子类实现."""
        raise NotImplementedError

    async def _llm_json(
        self,
        *,
        system: str,
        user: str,
        tier: str | None = None,
        task: str = "chat",
        temperature: float = 0.3,
    ) -> tuple[dict, dict]:
        """统一 LLM 调用 · 强制 JSON · 返回 (data, meta)."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        resp = await llm_router.chat(
            messages=messages,
            tier=tier or self.default_tier,
            task=task,
            response_format="json_object",
            temperature=temperature,
        )
        try:
            data = resp.as_json()
        except Exception as exc:
            logger.error(f"[{self.name}] JSON parse failed: {exc}")
            raise
        meta = {
            "agent": self.name,
            "model": resp.model,
            "tokens": resp.usage,
            "cost_cents": resp.cost_cents,
        }
        logger.info(f"[{self.name}] done · model={resp.model} cost={resp.cost_cents}¢")
        return data, meta
