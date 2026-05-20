"""订阅 + 订单路由."""
from __future__ import annotations

import json
from fastapi import APIRouter
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models.subscription import Order, ProductCatalog, Subscription
from app.schemas.subscription import OrderCreate, OrderOut, ProductOut, SubscriptionOut
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
    order = await subscription_service.create_order(
        db, user=user, sku=payload.sku,
        use_deduction=payload.use_deduction,
        referrer_code=payload.referrer_code,
    )
    pay = None
    if order.payment_status == "pending":
        pay = await payment_service.create_wechat_pay(order)
    await db.commit()
    await db.refresh(order)
    return OrderOut(
        id=order.id, order_no=order.order_no, sku=order.sku,
        total_cny=order.total_cny, deduction_cny=order.deduction_cny,
        paid_cny=order.paid_cny, payment_status=order.payment_status,
        pay_url=pay["pay_url"] if pay else None,
        created_at=order.created_at,
    )


@router.post("/orders/{order_no}/mock-pay")
async def mock_pay(order_no: str, db: DbSession, user: CurrentUser):
    """开发模式：模拟支付成功（生产删除）."""
    res = await db.execute(select(Order).where(Order.order_no == order_no, Order.user_id == user.id))
    order = res.scalar_one_or_none()
    if not order:
        return {"ok": False, "msg": "order not found"}
    if order.payment_status == "paid":
        return {"ok": True, "msg": "already paid"}
    await subscription_service.activate_subscription(db, order)
    await db.commit()
    return {"ok": True, "order_no": order_no}


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
