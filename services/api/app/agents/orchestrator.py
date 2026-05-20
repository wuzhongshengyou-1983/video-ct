"""Agent 编排器 · A2A 协同 · 纯路由逻辑，不依赖 LLM."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from loguru import logger

# 预定义的协同链
# 每条链 = 一连串 (agent_name, kwargs_factory) 步骤，前一步输出作为后一步的部分输入


@dataclass
class ChainStep:
    """协同链中的一个步骤."""
    agent_name: str
    kwargs_factory: Callable[..., dict] | None = None  # 从上游结果中提取 kwargs


@dataclass
class Chain:
    """一条完整的协同链."""
    name: str
    description: str
    steps: list[ChainStep] = field(default_factory=list)


class AgentOrchestrator:
    """Agent 编排器 · 根据 task_type 调度到对应链/Agent.

    设计原则：
    - 不依赖 LLM，纯路由逻辑
    - 每条链是一组串行 Agent 调用，上游输出可注入下游输入
    - 支持单 Agent 直调和多 Agent 链式调用
    """

    name = "AgentOrchestrator"

    def __init__(self) -> None:
        self._agent_registry: dict[str, Any] = {}
        self._chains: dict[str, Chain] = {}
        self._register_default_chains()

    def register_agent(self, name: str, agent: Any) -> None:
        """注册 Agent 实例."""
        self._agent_registry[name] = agent
        logger.info(f"[Orchestrator] registered agent: {name}")

    def register_chain(self, chain: Chain) -> None:
        """注册协同链."""
        self._chains[chain.name] = chain
        logger.info(f"[Orchestrator] registered chain: {chain.name} ({chain.description})")

    def _register_default_chains(self) -> None:
        """注册预定义的三条核心协同链."""

        # 链 1：视频诊断链（CT → 对标 → 人设漂移检测）
        self.register_chain(Chain(
            name="video_diagnosis",
            description="CT 诊断 → 对标分析 → 人设漂移检测",
            steps=[
                ChainStep(agent_name="CTRadiologist"),
                ChainStep(
                    agent_name="BenchmarkAnalyst",
                    kwargs_factory=lambda prev, ctx: {
                        "user_metrics": _extract_metrics(prev),
                        "benchmark_avg": ctx.get("benchmark_avg", {}),
                        "tier": ctx.get("tier", "free"),
                    },
                ),
                ChainStep(
                    agent_name="PersonaScout",
                    kwargs_factory=lambda prev, ctx: {
                        "videos_summary": ctx.get("videos_summary", ""),
                        "comments_summary": ctx.get("comments_summary", ""),
                        "user_description": ctx.get("user_description", ""),
                        "track": ctx.get("track", "通用"),
                        "tier": ctx.get("tier", "free"),
                    },
                ),
            ],
        ))

        # 链 2：月度复盘链（对标 + 人设 + 商业 + 简报）
        self.register_chain(Chain(
            name="monthly_review",
            description="对标分析 + 人设诊断 + 商业定位 + 顾问简报",
            steps=[
                ChainStep(
                    agent_name="BenchmarkAnalyst",
                    kwargs_factory=lambda prev, ctx: {
                        "user_metrics": ctx.get("user_metrics", {}),
                        "benchmark_avg": ctx.get("benchmark_avg", {}),
                        "history": ctx.get("gap_history"),
                        "tier": ctx.get("tier", "max"),
                    },
                ),
                ChainStep(
                    agent_name="PersonaScout",
                    kwargs_factory=lambda prev, ctx: {
                        "videos_summary": ctx.get("videos_summary", ""),
                        "comments_summary": ctx.get("comments_summary", ""),
                        "user_description": ctx.get("user_description", ""),
                        "track": ctx.get("track", "通用"),
                        "tier": ctx.get("tier", "max"),
                    },
                ),
                ChainStep(
                    agent_name="BizStrategist",
                    kwargs_factory=lambda prev, ctx: {
                        "track": ctx.get("track", "通用"),
                        "follower_count": ctx.get("follower_count", 0),
                        "current_monetization": ctx.get("current_monetization", ""),
                        "goals": ctx.get("goals", ""),
                        "tier": ctx.get("tier", "max"),
                    },
                ),
                ChainStep(
                    agent_name="ConsultantCopilot",
                    kwargs_factory=lambda prev, ctx: {
                        "client_id": ctx.get("client_id", 0),
                        "meeting_type": "monthly",
                        "user_metrics": ctx.get("user_metrics"),
                        "gap_history": ctx.get("gap_history"),
                        "persona_data": prev.get("PersonaScout"),
                        "tier": ctx.get("tier", "max"),
                    },
                ),
            ],
        ))

        # 链 3：新用户激活链（人设 → 内容 → 商业）
        self.register_chain(Chain(
            name="new_user_activation",
            description="新用户激活：人设观察 → 内容建议 → 商业方向",
            steps=[
                ChainStep(
                    agent_name="PersonaScout",
                    kwargs_factory=lambda prev, ctx: {
                        "videos_summary": ctx.get("videos_summary", ""),
                        "comments_summary": ctx.get("comments_summary", ""),
                        "user_description": ctx.get("user_description", ""),
                        "track": ctx.get("track", "通用"),
                        "tier": ctx.get("tier", "free"),
                    },
                ),
                ChainStep(
                    agent_name="ContentMaker",
                    kwargs_factory=lambda prev, ctx: {
                        "topic": prev.get("PersonaScout", {}).get("primary_archetype", ctx.get("track", "通用")),
                        "track": ctx.get("track", "通用"),
                        "persona_archetype": prev.get("PersonaScout", {}).get("primary_archetype"),
                        "tier": ctx.get("tier", "free"),
                    },
                ),
                ChainStep(
                    agent_name="BizStrategist",
                    kwargs_factory=lambda prev, ctx: {
                        "track": ctx.get("track", "通用"),
                        "follower_count": ctx.get("follower_count", 0),
                        "current_monetization": ctx.get("current_monetization", ""),
                        "goals": ctx.get("goals", ""),
                        "tier": ctx.get("tier", "free"),
                    },
                ),
            ],
        ))

    async def run(
        self,
        *,
        task_type: str,
        context: dict | None = None,
    ) -> dict[str, Any]:
        """调度执行.

        参数:
            task_type: 任务类型
              - 链名：video_diagnosis | monthly_review | new_user_activation
              - 单 Agent 名：CTRadiologist | PersonaScout | BizStrategist |
                             ContentMaker | BenchmarkAnalyst | DataSentinel |
                             ConsultantCopilot | CSButler
            context: 传递给链/Agent 的上下文参数

        返回:
            {"chain": 链名, "results": {agent_name: result, ...}, "status": "ok|error"}
        """
        ctx = context or {}

        # 检查是否是链名
        chain = self._chains.get(task_type)
        if chain is not None:
            return await self._run_chain(chain, ctx)

        # 检查是否是单 Agent 名
        agent = self._agent_registry.get(task_type)
        if agent is not None:
            result = await agent.run(**ctx)
            return {
                "chain": None,
                "results": {task_type: result},
                "status": "ok",
            }

        # 未找到
        available = list(self._chains.keys()) + list(self._agent_registry.keys())
        logger.error(f"[Orchestrator] unknown task_type: {task_type}, available: {available}")
        return {
            "chain": None,
            "results": {},
            "status": "error",
            "error": f"Unknown task_type '{task_type}'. Available: {available}",
        }

    async def _run_chain(self, chain: Chain, ctx: dict) -> dict[str, Any]:
        """串行执行一条协同链."""
        results: dict[str, Any] = {}
        prev: dict[str, Any] = {}

        for step in chain.steps:
            agent = self._agent_registry.get(step.agent_name)
            if agent is None:
                logger.error(f"[Orchestrator] agent not registered: {step.agent_name}")
                results[step.agent_name] = {"error": f"Agent '{step.agent_name}' not registered"}
                continue

            # 构建 kwargs：优先用 kwargs_factory，否则直接用 ctx
            if step.kwargs_factory:
                kwargs = step.kwargs_factory(results, ctx)
            else:
                kwargs = ctx

            try:
                result = await agent.run(**kwargs)
                results[step.agent_name] = result
                prev = result
                logger.info(f"[Orchestrator] chain={chain.name} step={step.agent_name} done")
            except Exception as exc:
                logger.exception(f"[Orchestrator] chain={chain.name} step={step.agent_name} failed: {exc}")
                results[step.agent_name] = {"error": str(exc)}
                return {
                    "chain": chain.name,
                    "results": results,
                    "status": "error",
                    "error": f"Step '{step.agent_name}' failed: {exc}",
                }

        return {
            "chain": chain.name,
            "results": results,
            "status": "ok",
        }


def _extract_metrics(prev_result: dict) -> dict:
    """从 CT 诊断结果中提取六大指标（用于对标分析）."""
    dims = prev_result.get("dimensions", {})
    metrics: dict[str, float] = {}
    # 维度名到指标名的映射（从 CT 诊断 6 维中估算）
    mapping = {
        "表层观感": "曝光率",
        "内容内核": "点赞率",
        "视听剪辑": "完播率",
        "人设话术": "评论率",
        "数据流量": "转发率",
        "变现预埋": "变现率",
    }
    for dim_name, metric_name in mapping.items():
        score = dims.get(dim_name, {}).get("score", 0)
        # 将 0-100 分数转换为百分比（近似）
        metrics[metric_name] = float(score) / 100.0 * 20.0  # 缩放至约 0-20% 范围
    return metrics


# 全局单例
orchestrator = AgentOrchestrator()
