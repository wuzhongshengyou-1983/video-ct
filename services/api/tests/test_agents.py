"""Agent 端到端测试 · CT 诊断官 / 对标分析师 / 人设观察员 + 新增 Agent."""
from __future__ import annotations

import pytest

from app.agents.benchmark_analyst import BenchmarkAnalystAgent
from app.agents.biz_strategist import BizStrategistAgent
from app.agents.content_maker import ContentMakerAgent
from app.agents.cs_butler import CSButlerAgent, LIFECYCLE_RULES
from app.agents.ct_radiologist import CTRadiologistAgent
from app.agents.data_sentinel import (
    DataSentinelAgent,
    THRESHOLDS,
    _classify_delta,
    _overall_status,
)
from app.agents.consultant_copilot import ConsultantCopilotAgent
from app.agents.orchestrator import AgentOrchestrator, orchestrator
from app.agents.persona_scout import PersonaScoutAgent


# ==================== DataSentinel 纯数学逻辑（不依赖 LLM）====================


class TestDataSentinelMath:
    """测试数据预警员的数学计算逻辑（不涉及 LLM 调用）."""

    def test_classify_delta_critical(self):
        assert _classify_delta("曝光率", -40) == "critical"
        assert _classify_delta("点赞率", 50) == "critical"

    def test_classify_delta_warning(self):
        assert _classify_delta("曝光率", -25) == "warning"
        assert _classify_delta("评论率", 20) == "notice"  # 评论阈值不同

    def test_classify_delta_notice(self):
        assert _classify_delta("曝光率", -12) == "notice"

    def test_classify_delta_none(self):
        assert _classify_delta("曝光率", -5) is None
        assert _classify_delta("曝光率", 5) is None

    def test_classify_delta_unknown_metric_uses_defaults(self):
        # 未知指标使用默认阈值
        result = _classify_delta("未知指标", -25)
        assert result == "warning"

    def test_overall_status_red(self):
        alerts = [
            {"severity": "warning", "metric": "A"},
            {"severity": "critical", "metric": "B"},
        ]
        assert _overall_status(alerts) == "red"

    def test_overall_status_orange(self):
        alerts = [
            {"severity": "warning", "metric": "A"},
            {"severity": "notice", "metric": "B"},
        ]
        assert _overall_status(alerts) == "orange"

    def test_overall_status_yellow(self):
        alerts = [{"severity": "notice", "metric": "A"}]
        assert _overall_status(alerts) == "yellow"

    def test_overall_status_green(self):
        assert _overall_status([]) == "green"

    @pytest.mark.asyncio
    async def test_run_no_baseline_no_alerts(self):
        """无基线数据时不应产生告警."""
        agent = DataSentinelAgent()
        result = await agent.run(
            user_metrics={"曝光率": 12.0, "点赞率": 4.5},
        )
        assert result["overall_status"] == "green"
        assert result["alerts"] == []
        assert len(result["summary"]) > 0

    @pytest.mark.asyncio
    async def test_run_with_baseline_generates_alerts(self):
        """有基线数据且偏差大时产生告警."""
        agent = DataSentinelAgent()
        result = await agent.run(
            user_metrics={"曝光率": 8.0, "点赞率": 3.0},
            baseline={"曝光率": 15.0, "点赞率": 6.0},
        )
        # 曝光率 delta = (8-15)/15 = -46.7% → critical
        # 点赞率 delta = (3-6)/6 = -50% → critical
        assert result["overall_status"] == "red"
        assert len(result["alerts"]) >= 2
        severities = [a["severity"] for a in result["alerts"]]
        assert "critical" in severities

    @pytest.mark.asyncio
    async def test_run_small_delta_no_alert(self):
        """小偏差不触发告警."""
        agent = DataSentinelAgent()
        result = await agent.run(
            user_metrics={"曝光率": 14.0},
            baseline={"曝光率": 15.0},
        )
        # delta = (14-15)/15 = -6.7% → below notice threshold (10%)
        assert result["alerts"] == []
        assert result["overall_status"] == "green"

    @pytest.mark.asyncio
    async def test_run_alerts_sorted_by_severity(self):
        """告警按严重程度排序（critical > warning > notice）."""
        agent = DataSentinelAgent()
        result = await agent.run(
            user_metrics={
                "曝光率": 8.0,   # -46.7% → critical
                "点赞率": 4.0,   # -33.3% → critical
                "评论率": 1.2,   # 无基线
                "转发率": 0.9,   # -40% → critical
                "收藏率": 3.2,   # -20% → warning
                "变现率": 0.6,   # -40% → critical
            },
            baseline={
                "曝光率": 15.0,
                "点赞率": 6.0,
                "转发率": 1.5,
                "收藏率": 4.0,
                "变现率": 1.0,
            },
        )
        severities = [a["severity"] for a in result["alerts"]]
        # 验证排序：critical 应排在 warning 前面
        assert severities == sorted(severities, key=lambda s: {"critical": 0, "warning": 1, "notice": 2}.get(s, 99))

    @pytest.mark.asyncio
    async def test_fallback_summary(self):
        """兜底摘要生成."""
        agent = DataSentinelAgent()
        summary = agent._fallback_summary("red", [{"severity": "critical", "metric": "曝光率"}])
        assert "曝光率" in summary
        assert "重大异动" in summary or "需立即" in summary


