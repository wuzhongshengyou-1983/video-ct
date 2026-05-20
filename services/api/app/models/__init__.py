"""所有 ORM 模型集中导入 · Alembic 自动发现用."""
from app.models.user import User, UserProfile
from app.models.subscription import Subscription, Order, ProductCatalog
from app.models.diagnosis import Diagnosis, Report
from app.models.archive import Archive, ArchiveSnapshot
from app.models.benchmark import Benchmark, BenchmarkSnapshot
from app.models.persona import Persona
from app.models.positioning import Positioning
from app.models.referrer import ReferrerLink, ReferrerLevel, RewardAccount, RewardTransaction
from app.models.coupon import Coupon, CouponRedemption
from app.models.event_log import EventLog

__all__ = [
    "User", "UserProfile",
    "Subscription", "Order", "ProductCatalog",
    "Diagnosis", "Report",
    "Archive", "ArchiveSnapshot",
    "Benchmark", "BenchmarkSnapshot",
    "Persona", "Positioning",
    "ReferrerLink", "ReferrerLevel", "RewardAccount", "RewardTransaction",
    "Coupon", "CouponRedemption",
    "EventLog",
]
