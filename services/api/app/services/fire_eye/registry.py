"""DataSourceRegistry — 六族模块注册与调度中心"""
from typing import Callable, Dict, Optional
from .contracts import VideoCTContext


# 族处理器类型：接收 context，就地更新并返回
FamilyHandler = Callable[[VideoCTContext], None]


class DataSourceRegistry:
    """
    六族热插拔调度器。
    每个族注册一个 async handler，Pipeline 按优先级依次调用。
    族失败时自动降级（记录 degraded_families），不中断整体流程。
    """

    def __init__(self):
        self._handlers: Dict[str, FamilyHandler] = {}
        self._timeouts: Dict[str, float] = {
            "f1": 15.0,
            "f2": 10.0,
            "f3": 15.0,
            "f4": 10.0,
            "f5": 25.0,
            "f6": 5.0,
        }

    def register(self, family: str, handler: FamilyHandler, timeout: Optional[float] = None):
        """注册族处理器"""
        self._handlers[family] = handler
        if timeout:
            self._timeouts[family] = timeout

    def get(self, family: str) -> Optional[FamilyHandler]:
        return self._handlers.get(family)

    @property
    def registered_families(self) -> list:
        return list(self._handlers.keys())


# 全局单例（在 app 启动时完成注册）
registry = DataSourceRegistry()
