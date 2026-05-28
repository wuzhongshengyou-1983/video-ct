"""fire_eye 配置 — 模块优先级与开关"""
from pydantic import BaseModel
from typing import Dict


class FireEyeConfig(BaseModel):
    """各族启用开关和优先级配置（从环境变量或 app config 注入）"""

    # 族启用开关（False = 跳过该族，不报错）
    f1_enabled: bool = True    # 平台数据源
    f2_enabled: bool = False   # 技术元数据（v3 启用）
    f3_enabled: bool = True    # AI内容理解
    f4_enabled: bool = True    # 趋势竞品
    f5_enabled: bool = True    # CT诊断（不可关）
    f6_enabled: bool = False   # 播放QoE（v3 启用）

    # 成本控制
    cost_warn_yuan: float = 0.25
    cost_hard_limit_yuan: float = 0.30

    # 降级策略：degraded_families 超过此比例时终止诊断
    max_degraded_ratio: float = 0.6


# 默认配置实例（应用启动时可从 .env 覆盖）
default_config = FireEyeConfig()
