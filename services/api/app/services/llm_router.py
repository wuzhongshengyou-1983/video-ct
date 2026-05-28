"""LLM 路由：按档位选择模型 · 真实调用 DeepSeek + 硅基流动 API."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import LLMBudgetExceededError

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class LLMResponse:
    def __init__(self, content: str, model: str, usage: dict, cost_cents: int):
        self.content = content
        self.model = model
        self.usage = usage
        self.cost_cents = cost_cents

    def as_json(self) -> dict:
        """安全解析 JSON 输出（兼容 markdown ```json 块）."""
        text = self.content.strip()
        # 去掉 markdown 代码块包裹
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip().startswith("```") else "\n".join(lines[1:])
            if text.startswith("json"):
                text = text[4:].lstrip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.warning(f"LLM JSON parse failed: {exc} | raw[:200]={text[:200]}")
            # 兜底：尝试找第一个 {...}
            start, end = text.find("{"), text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise


# ============ 模型档位定价（元/百万 tokens）================
MODEL_PRICING = {
    # DeepSeek 官方
    "deepseek-chat": {"input": 1, "output": 2},
    "deepseek-reasoner": {"input": 4, "output": 16},
    # 硅基流动 Qwen
    "Qwen/Qwen2.5-72B-Instruct": {"input": 4.13, "output": 4.13},
    "Qwen/Qwen2-VL-72B-Instruct": {"input": 4.13, "output": 4.13},
    # Embedding（按千次调用）
    "BAAI/bge-large-zh-v1.5": {"input": 0.5, "output": 0},  # 估算
}


def _cost_cents(model: str, prompt_tokens: int, completion_tokens: int) -> int:
    pricing = MODEL_PRICING.get(model, {"input": 4, "output": 16})
    rmb_yuan = (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000
    return max(1, round(rmb_yuan * 100))


class BudgetGuard:
    """全系统单日 LLM 成本硬上限守卫（A3）· Redis 日累计计数 + 调用前熔断.

    机制：调用前 check() 若当日累计成本已达 LLM_DAILY_BUDGET_CENTS 则抛 LLMBudgetExceededError；
    调用后 record() 累加实际成本。最多超额一次调用的成本（按调用粒度封顶），可接受。
    """

    def __init__(self):
        self._redis: "aioredis.Redis | None" = None
        if HAS_REDIS and settings.REDIS_URL:
            try:
                self._redis = aioredis.from_url(
                    settings.REDIS_URL, encoding="utf-8", decode_responses=True
                )
            except Exception as exc:
                logger.warning(f"[LLMBudget] Redis 初始化失败，成本守卫降级: {exc}")

    @staticmethod
    def _today_key() -> str:
        return f"llm:cost:cents:{datetime.now(timezone.utc).strftime('%Y%m%d')}"

    async def check(self) -> None:
        cap = settings.LLM_DAILY_BUDGET_CENTS
        if cap <= 0:
            return  # 0 = 关闭守卫
        if self._redis is None:
            # 无 Redis 无法计量：依 fail_open 策略决定（默认放行）
            if not settings.LLM_BUDGET_FAIL_OPEN:
                raise LLMBudgetExceededError("成本守卫不可用且配置为拒绝模式")
            return
        try:
            raw = await self._redis.get(self._today_key())
            spent = int(raw) if raw else 0
        except Exception as exc:
            if settings.LLM_BUDGET_FAIL_OPEN:
                logger.warning(f"[LLMBudget] 读取累计成本失败，放行: {exc}")
                return
            raise LLMBudgetExceededError("成本守卫读取失败且配置为拒绝模式") from exc
        if spent >= cap:
            logger.error(f"[LLMBudget] 单日成本 {spent} 分 ≥ 上限 {cap} 分，熔断 LLM 调用")
            raise LLMBudgetExceededError()

    async def record(self, cost_cents: int) -> None:
        if settings.LLM_DAILY_BUDGET_CENTS <= 0 or self._redis is None or cost_cents <= 0:
            return
        try:
            key = self._today_key()
            new_total = await self._redis.incrby(key, cost_cents)
            if new_total == cost_cents:  # 当日首次写入，设 48h 过期防 key 堆积
                await self._redis.expire(key, 172800)
        except Exception as exc:
            logger.warning(f"[LLMBudget] 记账失败（不影响主流程）: {exc}")


class LLMRouter:
    """按任务复杂度 + 用户档位选择模型."""

    def __init__(self):
        self._budget = BudgetGuard()
        self.deepseek_client = httpx.AsyncClient(
            base_url=settings.DEEPSEEK_BASE_URL,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            timeout=120,
        )
        self.siliconflow_client = httpx.AsyncClient(
            base_url=settings.SILICONFLOW_BASE_URL,
            headers={"Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}"},
            timeout=120,
        )

    def pick_model(self, *, tier: str = "free", task: str = "chat") -> tuple[str, str]:
        """根据用户档位 + 任务类型选模型. 返回 (provider, model)."""
        # tier: free / pro / max / addon
        # task: chat / reasoning / vision / embedding
        if task == "embedding":
            return "siliconflow", settings.SILICONFLOW_MODEL_EMBEDDING
        if task == "vision":
            return "siliconflow", settings.SILICONFLOW_MODEL_VISION
        if task == "reasoning" and tier in {"max", "addon"}:
            return "deepseek", settings.DEEPSEEK_MODEL_PRO
        if tier in {"pro", "max", "addon"}:
            return "deepseek", settings.DEEPSEEK_MODEL_CHAT
        # free / fallback
        return "deepseek", settings.DEEPSEEK_MODEL_CHAT

    async def chat(
        self,
        *,
        messages: list[dict],
        tier: str = "free",
        task: str = "chat",
        response_format: str | None = None,  # "json_object"
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        # A3 成本硬上限：预检（不进重试，超额即熔断）
        await self._budget.check()
        resp = await self._chat_call(
            messages=messages,
            tier=tier,
            task=task,
            response_format=response_format,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        await self._budget.record(resp.cost_cents)
        return resp

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _chat_call(
        self,
        *,
        messages: list[dict],
        tier: str = "free",
        task: str = "chat",
        response_format: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        provider, model = self.pick_model(tier=tier, task=task)
        client = self.deepseek_client if provider == "deepseek" else self.siliconflow_client
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}

        logger.info(f"LLM call: provider={provider} model={model} tier={tier} task={task}")
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        cost = _cost_cents(model, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))
        return LLMResponse(content=content, model=model, usage=usage, cost_cents=cost)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """文本向量化."""
        payload = {
            "model": settings.SILICONFLOW_MODEL_EMBEDDING,
            "input": texts,
            "encoding_format": "float",
        }
        resp = await self.siliconflow_client.post("/embeddings", json=payload)
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]

    async def close(self):
        await self.deepseek_client.aclose()
        await self.siliconflow_client.aclose()


# 单例
llm_router = LLMRouter()
