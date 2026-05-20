"""订阅 + 订单 + 产品目录."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProductCatalog(Base):
    """产品目录 · seed 初始化."""
    __tablename__ = "product_catalog"

    sku: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    tier: Mapped[str] = mapped_column(String(20))  # free / single / pro / max / addon
    billing_cycle: Mapped[str] = mapped_column(String(20))  # once / monthly / quarterly / yearly
    price_cny: Mapped[int] = mapped_column(Integer)  # 价格（元）
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    features: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON 字符串
    is_active: Mapped[bool] = mapped_column(default=True)


class Subscription(Base):
    """用户当前/历史订阅."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(50), ForeignKey("product_catalog.sku"))
    tier: Mapped[str] = mapped_column(String(20))  # pro / max
    status: Mapped[str] = mapped_column(String(20), default="active")  # active / canceled / expired
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    auto_renew: Mapped[bool] = mapped_column(default=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    """订单 · 单次/订阅/加购."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(50))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price_cny: Mapped[int] = mapped_column(Integer)
    total_cny: Mapped[int] = mapped_column(Integer)
    deduction_cny: Mapped[int] = mapped_column(Integer, default=0)  # 余额抵扣
    coupon_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    paid_cny: Mapped[int] = mapped_column(Integer)  # 实付
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    referred_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
