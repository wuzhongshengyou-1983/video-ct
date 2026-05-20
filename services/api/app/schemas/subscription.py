"""订阅 schemas."""
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class ProductOut(BaseModel):
    sku: str
    name: str
    tier: str
    billing_cycle: str
    price_cny: int
    description: str | None = None
    features: list[str] | None = None


class OrderCreate(BaseModel):
    sku: str
    coupon_code: str | None = None
    use_deduction: bool = False  # 是否用余额抵扣
    referrer_code: str | None = None


class OrderOut(BaseModel):
    id: int
    order_no: str
    sku: str
    total_cny: int
    deduction_cny: int
    paid_cny: int
    payment_status: str
    pay_url: str | None = None  # 微信支付二维码 / 支付链接
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionOut(BaseModel):
    id: int
    sku: str
    tier: str
    status: str
    started_at: datetime
    expires_at: datetime
    auto_renew: bool

    class Config:
        from_attributes = True
