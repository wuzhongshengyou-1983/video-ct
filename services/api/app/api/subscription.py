"""订阅 + 订单路由 · 真实支付 + 完整生命周期管理."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.deps import CurrentUser, DbSession
from app.models.subscription import Order, ProductCatalog, Subscription
from app.schemas.subscription import (
    OrderCreate,
    OrderOut,
    OrderStatusOut,
    PayParamsOut,
    ProductOut,
    SubscriptionCancelOut,
    SubscriptionOut,
)
from app.services import payment_service, subscription_service

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
async def list_products(db: DbSession):
    res = await db.execute(select(ProductCatalog).where(ProductCatalog.is_active.is_(True)))
    products = res.scalars().all()
    return [
        ProductOut(
            sku=p.sku, name=p.name, tier=p.tier,
            billing_cycle=p.billing_cycle, price_cny=p.price_cny,
            description=p.description,
            features=json.loads(p.features) if p.features else None,
        )
        for p in products
    ]


@router.post("/orders", response_model=OrderOut)
async def create_order(payload: OrderCreate, db: DbSession, user: CurrentUser):
    """创建支付订单 · 返回订单信息 + 前端调起支付所需 pay_params.

    返回的 pay_params 可直接传给 wx.requestPayment():
      { appId, timeStamp, nonceStr, package, signType, paySign, mock }
    H5 环境会附带 h5_url 用于微信外跳转。
    """
    order = await subscription_service.create_order(
        db, user=user, sku=payload.sku,
        use_deduction=payload.use_deduction,
        referrer_code=payload.referrer_code,
    )
    pay_result = None
    pay_params = None

    if order.payment_status == "pending" and order.paid_cny > 0:
        try:
            pay_result = await payment_service.create_wechat_pay(order)
        except Exception as exc:
            logger.error("[SUB] 生成支付参数失败: {}", exc)
            pay_result = {"mock": True, "order_no": order.order_no, "error": str(exc)}

        if pay_result:
            pay_params = {
                "appId": pay_result.get("appId", ""),
                "timeStamp": pay_result.get("timeStamp", ""),
                "nonceStr": pay_result.get("nonceStr", ""),
                "package": pay_result.get("package", ""),
                "signType": pay_result.get("signType", "RSA"),
                "paySign": pay_result.get("paySign", ""),
                "mock": pay_result.get("mock", False),
                "order_no": order.order_no,
            }
            if "h5_url" in pay_result:
                pay_params["h5_url"] = pay_result["h5_url"]

    elif order.payment_status == "paid" or order.paid_cny <= 0:
        pay_params = {"mock": True, "order_no": order.order_no, "paid": True}

    await db.commit()
    await db.refresh(order)

    pay_url = None
    if pay_result:
        pay_url = pay_result.get("h5_url") or pay_result.get("pay_url")

    return OrderOut(
        id=order.id, order_no=order.order_no, sku=order.sku,
        total_cny=order.total_cny, deduction_cny=order.deduction_cny,
        paid_cny=order.paid_cny, payment_status=order.payment_status,
        pay_url=pay_url,
        pay_params=pay_params,
        created_at=order.created_at,
    )


@router.get("/my", response_model=SubscriptionOut | None)
async def my_subscription(db: DbSession, user: CurrentUser):
    sub = await subscription_service.get_active_subscription(db, user.id)
    if not sub:
        return None
    return SubscriptionOut.model_validate(sub)


@router.get("/orders", response_model=list[OrderOut])
async def my_orders(db: DbSession, user: CurrentUser):
    res = await db.execute(
        select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()).limit(50)
    )
    return [OrderOut.model_validate(o) for o in res.scalars().all()]


@router.get("/orders/{order_no}/pay-params")
async def get_pay_params(order_no: str, db: DbSession, user: CurrentUser):
    """获取微信支付前端调起参数（不含敏感 key）."""
    res = await db.execute(
        select(Order).where(Order.order_no == order_no, Order.user_id == user.id)
    )
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.payment_status == "paid":
        raise HTTPException(status_code=400, detail="订单已支付")

    pay = await payment_service.create_wechat_pay(order)

    # 规范化字段名：camelCase（支付服务内部）-> snake_case（前端约定）
    package = pay.get("package", "")
    prepay_id = package.replace("prepay_id=", "") if package.startswith("prepay_id=") else None

    return {
        "order_no": order_no,
        "app_id": pay.get("appId", ""),
        "time_stamp": pay.get("timeStamp", ""),
        "nonce_str": pay.get("nonceStr", ""),
        "package": package,
        "sign_type": pay.get("signType", "RSA"),
        "pay_sign": pay.get("paySign", ""),
        "pay_url": pay.get("h5_url") or pay.get("pay_url"),
        "prepay_id": prepay_id,
        "mock": pay.get("mock", False),
    }


@router.get("/orders/{order_no}/status", response_model=OrderStatusOut)
async def get_order_status(order_no: str, db: DbSession, user: CurrentUser):
    """查询订单支付状态 · 主动向微信查询并对齐本地状态."""
    res = await db.execute(
        select(Order).where(Order.order_no == order_no, Order.user_id == user.id)
    )
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 如果本地已是 paid，直接返回
    if order.payment_status == "paid":
        return OrderStatusOut(
            order_no=order.order_no,
            payment_status=order.payment_status,
            paid_at=order.paid_at,
        )

    # 向微信查询（pending 订单）
    try:
        wx_result = await payment_service.query_order(order_no)
        trade_state = wx_result.get("trade_state", "UNKNOWN")

        # 微信说已支付但本地未更新 → 补激活
        if trade_state == "SUCCESS":
            logger.info("[SUB] 微信已支付，补激活 order_no={}", order_no)
            await subscription_service.activate_subscription(db, order)
            await db.commit()
            await db.refresh(order)
    except Exception as exc:
        logger.warning("[SUB] 查询微信支付状态失败（返回本地状态）: {}", exc)

    return OrderStatusOut(
        order_no=order.order_no,
        payment_status=order.payment_status,
        paid_at=order.paid_at,
    )


# ── 模拟支付（仅开发 mock 模式） ─────────────────────

@router.post("/orders/{order_no}/mock-pay")
async def mock_pay(order_no: str, db: DbSession, user: CurrentUser):
    """开发模式：模拟支付成功（仅 WECHAT_PAY_MCH_ID 以 mock_ 开头时可用）."""
    if not settings.is_pay_mock:
        raise HTTPException(status_code=403, detail="mock-pay 仅在 mock 支付模式下可用")

    res = await db.execute(
        select(Order).where(Order.order_no == order_no, Order.user_id == user.id)
    )
    order = res.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.payment_status == "paid":
        return {"ok": True, "msg": "already paid", "order_no": order_no}

    await subscription_service.activate_subscription(db, order)
    await db.commit()
    logger.info("[SUB][MOCK] 模拟支付成功 order_no={}", order_no)
    return {"ok": True, "order_no": order_no}


# ── 取消订阅 ─────────────────────────────────────────

@router.post("/cancel", response_model=SubscriptionCancelOut)
async def cancel_subscription(db: DbSession, user: CurrentUser):
    """取消当前订阅 · 权益保留到到期日，不再自动续费."""
    sub = await subscription_service.get_active_subscription(db, user.id)
    if not sub:
        return SubscriptionCancelOut(ok=False, msg="没有有效订阅", expires_at=None)

    if sub.status == "canceled":
        return SubscriptionCancelOut(
            ok=True, msg="订阅已处于取消状态", expires_at=sub.expires_at,
        )

    sub.status = "canceled"
    sub.auto_renew = False
    sub.canceled_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info("[SUB] 订阅已取消 user_id={} sku={} expires_at={}", user.id, sub.sku, sub.expires_at)
    return SubscriptionCancelOut(
        ok=True, msg="已取消自动续费，权益保留到到期日", expires_at=sub.expires_at,
    )
