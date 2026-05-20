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
    pay_channel: str | None = None  # "jsapi" | "h5" | None=auto


class OrderOut(BaseModel):
    id: int
    order_no: str
    sku: str
    total_cny: int
    deduction_cny: int
    paid_cny: int
    payment_status: str
    pay_url: str | None = None  # 微信支付二维码 / 支付链接
    pay_params: dict | None = None  # 前端调起支付参数（新接口多环境兼容）
    created_at: datetime

    class Config:
        from_attributes = True


class PayParamsOut(BaseModel):
    """微信支付前端调起参数（不包含敏感 key）"""
    order_no: str
    app_id: str = ""
    time_stamp: str = ""
    nonce_str: str = ""
    package: str = ""  # "prepay_id=wx..."
    sign_type: str = "RSA"
    pay_sign: str = ""
    pay_url: str | None = None  # H5 支付跳转链接（非 JSAPI 环境）
    prepay_id: str | None = None
    mock: bool = False


class OrderStatusOut(BaseModel):
    """订单支付状态查询"""
    order_no: str
    payment_status: str
    paid_at: datetime | None = None


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


class SubscriptionCancelOut(BaseModel):
    ok: bool
    msg: str
    expires_at: datetime | None = None  # 当前订阅到期时间（权益保留到到期日）