# ==================== BenchmarkAnalyst 数学逻辑 ====================


class TestBenchmarkAnalyst:
    """测试对标分析师的计算逻辑（不涉及 LLM 调用）."""

    @pytest.mark.asyncio
    async def test_gap_calculation(self):
        agent = BenchmarkAnalystAgent()
        result = await agent.run(
            user_metrics={
                "曝光率": 12, "点赞率": 4, "评论率": 1,
                "转发率": 0.5, "收藏率": 2, "变现率": 0.3,
            },
            benchmark_avg={
                "曝光率": 20, "点赞率": 8, "评论率": 2,
                "转发率": 1, "收藏率": 4, "变现率": 0.6,
            },
        )
        assert "gap_by_metric" in result
        assert "overall_gap_pct" in result
        assert result["overall_gap_pct"] < 0  # 全面低于头部
        assert result["alert"] is None  # 无历史数据，不触发异动

    @pytest.mark.asyncio
    async def test_alert_on_widening_gap(self):
        agent = BenchmarkAnalystAgent()
        result = await agent.run(
            user_metrics={"曝光率": 10, "点赞率": 3, "评论率": 1, "转发率": 0.5, "收藏率": 2, "变现率": 0.3},
            benchmark_avg={"曝光率": 20, "点赞率": 8, "评论率": 2, "转发率": 1, "收藏率": 4, "变现率": 0.6},
            history=[{"overall_gap": -30}],  # 上月差距
        )
        assert result["alert"] is not None
        assert result["alert"]["severity"] in {"warning", "notice"}

    @pytest.mark.asyncio
    async def test_priority_fixes_sorted(self):
        agent = BenchmarkAnalystAgent()
        result = await agent.run(
            user_metrics={"曝光率": 10, "点赞率": 3, "评论率": 1, "转发率": 0.5, "收藏率": 2, "变现率": 0.3},
            benchmark_avg={"曝光率": 20, "点赞率": 8, "评论率": 2, "转发率": 1, "收藏率": 4, "变现率": 0.6},
        )
        priorities = result["priority_fixes"]
        assert len(priorities) == 3
        # 差距最大的排在最前面
        assert priorities[0]["gap_pct"] <= priorities[1]["gap_pct"]


# ==================== CSButler 规则层 ====================


class TestCSButler:
    """测试客户成功管家的规则逻辑."""

    def test_all_lifecycle_events_have_rules(self):
        """所有标准生命周期事件都应有规则覆盖."""
        events = [
            "registered", "first_scan", "first_paid", "renewal_due",
            "churn_risk", "upgrade_ready", "engagement_drop",
            "negative_feedback", "milestone_reached", "inactive_30d",
        ]
        for event in events:
            assert event in LIFECYCLE_RULES, f"Missing rule for {event}"

    def test_rules_have_required_fields(self):
        """每条规则必须包含必要字段."""
        required = ["recommended_action", "priority", "channel", "urgency", "reason"]
        for event, rule in LIFECYCLE_RULES.items():
            for field in required:
                assert field in rule, f"Rule for {event} missing field: {field}"
            assert rule["priority"] in {"P0", "P1", "P2"}, f"Invalid priority for {event}"

    @pytest.mark.asyncio
    async def test_run_churn_risk_returns_p0(self):
        agent = CSButlerAgent()
        result = await agent.run(
            client_id=1,
            lifecycle_event="churn_risk",
            client_context={"nickname": "测试用户", "track": "知识分享"},
        )
        assert result["priority"] == "P0"
        assert result["recommended_action"] == "consultant_call"
        assert len(result["message_template"]) > 0
        assert result["urgency"] == "now"

    @pytest.mark.asyncio
    async def test_run_unknown_event_fallback(self):
        agent = CSButlerAgent()
        result = await agent.run(
            client_id=1,
            lifecycle_event="some_future_event_xyz",
        )
        assert result["recommended_action"] == "no_action"
        assert result["priority"] == "P2"
        assert "未识别" in result["reason"]

    def test_fallback_template_coverage(self):
        """每个事件都有兜底模板."""
        agent = CSButlerAgent()
        for event in LIFECYCLE_RULES:
            template = agent._fallback_template(event, LIFECYCLE_RULES[event], {"nickname": "测试"})
            assert len(template) > 0, f"No fallback template for {event}"


# ==================== AgentOrchestrator 路由逻辑 ====================


class TestAgentOrchestrator:
    """测试 Agent 编排器的路由逻辑."""

    @pytest.mark.asyncio
    async def test_unknown_task_type_returns_error(self):
        result = await orchestrator.run(task_type="nonexistent_chain")
        assert result["status"] == "error"
        assert "Unknown task_type" in result["error"]

    @pytest.mark.asyncio
    async def test_registered_chain_names_exist(self):
        """预定义的 3 条链应该都存在."""
        chains = ["video_diagnosis", "monthly_review", "new_user_activation"]
        for name in chains:
            assert name in orchestrator._chains, f"Chain '{name}' not registered"

    @pytest.mark.asyncio
    async def test_chain_has_correct_steps(self):
        """每条链步骤数量检查."""
        chain = orchestrator._chains["video_diagnosis"]
        assert len(chain.steps) == 3
        agent_names = [s.agent_name for s in chain.steps]
        assert "CTRadiologist" in agent_names
        assert "BenchmarkAnalyst" in agent_names
        assert "PersonaScout" in agent_names

    @pytest.mark.asyncio
    async def test_monthly_review_chain_structure(self):
        chain = orchestrator._chains["monthly_review"]
        agent_names = [s.agent_name for s in chain.steps]
        assert "BenchmarkAnalyst" in agent_names
        assert "PersonaScout" in agent_names
        assert "BizStrategist" in agent_names
        assert "ConsultantCopilot" in agent_names

    @pytest.mark.asyncio
    async def test_new_user_activation_chain_structure(self):
        chain = orchestrator._chains["new_user_activation"]
        agent_names = [s.agent_name for s in chain.steps]
        assert "PersonaScout" in agent_names
        assert "ContentMaker" in agent_names
        assert "BizStrategist" in agent_names

    @pytest.mark.asyncio
    async def test_register_agent(self):
        orch = AgentOrchestrator()
        orch.register_agent("TestAgent", "mock_instance")
        assert "TestAgent" in orch._agent_registry


# ==================== CT 诊断官输出 schema ====================


class TestCTRadiologistOutput:
    """测试 CT 诊断官的输出 schema 校验."""

    def test_validate_and_fill_sets_defaults(self):
        agent = CTRadiologistAgent()
        result = agent._validate_and_fill({})
        assert result["overall_score"] == 60
        assert result["grade"] == "L2"
        assert len(result["dimensions"]) == 6
        for dim_name in ["表层观感", "内容内核", "视听剪辑", "人设话术", "数据流量", "变现预埋"]:
            assert dim_name in result["dimensions"]
            assert result["dimensions"][dim_name]["score"] == 60

    def test_validate_invalid_grade_fallback(self):
        agent = CTRadiologistAgent()
        result = agent._validate_and_fill({"grade": "L7"})
        assert result["grade"] == "L2"

    def test_validate_score_clamping(self):
        agent = CTRadiologistAgent()
        result = agent._validate_and_fill({"overall_score": 999, "dimensions": {"表层观感": {"score": -50}}})
        assert result["overall_score"] == 100
        assert result["dimensions"]["表层观感"]["score"] == 0

    def test_validate_valid_data_preserved(self):
        agent = CTRadiologistAgent()
        result = agent._validate_and_fill({
            "overall_score": 85,
            "grade": "L4",
            "summary": "优质创作者",
        })
        assert result["overall_score"] == 85
        assert result["grade"] == "L4"


# ==================== PersonaScout 输出 schema ====================


class TestPersonaScoutOutput:
    """测试人设观察员的输出 schema 校验."""

    def test_run_requires_llm(self):
        """人设观察员依赖 LLM，此处仅验证类实例化."""
        agent = PersonaScoutAgent()
        assert agent.name == "PersonaScout"
        assert agent.role is not None


# ==================== ConsultantCopilot 输出 schema ====================


class TestConsultantCopilotOutput:
    """测试顾问助理的 schema 校验."""

    def test_validate_and_fill_sets_defaults(self):
        agent = ConsultantCopilotAgent()
        result = agent._validate_and_fill({}, "monthly")
        assert "brief_title" in result
        assert "key_metrics" in result
        assert "recommended_agenda" in result
        assert result["client_mood_estimate"] == "neutral"

    def test_validate_invalid_mood(self):
        agent = ConsultantCopilotAgent()
        result = agent._validate_and_fill({"client_mood_estimate": "angry"}, "quarterly")
        assert result["client_mood_estimate"] == "neutral"

    def test_validate_valid_mood_preserved(self):
        agent = ConsultantCopilotAgent()
        result = agent._validate_and_fill({"client_mood_estimate": "at_risk"}, "monthly")
        assert result["client_mood_estimate"] == "at_risk"


# ==================== 阈值配置完整性 ====================


class TestThresholdConfig:
    """测试阈值配置的正确性."""

    def test_all_standard_metrics_have_thresholds(self):
        standard_metrics = ["曝光率", "点赞率", "评论率", "转发率", "收藏率", "变现率", "粉丝增长率", "完播率"]
        for metric in standard_metrics:
            assert metric in THRESHOLDS, f"Missing threshold for {metric}"

    def test_threshold_grading_is_strict(self):
        """notice < warning < critical 严格递增."""
        for metric, thresholds in THRESHOLDS.items():
            assert thresholds["notice"] < thresholds["warning"] < thresholds["critical"], (
                f"Threshold grading not strict for {metric}"
            )
